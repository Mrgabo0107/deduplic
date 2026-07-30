from.input_adapter import normalize_input
from .do_reports import do_reports
from deduplic import (
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
    deduplic_delete_all
)
from .merge_manager import (
    deduplic_execute_merge,
    deduplic_list_pending_merges,
    deduplic_has_pending_merges,
    deduplic_forget_single_merge,
    deduplic_forget_merges,
)