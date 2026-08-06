"""Deduplic: High-performance record deduplication and entity resolution library."""

# Core Operations
from .core import (
    refresh_cluster_merges,
    deduplic_normalize_input,
    deduplic_do_reports,
    deduplic_init,
    deduplic_init_from_file,
    deduplic_connection,
    deduplic_cluster,
    deduplic_cluster_by_comp_id,
    deduplic_all,
    deduplic_get_state,
    deduplic_commit,
    deduplic_restore,
    deduplic_get_projects_info,
    deduplic_delete_project,
    deduplic_delete_all,
    deduplic_execute_merge,
    deduplic_list_pending_merges,
    deduplic_has_pending_merges,
    deduplic_forget_single_merge,
    deduplic_forget_merges,
    deduplic_purge_workspace,
    deduplic_set_workspace_dir,
)

# Exceptions
from .exceptions import (
    DeduplicError,
    DeduplicWarning,
    DedupAdapterError,
    DeduplicConfigError,
    DeduplicClusterSafetyError,
    DeduplicFileNotFoundError,
    DeduplicIndexError,
    DeduplicCorruptDataWarning,
)


__all__ = [
    "deduplic_normalize_input",
    "deduplic_do_reports",
    "deduplic_init",
    "deduplic_init_from_file",
    "deduplic_connection",
    "deduplic_cluster",
    "deduplic_cluster_by_comp_id",
    "deduplic_all",
    "deduplic_get_state",
    "deduplic_commit",
    "deduplic_restore",
    "deduplic_get_projects_info",
    "deduplic_delete_project",
    "deduplic_delete_all",
    "deduplic_execute_merge",
    "deduplic_list_pending_merges",
    "deduplic_has_pending_merges",
    "deduplic_forget_single_merge",
    "deduplic_forget_merges",
    "deduplic_purge_workspace",
    "deduplic_set_workspace_dir",
    "DeduplicError",
    "DeduplicWarning",
    "DedupAdapterError",
    "DeduplicConfigError",
    "DeduplicClusterSafetyError",
    "DeduplicFileNotFoundError",
    "DeduplicIndexError",
    "DeduplicCorruptDataWarning",
]




# # Funcion                               |exp func| Comando |
# #---------------------------------------|--------|---------|
# # deduplic normalize input              |   X    |         |
# # deduplic do reports                   |   X    |         |
# # deduplic init                         |   X    |         |
# # deduplic_get_projects_info            |   X    |         |
# # deduplic init from file               |   X    |    O    |
# # deduplic connection                   |   X    |    O    |
# # deduplic cluster                      |   X    |    O    |
# # deduplic cluster by componenet id     |   X    |    O    |
# # deduplic all                          |   X    |    O    |
# # deduplic_get_state                    |   X    |    O    |
# # deduplic_commit                       |   X    |    O    |
# # deduplic_restore                      |   X    |    O    |
# # deduplic_delete project               |   X    |    O    |
# # deduplic delete all                   |   X    |    O    |
# # deduplic execute merge                |   X    |    O    |
# # deduplic list pending merges          |   X    |    O    |
# # deduplic has pending merges           |   X    |    O    |
# # deduplic forget single merge          |   X    |    O    |
# # deduplic forget merges                |   X    |    O    |
# # deduplic_set_workspace_dir            |   X    |    O    |
# # deduplic_purge_workspace              |   X    |    O    |
# # deduplic_get_workspace                |        |    O    |
# # deduplic_set_threshold                |        |    O    |
# # deduplic_get_threshold                |        |    O    |
# # deduplic_set_resolution_method        |        |    O    |
# # deduplic_get_resolution_method        |        |    O    |
# # deduplic_set_diff_colors              |        |    O    |
# # deduplic_launch_gui                   |        |    X    | fix adjusting to pass path as parameter