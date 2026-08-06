"""Core API for project creation, graph resolution strategies, state management, and commits."""

import json
import logging
import shutil
from pathlib import Path
from typing import Any
from platformdirs import user_data_dir

from ..config import settings, resolve_workspace_dir
from ..exceptions import DeduplicError, DeduplicFileNotFoundError, DeduplicIndexError
from .draft_io import load_draft, save_draft
from .input_adapter import deduplic_normalize_input
from .methods import (
    clean_record,
    create_pending_merge,
    deduplic_forget_merges,
    deduplic_has_pending_merges,
    refresh_cluster_merges,
    apply_method,
)
from .do_reports import deduplic_do_reports

logger = logging.getLogger(__name__)


def _process_edge(
    corpus: dict,
    report: list,
    cluster_idx: int,
    edge_idx: int,
    method: str | None = None,
    project_path: Path | str | None = None,
) -> tuple[dict, list]:
    """Validates boundary indices and applies a resolution method to a specific edge in RAM.

    Args:
        corpus: In-memory dictionary representing active and deprecated records.
        report: In-memory list containing cluster report structures.
        cluster_idx: Zero-based index of the cluster within the report.
        edge_idx: Zero-based index of the edge within the cluster's traceability list.
        method: Resolution strategy name (e.g., 'keep_newest', 'keep_oldest', 'merge').
        project_path: Optional path to the project root for strategy context.

    Returns:
        A tuple containing the updated (corpus, report) dictionaries in memory.

    Raises:
        DeduplicIndexError: If cluster_idx or edge_idx are out of valid bounds.
    """
    method = method or settings.default_resolution_method

    if not (0 <= cluster_idx < len(report)):
        raise DeduplicIndexError(
            f"Cluster index {cluster_idx} is out of bounds. "
            f"The report contains {len(report)} clusters (valid range: 0 to {len(report) - 1})."
        )

    cluster = report[cluster_idx]
    edges = cluster.get("edges_trazability", [])

    if not (0 <= edge_idx < len(edges)):
        raise DeduplicIndexError(
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
    """Iteratively processes all edges in a cluster until no connections remain.

    Args:
        corpus: In-memory dictionary representing active and deprecated records.
        report: In-memory list containing cluster report structures.
        cluster_idx: Zero-based index of the cluster to process.
        method: Resolution strategy name to apply to every edge in the cluster.
        project_path: Optional path to the project root.

    Returns:
        A tuple containing the updated (corpus, report) dictionaries in memory.

    Raises:
        DeduplicIndexError: If cluster_idx is out of valid bounds.
    """
    method = method or settings.default_resolution_method

    if not (0 <= cluster_idx < len(report)):
        raise DeduplicIndexError(
            f"Cluster index {cluster_idx} is out of bounds. "
            f"The report contains {len(report)} clusters."
        )

    cluster = report[cluster_idx]

    while cluster.get("edges_trazability"):
        corpus, report = _process_edge(corpus, report, cluster_idx, 0, method, project_path)
        cluster = report[cluster_idx]

    return corpus, report


def _init_workspace(project_path: Path) -> None:
    """Internal helper: Seeds root files and initializes `.draft/` workspace directory."""
    project_path = Path(project_path).resolve()
    path_original = project_path / "original"
    path_draft = project_path / ".draft"

    if not path_original.exists():
        raise DeduplicFileNotFoundError(
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
    """Initializes a new deduplication project from raw in-memory data.

    Normalizes data, computes duplicate clusters via blocking graph algorithms,
    persists records to `original/`, and prepares `.draft/`.

    Args:
        raw_input: List of dicts, pandas DataFrame, or raw data structure.
        keys: Fields/columns to check for duplicate similarities.
        name: Desired project folder name. Auto-increments if None or duplicate.
        threshold: Similarity match threshold (0.0 to 1.0). Defaults to settings.
        projects_dir: Root directory for projects. Defaults to settings.projects_dir.

    Returns:
        Path to the created project directory, or None if no duplicates are found.
    """
    threshold = (
        threshold if threshold is not None else settings.default_threshold
    )
    projects_root = Path(
        projects_dir if projects_dir is not None else settings.projects_dir
    ).resolve()
    projects_root.mkdir(parents=True, exist_ok=True)

    normalized_records = deduplic_normalize_input(raw_input)

    report_data = deduplic_do_reports(
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
    """Initializes a new deduplication project by reading data from a JSON file.

    Args:
        file_path: Path to input JSON file containing array of records.
        keys: List of dict keys to analyze for similarities.
        name: Name for the project folder. Defaults to input file stem if None.
        threshold: Match threshold value (0.0 to 1.0).
        projects_dir: Workspace directory. Defaults to settings.projects_dir.

    Returns:
        Path to the initialized project directory, or None if no duplicates are found.

    Raises:
        DeduplicFileNotFoundError: If file_path does not exist.
    """
    file_path = Path(file_path).resolve()
    if not file_path.exists():
        raise DeduplicFileNotFoundError(f"Input file not found: {file_path}")

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


def deduplic_connection(
    project_path: Path | str, 
    cluster_idx: int,
    edge_idx: int,
    method: str | None = None,
) -> None:
    """Applies a resolution method to a single edge within a cluster and updates `.draft/`.

    If method is 'merge', creates an interactive pending merge JSON in `merges/` instead
    of auto-resolving in RAM.

    Args:
        project_path: Path to the target project directory.
        cluster_idx: Index of the cluster containing the connection.
        edge_idx: Index of the edge to resolve within the cluster.
        method: Strategy name to use. If None, uses settings.default_resolution_method.

    Raises:
        DeduplicIndexError: If cluster_idx or edge_idx are out of bounds.
        DeduplicError: If the resolution method execution fails.
    """
    method = method or settings.default_resolution_method

    if method == "merge":
        create_pending_merge(project_path, cluster_idx, edge_idx)
        return

    corpus, report = load_draft(project_path)

    try:
        corpus, report = _process_edge(
            corpus, report, cluster_idx, edge_idx, method, project_path
        )
    except DeduplicError:
        raise
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
    """Applies a deduplication method across all connections in a specific cluster.

    Args:
        project_path: Path to the target project directory.
        cluster_idx: Zero-based index of the cluster to resolve.
        method: Resolution strategy name to apply.

    Raises:
        DeduplicIndexError: If cluster_idx is out of bounds.
        DeduplicError: If cluster processing encounters an unrecoverable error.
    """
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
    except DeduplicError:
        raise
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
    """Finds a cluster by its `component_id` attribute and applies the resolution method.

    Args:
        project_path: Path to the project directory.
        id_to_find: The component ID integer assigned during graph analysis.
        method: Resolution strategy name to apply.

    Raises:
        DeduplicError: If no cluster matching `component_id` exists in the report.
    """
    method = method or settings.default_resolution_method
    _, report = load_draft(project_path)

    found = False
    for cluster_idx, cluster in enumerate(report):
        if cluster.get("component_id") == id_to_find:
            deduplic_cluster(project_path, cluster_idx, method)
            found = True
            break
    if not found:
        raise DeduplicError(f"No cluster found with component_id={id_to_find}")


def deduplic_all(
    project_path: Path | str,
    method: str | None = None,
) -> None:
    """Applies a resolution method sequentially to all clusters in the project draft.

    Args:
        project_path: Path to the project directory.
        method: Strategy name to apply across the entire project.

    Raises:
        DeduplicError: If processing any cluster fails.
    """
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
    except DeduplicError:
        raise
    except Exception as e:
        logger.error(f"Failed to complete deduplic_all process: {e}")
        raise DeduplicError(
            f"Error during deduplic_all execution: {e}"
        ) from e

    save_draft(project_path, corpus, report)
    for cluster in report:
        comp_id = cluster.get("component_id")
        if comp_id is not None:
            refresh_cluster_merges(project_path, comp_id)


def deduplic_get_state(
    project_path: Path | str,
    output_path: Path | str | None = None,
) -> Path:
    """Generates a consolidated, active-only JSON corpus snapshot.

    Filters out deprecated records, strips internal metadata (e.g., `_status`),
    and re-indexes keys sequentially starting from 0.

    Args:
        project_path: Path to the project directory.
        output_path: Optional custom path for the generated file. If None, defaults to
            `project_path / "dedup_corpus.json"`.

    Returns:
        Path object pointing to the written output JSON file.

    Raises:
        DeduplicFileNotFoundError: If draft data cannot be loaded.
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

    out_file = Path(output_path).resolve() if output_path else project_path / "dedup_corpus.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(clean_corpus, f, indent=4, ensure_ascii=False)

    logger.info(f"Snapshot successfully generated: '{out_file.name}'")
    return out_file


def deduplic_commit(project_path: Path | str) -> None:
    """Finalizes project changes from `.draft/` into the project root.

    Blocks execution if pending human merge drafts remain unresolved. Upon completion,
    generates `dedup_corpus.json`, clears `.draft/`, removes obsolete root files,
    and updates `metadata.json` status to 'committed'.

    Args:
        project_path: Path to the target project directory.

    Raises:
        DeduplicError: If pending merges exist or metadata update fails.
        DeduplicFileNotFoundError: If `.draft/` directory does not exist.
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
        raise DeduplicFileNotFoundError(f"No draft (.draft) found to commit in {project_path}.")

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
    """Restores the project draft state to its original raw input files.

    Copies `corpus.json` and `report.json` from `original/` back to root and `.draft/`,
    deletes any generated `dedup_corpus.json`, and wipes pending merge drafts.

    Args:
        project_path: Path to the target project directory.

    Raises:
        DeduplicFileNotFoundError: If the `original/` directory is missing.
    """
    project_path = Path(project_path).resolve()
    original_dir = project_path / "original"
    draft_dir = project_path / ".draft"

    if not original_dir.exists():
        raise DeduplicFileNotFoundError(
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
    """Scans the workspace directory and retrieves project metadata statuses.

    Args:
        workspace_path: Directory containing project folders. If None, defaults to `settings.projects_dir`.

    Returns:
        A dictionary mapping project folder names to their status string
        (e.g., {'project_1': 'in_progress', 'project_2': 'committed'}).
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


def deduplic_delete_project(
        project_path: Path | str,
        confirm: bool = False,
        ) -> None:
    """Deletes an entire project directory from disk.

    Args:
        project_path: Path to the project folder to remove.

    Raises:
        DeduplicFileNotFoundError: If project_path does not exist or is not a directory.
        DeduplicError: If file deletion fails due to permission or I/O errors.
    """
    project_path = Path(project_path).resolve()
    if not confirm:
        raise DeduplicError("deduplic_delete_project requires confirm=True.")

    if not project_path.exists() or not project_path.is_dir():
        msg = f"Cannot delete project. Path does not exist or is not a directory: {project_path}"
        logger.warning(msg)
        raise DeduplicFileNotFoundError(msg)

    try:
        shutil.rmtree(project_path)
        logger.info(f"Project directory successfully deleted: {project_path.name}")
    except OSError as e:
        msg = f"Failed to delete project directory '{project_path.name}': {e}"
        logger.error(msg)
        raise DeduplicError(msg) from e


def deduplic_delete_all(
    confirm: bool = False, workspace_path: Path | str | None = None
) -> None:
    """Deletes all project directories within the workspace and recreates an empty root.

    Args:
        confirm: Confirmation flag. Must be set to True to execute deletion.
        workspace_path: Path to workspace. Defaults to `settings.projects_dir`.

    Raises:
        DeduplicError: If confirm is False or directory removal fails.
        DeduplicFileNotFoundError: If workspace_path does not exist.
    """
    if not confirm:
        raise DeduplicError("deduplic_delete_all requires confirm=True.")

    target_workspace = Path(
        workspace_path if workspace_path is not None else settings.projects_dir
    ).resolve()

    if not target_workspace.exists():
        msg = f"Cannot delete workspace. Path does not exist: {target_workspace}"
        logger.warning(msg)
        raise DeduplicFileNotFoundError(msg)

    try:
        shutil.rmtree(target_workspace)
        target_workspace.mkdir(parents=True, exist_ok=True)
        logger.info(f"Workspace successfully cleared: '{target_workspace}'")
    except OSError as e:
        msg = f"Failed to clear workspace '{target_workspace}': {e}"
        logger.error(msg)
        raise DeduplicError(msg) from e


def deduplic_set_workspace_dir(new_path: Path | str | None = None) -> Path:
    """Sets the global workspace directory where deduplication projects are stored.

    Args:
        new_path: Target path directory. If None or invalid, resets to OS default.

    Returns:
        Path: Absolute path of the active workspace directory.
    """
    resolved_path = resolve_workspace_dir(new_path)
    settings.projects_dir = resolved_path
    logger.info(f"Global projects directory updated to: {resolved_path}")
    return resolved_path


def deduplic_purge_workspace(confirm: bool = False) -> None:
    """Completely deletes the active deduplic workspace directory from disk.

    If using the default OS user data directory and it becomes empty after purging,
    the root 'deduplic' data folder is also removed.

    Args:
        confirm: Confirmation flag. Must be set to True to execute deletion.

    Raises:
        DeduplicError: If confirm is False or directory removal fails.
    """
    if not confirm:
        raise DeduplicError("purge_workspace requires confirm=True.")

    target_workspace = settings.projects_dir.resolve()

    if not target_workspace.exists():
        logger.warning(f"Workspace path does not exist: '{target_workspace}'")
        return

    if target_workspace == target_workspace.anchor or target_workspace == Path.home():
        raise DeduplicError(
            f"Safety block: Refusing to purge dangerous root/home path '{target_workspace}'."
        )

    try:
        shutil.rmtree(target_workspace)
        logger.info(f"Workspace directory successfully purged: {target_workspace}")

        official_user_dir = Path(user_data_dir("deduplic")).resolve()
        
        if official_user_dir in target_workspace.parents and official_user_dir.exists():
            if not any(official_user_dir.iterdir()):
                official_user_dir.rmdir()
                logger.info(f"Empty OS user data directory removed: {official_user_dir}")

        deduplic_set_workspace_dir(None)

    except OSError as e:
        msg = f"Failed to purge workspace at '{target_workspace}': {e}"
        logger.error(msg)
        raise DeduplicError(msg) from e