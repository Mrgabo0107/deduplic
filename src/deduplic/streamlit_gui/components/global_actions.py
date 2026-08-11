"""Global project actions toolbar for Deduplic Streamlit GUI.

Location: src/deduplic/streamlit_gui/components/global_actions.py
"""

import streamlit as st
from deduplic.streamlit_gui.services.dedup_service import (
    resolve_all_action,
    commit_project_action,
    restore_project_action,
    get_pending_merges_service,
)
from deduplic.streamlit_gui.components.cluster_view import (
    AVAILABLE_METHODS,
    EXCLUDED_METHODS,
)


def _on_commit_project(project_name: str, total_clusters: int):
    try:
        commit_project_action(project_name, remaining_clusters_count=total_clusters)

        st.session_state.pop("active_report", None)
        st.session_state.pop(f"report_data_{project_name}", None)

        st.session_state["selected_project_name"] = project_name
        st.session_state["sidebar_project_selectbox"] = project_name

        st.toast("Project changes successfully committed!")
    except Exception as e:
        st.error(f"Commit failed: {e}")


def _on_restore_project(project_name: str):
    try:
        restore_project_action(project_name)
        if "active_report" in st.session_state:
            del st.session_state["active_report"]
        st.toast("Project restored to original state")
    except Exception as e:
        st.error(f"Restore failed: {e}")


def render_project_global_actions(project_name: str, total_clusters: int):
    st.markdown("---")

    pending_merges = get_pending_merges_service(project_name)
    merges_count = len(pending_merges)
    has_merges = merges_count > 0

    if total_clusters > 0:
        st.markdown("##### Solve project by method:")
        col_select, _, col_btn = st.columns([3, 6, 1])

        with col_select:
            selected_global_method = st.selectbox(
                "Method for all clusters:",
                options=[m for m in AVAILABLE_METHODS if m not in EXCLUDED_METHODS],
                key=f"select_global_method_{project_name}",
                label_visibility="collapsed",
            )

        with col_btn:
            if st.button(
                "Resolve all",
                key=f"btn_dedup_all_{project_name}",
                type="primary",
                use_container_width=True,
            ):
                resolve_all_action(project_name, selected_global_method)
                st.toast(f"Applied '{selected_global_method}' to all clusters!")
                st.rerun()

        st.markdown("---")

    if has_merges:
        st.warning(
            f"You have **{merges_count}** pending merge operation(s) to resolve before committing."
        )

    col_commit, col_restore, _, col_merge = st.columns([2, 2, 4, 2])

    with col_commit:
        st.button(
            "Commit",
            key=f"btn_commit_{project_name}",
            type="primary",
            disabled=has_merges,
            on_click=_on_commit_project,
            args=(project_name, total_clusters),
            use_container_width=True,
        )

    with col_restore:
        st.button(
            "Restore",
            key=f"btn_restore_{project_name}",
            type="secondary",
            on_click=_on_restore_project,
            args=(project_name,),
            use_container_width=True,
        )

    with col_merge:
        label_merge = f"Solve Merges ({merges_count})" if has_merges else "Merges"
        if st.button(
            label_merge,
            key=f"btn_solve_merges_{project_name}",
            type="secondary",
            use_container_width=True,
        ):
            st.session_state.pop("active_edit_key", None)
            st.session_state["open_merge_dialog"] = True
            st.rerun()

