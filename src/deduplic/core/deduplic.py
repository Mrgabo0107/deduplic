import json
import logging
import shutil
from pathlib import Path
from typing import Any

from ..config import settings
from ..exceptions import DeduplicError
from .draft_io import load_draft, save_draft
from .input_adapter import normalize_input
from .merge_manager import (
    create_pending_merge,
    deduplic_forget_merges,
    deduplic_has_pending_merges,
    refresh_cluster_merges,
)
from .methods import apply_method, clean_record
from .do_reports import do_reports

logger = logging.getLogger(__name__)


def _process_edge(
    corpus: dict,
    report: list,
    cluster_idx: int,
    edge_idx: int,
    method: str | None = None,
    project_path: Path | str | None = None,
) -> tuple[dict, list]:
    """
    Validates boundary indices and applies a resolution method to a specific edge directly in RAM.
    Does not perform file I/O operations (optimized for batch iterations).
    """
    method = method or settings.default_resolution_method

    if not (0 <= cluster_idx < len(report)):
        raise IndexError(
            f"Cluster index {cluster_idx} is out of bounds. "
            f"The report contains {len(report)} clusters (valid range: 0 to {len(report) - 1})."
        )

    cluster = report[cluster_idx]
    edges = cluster.get("edges_trazability", [])

    if not (0 <= edge_idx < len(edges)):
        raise IndexError(
            f"Edge index {edge_idx} is out of bounds for cluster {cluster_idx}. "
            f"The cluster contains {len(edges)} connections (valid range: 0 to {len(edges) - 1})."
        )

    target_edge = edges[edge_idx]

    target_info = {
        "project_path": project_path,
        "cluster_idx": cluster_idx,
        "edge_idx": edge_idx,
        "edge": target_edge,
    }

    return apply_method(method, corpus, report, target_info)


def _process_cluster(
    corpus: dict,
    report: list,
    cluster_idx: int,
    method: str | None = None,
    project_path: Path | str | None = None,
) -> tuple[dict, list]:
    """Processes all edges in a cluster until no connections remain."""
    method = method or settings.default_resolution_method

    if not (0 <= cluster_idx < len(report)):
        raise IndexError(
            f"Cluster index {cluster_idx} is out of bounds. "
            f"The report contains {len(report)} clusters."
        )

    cluster = report[cluster_idx]

    while cluster.get("edges_trazability"):
        corpus, report = _process_edge(corpus, report, cluster_idx, 0, method, project_path)
        cluster = report[cluster_idx]

    return corpus, report


def deduplic_connection(
    project_path: Path | str, 
    cluster_idx: int,
    edge_idx: int,
    method: str | None = None,
) -> None:
    """Applies a deduplication method to a single edge/connection within a cluster."""
    method = method or settings.default_resolution_method

    if method == "merge":
        create_pending_merge(project_path, cluster_idx, edge_idx)
        return

    corpus, report = load_draft(project_path)

    try:
        corpus, report = _process_edge(
            corpus, report, cluster_idx, edge_idx, method, project_path
        )
    except Exception as e:
        logger.error(
            f"Failed to process connection ({edge_idx}) in cluster ({cluster_idx}): {e}"
        )
        raise DeduplicError(
            f"Error processing connection ({edge_idx}) in cluster ({cluster_idx}): {e}"
        ) from e

    save_draft(project_path, corpus, report)

    component_id = report[cluster_idx].get("component_id", cluster_idx)
    refresh_cluster_merges(project_path, component_id)


def deduplic_cluster(
    project_path: Path | str,
    cluster_idx: int,
    method: str | None = None,
) -> None:
    """Applies a deduplication method to an entire cluster."""
    method = method or settings.default_resolution_method

    if method == "merge":
        _, report = load_draft(project_path)
        cluster = report[cluster_idx]
        edges = cluster.get("edges_trazability", [])
        for edge_idx in range(len(edges)):
            create_pending_merge(project_path, cluster_idx, edge_idx)
        return

    corpus, report = load_draft(project_path)
    try:
        corpus, report = _process_cluster(corpus, report, cluster_idx, method)
    except Exception as e:
        logger.error(f"Failed to process cluster ({cluster_idx}): {e}")
        raise DeduplicError(
            f"Error processing cluster ({cluster_idx}): {e}"
        ) from e

    save_draft(project_path, corpus, report)
    component_id = report[cluster_idx].get("component_id", cluster_idx)
    refresh_cluster_merges(project_path, component_id)


def deduplic_cluster_by_comp_id(
    project_path: Path | str,
    id_to_find: int,
    method: str | None = None,
) -> None:
    """Finds a cluster by its component ID and applies the specified deduplication method."""
    method = method or settings.default_resolution_method
    _, report = load_draft(project_path)

    for cluster_idx, cluster in enumerate(report):
        if cluster.get("component_id") == id_to_find:
            deduplic_cluster(project_path, cluster_idx, method)


def deduplic_all(
    project_path: Path |str,
    method: str | None = None,
) -> None:
    """Applies a deduplication method across all identified clusters in the project."""
    method = method or settings.default_resolution_method

    if method == "merge":
        _, report = load_draft(project_path)
        for cluster_idx in range(len(report)):
            edges = report[cluster_idx].get("edges_trazability", [])
            for edge_idx in range(len(edges)):
                create_pending_merge(project_path, cluster_idx, edge_idx)
        return

    corpus, report = load_draft(project_path)
    try:
        for cluster_idx in range(len(report)):
            corpus, report = _process_cluster(corpus, report, cluster_idx, method)
    except Exception as e:
        logger.error(f"Failed to complete deduplic_all process: {e}")
        raise DeduplicError(
            f"Error during deduplic_all execution: {e}"
        ) from e

    save_draft(project_path, corpus, report)


def deduplic_get_state(project_path: Path | str) -> Path:
    """
    Generates a consolidated 'dedup_corpus.json' file in the project root.
    Removes deprecated records, strips internal metadata, and reindexes the keys.
    """
    project_path = Path(project_path).resolve()
    corpus_draft, _ = load_draft(project_path)

    active_items = [
        (old_key, rec)
        for old_key, rec in corpus_draft.items()
        if rec.get("_status") != "deprecated"
    ]

    clean_corpus = {}
    for new_idx, (_, record) in enumerate(active_items):
        clean_corpus[str(new_idx)] = clean_record(record)

    output_file = project_path / "dedup_corpus.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(clean_corpus, f, indent=4, ensure_ascii=False)

    logger.info(f"Snapshot successfully generated: '{output_file.name}'")
    return output_file


def deduplic_commit(project_path: Path | str) -> None:
    """
    Commits the changes from .draft/ to the project root.
    The operation is blocked if there are pending merge drafts in merges/.
    """
    project_path = Path(project_path).resolve()
    if deduplic_has_pending_merges(project_path):
        msg = (
            "Commit cannot be performed: there are pending merge drafts in the 'merges/' directory. "
            "Resolve them by running 'deduplic_execute_merge' or discard them with 'deduplic_forget_merges'."
        )
        logger.error(msg)
        raise DeduplicError(msg)

    deduplic_get_state(project_path)

    root_report_file = project_path / "report.json"
    if root_report_file.exists():
        root_report_file.unlink()

    root_original_corp_file = project_path / "corpus.json"
    if root_original_corp_file.exists():
        root_original_corp_file.unlink()

    draft_dir = project_path / ".draft"
    if not draft_dir.exists():
        raise FileNotFoundError(f"No draft (.draft) found to commit in {project_path}.")

    shutil.rmtree(draft_dir)

    metadata_file = project_path / "metadata.json"
    if metadata_file.exists():
        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        metadata["status"] = "committed"

        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4, ensure_ascii=False)

    logger.info(f"Changes successfully committed to {project_path.name}.")


def deduplic_restore(project_path: Path | str) -> None:
    """
    Restores the project to its original state.
    Copies corpus.json and report.json from original/ back to project root and .draft/.
    """
    project_path = Path(project_path).resolve()
    original_dir = project_path / "original"
    draft_dir = project_path / ".draft"

    if not original_dir.exists():
        raise FileNotFoundError(
            f"Cannot restore: 'original/' directory not found in '{project_path}'."
        )

    draft_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(original_dir / "corpus.json", project_path / "corpus.json")
    shutil.copy2(original_dir / "report.json", project_path / "report.json")

    shutil.copy2(original_dir / "corpus.json", draft_dir / "corpus.json")
    shutil.copy2(original_dir / "report.json", draft_dir / "report.json")

    dedup_file = project_path / "dedup_corpus.json"
    if dedup_file.exists():
        dedup_file.unlink()

    deduplic_forget_merges(project_path, True)

    logger.info(
        f"Restore successful for '{project_path.name}'. Reverted to original state."
    )


def deduplic_get_projects_info(workspace_path: Path | str | None = None) -> dict[str, str]:
    """
    Scans the workspace directory and reads metadata status for each project folder.
    If workspace_path is not provided, defaults to settings.projects_dir.
    """
    target_workspace = Path(
        workspace_path if workspace_path is not None else settings.projects_dir
    ).resolve()
    projects = {}

    if not target_workspace.exists() or not target_workspace.is_dir():
        logger.warning(
            f"Workspace path does not exist or is not a directory: {target_workspace}"
        )
        return projects

    for p in target_workspace.iterdir():
        if p.is_dir():
            meta_file = p / "metadata.json"
            if meta_file.exists():
                try:
                    with open(meta_file, "r", encoding="utf-8") as f:
                        metadata = json.load(f)
                        projects[p.name] = metadata.get("status", "unknown")
                except (OSError, json.JSONDecodeError) as e:
                    logger.warning(
                        f"Could not read metadata for project '{p.name}': {e}"
                    )
                    projects[p.name] = "error"
            else:
                projects[p.name] = "no_metadata"

    return projects


def deduplic_delete_project(project_path: Path | str) -> bool:
    """
    Deletes an entire project directory from disk.
    Returns True if successfully deleted, False otherwise.
    """
    project_path = Path(project_path).resolve()

    if not project_path.exists() or not project_path.is_dir():
        logger.warning(
            f"Cannot delete project. Path does not exist or is not a directory: {project_path}"
        )
        return False

    try:
        shutil.rmtree(project_path)
        logger.info(f"Project directory successfully deleted: {project_path.name}")
        return True
    except OSError as e:
        logger.error(
            f"Failed to delete project directory '{project_path.name}': {e}"
        )
        return False


def deduplic_delete_all(workspace_path: Path | str | None = None) -> bool:
    """
    Deletes the entire workspace directory and recreates it empty.
    Returns True if successful, False otherwise.
    """
    target_workspace = Path(
        workspace_path if workspace_path is not None else settings.projects_dir
    ).resolve()

    if not target_workspace.exists():
        logger.warning(
            f"Cannot delete workspace. Path does not exist: {target_workspace}"
        )
        return False

    try:
        shutil.rmtree(target_workspace)
        
        target_workspace.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Workspace successfully cleared: '{target_workspace}'")
        return True
    except OSError as e:
        logger.error(f"Failed to clear workspace '{target_workspace}': {e}")
        return False


def _init_workspace(project_path: Path) -> None:
    """
    Internal helper: Sets original/ files as current active state and creates .draft/.
    """
    project_path = Path(project_path).resolve()
    path_original = project_path / "original"
    path_draft = project_path / ".draft"

    if not path_original.exists():
        raise FileNotFoundError(
            f"Cannot initialize workspace: '{path_original}' does not exist."
        )

    path_draft.mkdir(parents=True, exist_ok=True)

    for filename in ["corpus.json", "report.json"]:
        source_file = path_original / filename
        if source_file.exists():
            shutil.copy2(source_file, project_path / filename)
            shutil.copy2(source_file, path_draft / filename)
        else:
            logger.warning(f"File '{filename}' missing in '{path_original}'.")

    logger.info(f"Workspace successfully initialized for '{project_path.name}'.")


def deduplic_init(
    raw_input: Any,
    keys: list[str],
    name: str | None = None,
    threshold: float | None = None,
    projects_dir: Path | str | None = None,
) -> Path | None:
    """
    Normalizes in-memory raw input, creates the project directory,
    generates the report, populates original/ and initializes workspace (.draft/).
    """
    threshold = (
        threshold if threshold is not None else settings.default_threshold
    )
    projects_root = Path(
        projects_dir if projects_dir is not None else settings.projects_dir
    ).resolve()
    projects_root.mkdir(parents=True, exist_ok=True)

    normalized_records = normalize_input(raw_input)

    report_data = do_reports(
        data=normalized_records,
        keys_to_check=keys,
        threshold=threshold,
    )

    if not report_data:
        logger.info(
            f"No duplications found with threshold {threshold}. Project creation aborted."
        )
        return None

    if name is None:
        counter = 1
        while (projects_root / str(counter)).exists():
            counter += 1
        project_name = str(counter)
    else:
        if not (projects_root / name).exists():
            project_name = name
        else:
            counter = 2
            while (projects_root / f"{name}_{counter}").exists():
                counter += 1
            project_name = f"{name}_{counter}"

    project_path = projects_root / project_name
    path_original = project_path / "original"
    path_original.mkdir(parents=True, exist_ok=True)

    corpus_boite = {str(i): record for i, record in enumerate(normalized_records)}

    corpus_file = path_original / "corpus.json"
    with open(corpus_file, "w", encoding="utf-8") as f:
        json.dump(corpus_boite, f, indent=4, ensure_ascii=False)

    report_file = path_original / "report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=4, ensure_ascii=False)

    metadata = {
        "threshold": threshold,
        "keys_checked": keys,
        "total_records": len(normalized_records),
        "status": "in_progress",
    }
    metadata_file = project_path / "metadata.json"
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4, ensure_ascii=False)

    _init_workspace(project_path)

    logger.info(f"Project directory successfully initialized at: {project_path}")
    return project_path


def deduplic_init_from_file(
    file_path: Path | str,
    keys: list[str],
    name: str | None = None,
    threshold: float | None = None,
    projects_dir: Path | str | None = None,
) -> Path | None:
    """
    Loads JSON from file_path and initializes project using deduplic_init.
    """
    file_path = Path(file_path).resolve()
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        raw_json_data = json.load(f)

    derived_name = name if name is not None else file_path.stem

    return deduplic_init(
        raw_input=raw_json_data,
        keys=keys,
        name=derived_name,
        threshold=threshold,
        projects_dir=projects_dir,
    )