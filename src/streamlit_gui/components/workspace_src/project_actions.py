# src/streamlit_gui/components/workspace_src/project_actions.py

import streamlit as st
from src.streamlit_gui.components.workspace_src.corpus_loader import (
    AVAILABLE_METHODS,
    EXCLUDED_METHODS,
)
from src.streamlit_gui.services.dedup_service import (
    resolve_all_action,
    commit_project_action,
    restore_project_action,
    get_pending_merges_service,
)
from src.streamlit_gui.components.workspace_src.merge_dialog import render_merge_modal


def _on_resolve_all(project_name: str, method_key: str):
    method = st.session_state.get(method_key)
    print(f"--> [DEBUG Callback] Resolviendo proyecto '{project_name}' con método '{method}'")
    resolve_all_action(project_name=project_name, method_name=method)
    st.toast("All pending clusters resolved successfully!", icon="🚀")


def _on_commit_project(project_name: str, total_clusters: int):
    try:
        commit_project_action(project_name, remaining_clusters_count=total_clusters)
        # Limpiamos el caché del reporte en sesión
        if "active_report" in st.session_state:
            del st.session_state["active_report"]
        st.toast("Project changes successfully committed!", icon="💾")
    except Exception as e:
        st.error(f"Commit failed: {e}")


def _on_restore_project(project_name: str):
    try:
        restore_project_action(project_name)
        if "active_report" in st.session_state:
            del st.session_state["active_report"]
        st.toast("Project restored to original state!", icon="🔄")
    except Exception as e:
        st.error(f"Restore failed: {e}")


def render_project_global_actions(project_name: str, total_clusters: int):
    st.markdown("---")
    
    # Check de merges pendientes
    pending_merges = get_pending_merges_service(project_name)
    merges_count = len(pending_merges)
    has_merges = merges_count > 0

    # 1. SECCIÓN: DEDUPLICATE ALL (Solo si quedan clusters)
    if total_clusters > 0:
        # ... (tu código del selector deduplicate all) ...
        pass

    # 2. SECCIÓN: MERGES PENDIENTES & PERSISTENCIA
    st.markdown("##### Project Persistence & Merges:")

    if has_merges:
        st.warning(
            f"⚠️ You have **{merges_count}** pending merge operation(s) to resolve before committing.",
            icon="⚠️"
        )

    col_commit, col_restore, col_merge = st.columns([2, 2, 3])

    with col_commit:
        st.button(
            "💾 Commit Changes",
            key=f"btn_commit_{project_name}",
            type="primary",
            disabled=has_merges,
            on_click=_on_commit_project,
            args=(project_name, total_clusters),
            use_container_width=True,
        )

    with col_restore:
        st.button(
            "🔄 Restore Original",
            key=f"btn_restore_{project_name}",
            type="secondary",
            on_click=_on_restore_project,
            args=(project_name,),
            use_container_width=True,
        )

    with col_merge:
        # Botón que invoca el modal de merges
        label_merge = f"🧩 Solve Merges ({merges_count})" if has_merges else "🧩 Solve Merges"
        if st.button(label_merge, key=f"btn_solve_merges_{project_name}", type="secondary", use_container_width=True):
            render_merge_modal(project_name)
