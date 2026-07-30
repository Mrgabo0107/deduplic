import json
import logging
import shutil
from pathlib import Path

from ..exceptions import DeduplicError
from .draft_io import load_draft, save_draft
from .methods.utils import (
    collect_neighbors_and_untouched_edges,
    deprecate_source_records,
    get_next_corpus_id,
    load_comparison_keys_from_project,
    load_threshold_from_project,
    recompute_edges_for_synthetic_node,
    update_cluster_structure,
)

logger = logging.getLogger(__name__)


def _resolve_active_node(corpus: dict, node_id: int | str) -> str | int:
    """
    Sigue la cadena de redirecciones (_status == 'deprecated', _merged_into) 
    hasta encontrar el ID activo definitivo dentro del corpus.
    """
    curr = str(node_id)
    visited = set()

    while curr in corpus and curr not in visited:
        visited.add(curr)
        rec = corpus[curr]
        if rec.get("_status") == "deprecated" and rec.get("_merged_into"):
            curr = str(rec["_merged_into"])
        else:
            break

    return int(curr) if curr.isdigit() else curr


def _get_merges_dir(project_path: Path | str) -> Path:
    merges_dir = Path(project_path) / "merges"
    merges_dir.mkdir(parents=True, exist_ok=True)
    return merges_dir


def _merge_filename(component_id: int | str, node_a_id: int, node_b_id: int) -> str:
    lo, hi = sorted((int(node_a_id), int(node_b_id)))
    return f"{component_id}_{lo}_{hi}.json"


def _build_merge_preview(corpus: dict, report: list, cluster_idx: int, edge_idx: int) -> dict:
    """
    Construye la estructura preview para un merge interactivo.
    Resuelve aliases activos e incluye el component_id.
    """
    if not (0 <= cluster_idx < len(report)):
        raise DeduplicError(f"Cluster index {cluster_idx} out of range.")

    cluster = report[cluster_idx]
    component_id = cluster.get("component_id", cluster.get("id", cluster_idx))
    edges = cluster.get("edges_trazability", [])

    if not (0 <= edge_idx < len(edges)):
        raise DeduplicError(f"Edge index {edge_idx} out of range for cluster {cluster_idx}.")

    target_edge = edges[edge_idx]
    pair = target_edge.get("pair", [])
    if len(pair) < 2:
        raise DeduplicError(f"Invalid edge pair at index {edge_idx}.")

    raw_a_id, raw_b_id = pair[0], pair[1]
    active_a_id = int(_resolve_active_node(corpus, raw_a_id))
    active_b_id = int(_resolve_active_node(corpus, raw_b_id))

    if active_a_id == active_b_id:
        return {}

    rec_a = corpus.get(str(active_a_id), {})
    rec_b = corpus.get(str(active_b_id), {})

    all_keys = set(rec_a.keys()) | set(rec_b.keys())
    clean_keys = sorted([k for k in all_keys if not k.startswith("_")])

    fields = {
        key: {"keep": False, "source": None, "edit": None}
        for key in clean_keys
    }

    return {
        "component_id": component_id,
        "cluster_idx": cluster_idx,
        "edge_idx": edge_idx,
        "node_a_id": active_a_id,
        "node_b_id": active_b_id,
        "rec_a": rec_a,
        "rec_b": rec_b,
        "fields": fields,
    }


def _apply_merge_decision(
    corpus: dict,
    report: list,
    merge_data: dict,
    project_path: Path | str | None = None,
) -> tuple[dict, list]:
    """Aplica la decisión humana validada sobre el corpus y el report."""
    cluster_idx = merge_data["cluster_idx"]
    node_a_id = merge_data["node_a_id"]
    node_b_id = merge_data["node_b_id"]
    fields = merge_data.get("fields", {})

    str_a, str_b = str(node_a_id), str(node_b_id)
    rec_a = corpus.get(str_a, {})
    rec_b = corpus.get(str_b, {})

    synthetic_record = {}
    for key, rule in fields.items():
        if not rule.get("keep"):
            continue

        edit_val = rule.get("edit")
        if edit_val is not None:
            synthetic_record[key] = edit_val
            continue

        source = rule.get("source")
        val = None

        if source == node_a_id or str(source) == str_a:
            val = rec_a.get(key) if rec_a.get(key) is not None else rec_b.get(key)
        elif source == node_b_id or str(source) == str_b:
            val = rec_b.get(key) if rec_b.get(key) is not None else rec_a.get(key)
        else:
            raise DeduplicError(f"Invalid source '{source}' for field '{key}'.")

        synthetic_record[key] = val

    synthetic_record["_status"] = "active"
    synthetic_record["_merged_from"] = [int(node_a_id), int(node_b_id)]

    str_c = get_next_corpus_id(corpus)
    int_c = int(str_c)
    corpus[str_c] = synthetic_record

    deprecate_source_records(corpus, str_a, str_b, str_c)

    cluster = report[cluster_idx]
    edges = cluster.get("edges_trazability", [])

    threshold = load_threshold_from_project(project_path)
    keys_for_similarity = load_comparison_keys_from_project(project_path)

    neighbor_ids, untouched_edges = collect_neighbors_and_untouched_edges(
        edges, node_a_id, node_b_id
    )
    new_edges_for_c = recompute_edges_for_synthetic_node(
        corpus, synthetic_record, int_c, neighbor_ids, keys_for_similarity, threshold
    )

    update_cluster_structure(cluster, untouched_edges + new_edges_for_c)

    return corpus, report


# ---------------------------------------------------------------------------
# GESTIÓN DE ARCHIVOS Y ESTADOS (.JSON EN MERGES/)
# ---------------------------------------------------------------------------


def _is_decision_complete(fields: dict) -> bool:
    has_keep = False
    for _, rule in fields.items():
        if rule.get("keep"):
            has_keep = True
            if rule.get("source") is None and rule.get("edit") is None:
                return False
    return has_keep


def _compute_status(merge_data: dict, corpus: dict) -> str:
    final_a = _resolve_active_node(corpus, merge_data["node_a_id"])
    final_b = _resolve_active_node(corpus, merge_data["node_b_id"])

    if final_a == final_b:
        return "obsolete"

    if str(final_a) != str(merge_data["node_a_id"]) or str(final_b) != str(merge_data["node_b_id"]):
        return "stale"

    if _is_decision_complete(merge_data.get("fields", {})):
        return "ready"

    return "draft"


def create_pending_merge(project_path: Path | str, cluster_idx: int, edge_idx: int) -> Path | None:
    project_path = Path(project_path)
    corpus, report = load_draft(project_path)

    preview = _build_merge_preview(corpus, report, cluster_idx, edge_idx)
    if not preview:
        return None

    filename = _merge_filename(
        preview["component_id"], preview["node_a_id"], preview["node_b_id"]
    )
    merges_dir = _get_merges_dir(project_path)
    file_path = merges_dir / filename

    if file_path.exists():
        logger.info(f"Merge draft already exists: {file_path.name}")
        return file_path

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(preview, f, indent=2, ensure_ascii=False)

    logger.info(f"Merge draft created: {file_path.name}")
    return file_path


def deduplic_execute_merge(
    project_path: Path | str,
    node_a_id: int,
    node_b_id: int,
    component_id: int | str = "cluster",
) -> str:
    """Applies a merge if its status is 'ready', or repairs/discards it if obsolete/stale."""
    project_path = Path(project_path)

    def _find_edge_idx_for_pair(report, cluster_idx, target_a, target_b):
        edges = report[cluster_idx].get("edges_trazability", [])
        target_pair = {int(target_a), int(target_b)}
        for idx, edge in enumerate(edges):
            pair = edge.get("pair", [])
            if len(pair) == 2 and {int(p) for p in pair} == target_pair:
                return idx
        return None

    corpus, report = load_draft(project_path)
    merges_dir = _get_merges_dir(project_path)

    filename = _merge_filename(component_id, node_a_id, node_b_id)
    file_path = merges_dir / filename

    if not file_path.exists():
        target_pair = {int(node_a_id), int(node_b_id)}
        for candidate in merges_dir.glob("*.json"):
            try:
                with open(candidate, "r", encoding="utf-8") as f:
                    cdata = json.load(f)
                if {int(cdata.get("node_a_id")), int(cdata.get("node_b_id"))} == target_pair:
                    file_path = candidate
                    break
            except (OSError, json.JSONDecodeError):
                pass

    if not file_path.exists():
        raise DeduplicError(f"No merge draft exists for nodes {node_a_id} and {node_b_id}.")

    with open(file_path, "r", encoding="utf-8") as f:
        merge_data = json.load(f)

    status = _compute_status(merge_data, corpus)

    if status == "obsolete":
        file_path.unlink(missing_ok=True)
        logger.info(f"Merge {file_path.name} is obsolete. Automatically discarded.")
        return "discarded"

    if status == "stale":
        final_a = _resolve_active_node(corpus, merge_data["node_a_id"])
        final_b = _resolve_active_node(corpus, merge_data["node_b_id"])
        new_edge_idx = _find_edge_idx_for_pair(report, merge_data["cluster_idx"], final_a, final_b)

        if new_edge_idx is None:
            file_path.unlink(missing_ok=True)
            logger.info(f"Merge {file_path.name} no longer has a valid edge. Discarded.")
            return "discarded"

        fresh = _build_merge_preview(corpus, report, merge_data["cluster_idx"], new_edge_idx)

        if not fresh:
            file_path.unlink(missing_ok=True)
            logger.info(f"Merge {file_path.name} resulted in a self-merge. Discarded.")
            return "discarded"

        new_file_path = merges_dir / _merge_filename(
            merge_data.get("component_id", component_id), fresh["node_a_id"], fresh["node_b_id"]
        )

        with open(new_file_path, "w", encoding="utf-8") as f:
            json.dump(fresh, f, indent=2, ensure_ascii=False)

        if file_path != new_file_path and file_path.exists():
            file_path.unlink(missing_ok=True)

        logger.info(f"Merge was stale. Preview regenerated as {new_file_path.name}.")
        return "needs_review"

    if status != "ready":
        logger.warning(f"Merge {file_path.name} is in '{status}' state and cannot be applied.")
        return "not_ready"

    corpus, report = _apply_merge_decision(
        corpus,
        report,
        merge_data,
        project_path=project_path,
    )

    save_draft(project_path, corpus, report)
    file_path.unlink(missing_ok=True)

    logger.info(f"Merge {file_path.name} applied successfully.")
    return "applied"


def refresh_cluster_merges(project_path: Path | str, component_id: int | str) -> None:
    """Scans and updates or removes stale/obsolete merge drafts for a specific cluster."""
    project_path = Path(project_path)
    merges_dir = project_path / "merges"

    if not merges_dir.exists():
        return

    cluster_files = list(merges_dir.glob(f"{component_id}_*.json"))

    for file_path in cluster_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                merge_data = json.load(f)
            
            node_a = merge_data.get("node_a_id")
            node_b = merge_data.get("node_b_id")
            comp = merge_data.get("component_id", component_id)

            if node_a is not None and node_b is not None:
                deduplic_execute_merge(project_path, node_a, node_b, comp)
        except Exception as e:
            logger.warning(f"Error refreshing {file_path.name}: {e}")


def deduplic_list_pending_merges(project_path: Path | str) -> list[dict]:
    project_path = Path(project_path)
    corpus, _ = load_draft(project_path)

    merges_dir = project_path / "merges"
    if not merges_dir.exists():
        return []

    results = []
    for file_path in sorted(merges_dir.glob("*.json")):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["_status"] = _compute_status(data, corpus)
            data["_file_name"] = file_path.name
            results.append(data)
        except (OSError, json.JSONDecodeError) as e:
            logger.warning(f"Error reading merge file {file_path.name}: {e}")

    return results


def deduplic_has_pending_merges(project_path: Path | str) -> bool:
    merges_dir = Path(project_path) / "merges"
    return merges_dir.exists() and any(merges_dir.glob("*.json"))


def deduplic_forget_single_merge(project_path: Path | str, filename: str) -> bool:
    file_path = Path(project_path) / "merges" / filename
    if file_path.exists():
        file_path.unlink()
        logger.info(f"Merge draft {filename} deleted.")
        return True
    return False


def deduplic_forget_merges(project_path: Path | str, confirm: bool = False) -> None:
    if not confirm:
        raise DeduplicError("forget_merges requires confirm=True.")

    merges_dir = Path(project_path) / "merges"
    if merges_dir.exists():
        shutil.rmtree(merges_dir)
        logger.info(f"Directory 'merges/' removed for project {Path(project_path).name}.")