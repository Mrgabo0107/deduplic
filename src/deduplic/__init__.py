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
from .exceptions import DeduplicError


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
    "DeduplicError"
]




# # Funcion                               |exp func| Comando |
# #---------------------------------------|--------|---------|
# # deduplic normalize input              |   X    |         |done
# # deduplic do reports                   |   X    |         |done
# # deduplic init                         |   X    |         |done
# # deduplic init from file               |   X    |    X    |fix command else done
# # deduplic connection                   |   X    |    X    |fix comm
# # deduplic cluster                      |   X    |    X    |fix com
# # deduplic cluster by componenet id     |   X    |    X    |fix comm
# # deduplic all                          |   X    |    X    |fix comm
# # deduplic_get_state                    |   X    |    X    |fix comm
# # deduplic_commit                       |   X    |    X    |fix comm
# # deduplic_restore                      |   X    |    X    |fix comm
# # deduplic_get_projects_info            |   X    |         |done
# # deduplic_delete project               |   X    |    X    |do cmmd
# # deduplic delete all                   |   X    |    X    |do cmmd
# # deduplic execute merge                |   X    |    X    |fix comm
# # deduplic list pending merges          |   X    |    X    |fix comm
# # deduplic has pending merges           |   X    |    X    |do cmd
# # deduplic forget single merge          |   X    |    X    |do cmd
# # deduplic forget merges                |   X    |    X    |fix comm
# # deduplic_set_workspace_dir            |   X    |    X    |do cm
# # deduplic_purge_workspace              |   X    |    X    |do cmmd
# # deduplic_launch_gui                   |        |    X    | fix adjusting to pass path as parameter