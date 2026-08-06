"""Services layer for Deduplic Streamlit GUI."""

from deduplic.streamlit_gui.services.project_service import (
    get_workspace_dir,
    delete_project_directory,
    deduplic_get_projects_info,
    create_new_project_from_upload,
    load_project_report,
    load_dedup_corpus,
)

from deduplic.streamlit_gui.services.dedup_service import (
    resolve_edge_action,
    resolve_cluster_action,
    resolve_all_action,
    commit_project_action,
    restore_project_action,
    get_pending_merges_service,
    execute_single_merge_service,
    forget_single_merge_service,
    forget_all_merges_service,
)