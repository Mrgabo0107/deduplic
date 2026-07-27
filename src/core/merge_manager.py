import json
import shutil
from pathlib import Path
from core.methods.utils import resolve_active_node
from core.methods.merge import build_merge_preview, apply_merge_decision
from core.draft_io import load_draft, save_draft


def _merge_filename(component_id: int | str, node_a_id: int, node_b_id: int) -> str:
    lo, hi = sorted((int(node_a_id), int(node_b_id)))
    return f"{component_id}_{lo}_{hi}.json"

def is_decision_complete(fields: dict) -> bool:
    """Checks whether the decision has at least one active field and all active fields are valid."""
    has_keep = False
    for _, rule in fields.items():
        if rule.get("keep"):
            has_keep = True
            # If keep is True, it must have either a non-None source or a non-None edit
            if rule.get("source") is None and rule.get("edit") is None:
                return False
    return has_keep


def compute_status(merge_data: dict, corpus: dict) -> str:
    """Dynamically computes the merge status against the current corpus state."""
    final_a = resolve_active_node(corpus, merge_data["node_a_id"])
    final_b = resolve_active_node(corpus, merge_data["node_b_id"])

    # Self-merge (both nodes have already been merged into the same final node)
    if final_a == final_b:
        return "obsolete"

    # One of the nodes changed identity due to another operation
    if str(final_a) != str(merge_data["node_a_id"]) or str(final_b) != str(merge_data["node_b_id"]):
        return "stale"

    # The user decision is complete and ready to be applied
    if is_decision_complete(merge_data.get("fields", {})):
        return "ready"

    return "draft"



def create_pending_merge(project_path: Path, cluster_idx: int, edge_idx: int) -> Path | None:
    """Creates a draft .json file inside the project's merges/ directory if it doesn't already exist."""
    corpus, report = load_draft(project_path)

    preview = build_merge_preview(corpus, report, cluster_idx, edge_idx)
    if not preview:
        return None

    cluster = report[cluster_idx]
    component_id = cluster.get("component_id", cluster.get("id", cluster_idx))

    filename = _merge_filename(component_id, preview["node_a_id"], preview["node_b_id"])
    merges_dir = project_path / "merges"
    merges_dir.mkdir(parents=True, exist_ok=True)

    file_path = merges_dir / filename

    # ✅ Si ya existe la misma conexión en borrador, no la duplicamos
    if file_path.exists():
        print(f"-> Merge draft already exists for edge {edge_idx}: {file_path.name}")
        return file_path

    preview["component_id"] = component_id

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(preview, f, indent=2, ensure_ascii=False)

    print(f"-> Merge draft created at: {file_path}")
    return file_path





def execute_merge(project_path: Path, node_a_id: int, node_b_id: int) -> str:
    def _find_edge_idx_for_pair(report, cluster_idx, node_a_id, node_b_id):
        edges = report[cluster_idx].get("edges_trazability", [])
        
        # Convertir a int explícitamente para evitar choques de tipos
        target_pair = {int(node_a_id), int(node_b_id)}
        
        for idx, edge in enumerate(edges):
            pair = edge.get("pair", [])
            if len(pair) == 2 and {int(p) for p in pair} == target_pair:
                return idx
                
        return None
    """Applies a merge if its status is 'ready'."""
    corpus, report = load_draft(project_path)
    file_path = project_path / "merges" / _merge_filename(node_a_id, node_b_id)
    if not file_path.exists():
        raise FileNotFoundError(
            f"No merge draft exists for nodes {node_a_id} and {node_b_id}."
        )

    with open(file_path, "r", encoding="utf-8") as f:
        merge_data = json.load(f)

    status = compute_status(merge_data, corpus)

    if status == "obsolete":
        file_path.unlink()
        print(f"-> Merge {file_path.name} is obsolete. Automatically discarded.")
        return "discarded"

    if status == "stale":
        final_a = resolve_active_node(corpus, merge_data["node_a_id"])
        final_b = resolve_active_node(corpus, merge_data["node_b_id"])
        new_edge_idx = _find_edge_idx_for_pair(report, merge_data["cluster_idx"], final_a, final_b)
        if new_edge_idx is None:
            # el motor de similitud ya no conecta a estos nodos finales: nada que revisar
            file_path.unlink()
            print(f"-> Merge {file_path.name} ya no tiene arista válida. Descartado.")
            return "discarded"
    
        # 1. Regenerate the preview using the updated active nodes
        fresh = build_merge_preview(corpus, report, merge_data["cluster_idx"], new_edge_idx)

        # If resolution results in a self-merge, discard the draft
        if not fresh:
            file_path.unlink()
            print(f"-> Merge {file_path.name} resulted in a self-merge. Automatically discarded.")
            return "discarded"

        # 2. Compute the new filename using the updated active node IDs
        # (e.g., merge_0_1.json -> merge_1_15.json)
        new_file_path = project_path / "merges" / _merge_filename(
            fresh["node_a_id"], fresh["node_b_id"], 
        )

        # 3. Save the regenerated draft (its fields are reset, so its status becomes "draft")
        with open(new_file_path, "w", encoding="utf-8") as f:
            json.dump(fresh, f, indent=2, ensure_ascii=False)

        # 4. Remove the old file if the IDs (and therefore the filename) changed
        if file_path != new_file_path and file_path.exists():
            file_path.unlink()

        print(
            f"-> Merge is stale. "
            f"Preview regenerated as {new_file_path.name} for active nodes "
            f"{node_a_id} and {node_b_id}."
        )
        return "needs_review"

    if status != "ready":
        print(f"-> Merge {file_path.name} is in '{status}' state and cannot be applied.")
        return "not_ready"

    # Apply the merge decision
    corpus, report = apply_merge_decision(
        corpus,
        report,
        merge_data,
        project_path=project_path
    )

    save_draft(project_path, corpus, report)
    file_path.unlink()

    print(f"-> Merge {file_path.name} applied successfully.")
    return "applied"


def forget_merges(project_path: Path, confirm: bool = False):
    """Deletes the project's entire merges/ directory."""
    if not confirm:
        raise ValueError("forget_merges requires confirm=True.")

    merges_dir = project_path / "merges"
    if merges_dir.exists():
        shutil.rmtree(merges_dir)
        print(f"-> 'merges/' directory removed for {project_path.name}.")


# def has_pending_merges(project_path: Path) -> bool:
#     """Returns whether any merge draft files exist in the merges/ directory."""
#     merges_dir = project_path / "merges"
#     return merges_dir.exists() and any(merges_dir.glob("merge_*.json"))

def list_pending_merges(project_path: Path) -> list[dict]:
    """Lists all merge drafts in the merges/ directory with their recomputed status."""
    corpus, _ = load_draft(project_path)

    merges_dir = project_path / "merges"
    if not merges_dir.exists():
        return []

    results = []
    # Busca cualquier archivo .json (ej: 199_50_51.json)
    for file_path in sorted(merges_dir.glob("*.json")):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["_status"] = compute_status(data, corpus)
            data["_file_name"] = file_path.name
            results.append(data)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    return results


def has_pending_merges(project_path: Path) -> bool:
    """Returns whether any merge draft files exist in the merges/ directory."""
    merges_dir = project_path / "merges"
    return merges_dir.exists() and any(merges_dir.glob("*.json"))

def forget_single_merge(project_path: Path, filename: str) -> bool:
    """Deletes a specific merge draft file from the merges/ directory."""
    file_path = project_path / "merges" / filename
    if file_path.exists():
        file_path.unlink()
        print(f"-> Merge draft {filename} deleted.")
        return True
    return False

def refresh_cluster_merges(project_path: Path, component_id: int | str):
    """
    Scans and updates or removes stale/obsolete merge drafts for a specific cluster.
    """
    corpus, report = load_draft(project_path)
    merges_dir = project_path / "merges"
    
    if not merges_dir.exists():
        return

    # Busca solo los archivos que inicien con el component_id del cluster (ej: 199_*.json)
    cluster_files = list(merges_dir.glob(f"{component_id}_*.json"))
    
    for file_path in cluster_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                merge_data = json.load(f)
            
            status = compute_status(merge_data, corpus)
            
            # Si se volvió auto-merge u obsoleto, lo eliminamos automáticamente
            if status in ("obsolete", "discarded"):
                file_path.unlink()
                print(f"-> Auto-cleared obsolete merge draft: {file_path.name}")
        except Exception as e:
            print(f"Error refreshing {file_path}: {e}")