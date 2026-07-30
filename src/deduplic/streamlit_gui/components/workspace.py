import json
import streamlit as st
from deduplic.streamlit_gui.utils.project_loader import (
    load_project_report,
    load_dedup_corpus,
    deduplic_get_projects_info,
    PROJECTS_DIR
)
from deduplic.streamlit_gui.components.workspace_src import (
    get_cached_corpus,
    get_corpus_mtime,
    render_component_item,
    render_project_global_actions,
)
from deduplic.streamlit_gui.components.workspace_src.merge_dialog import render_merge_modal


def get_active_report(project_name: str):
    draft_report = PROJECTS_DIR / project_name / ".draft" / "report.json"
    if draft_report.exists():
        with open(draft_report, "r", encoding="utf-8") as f:
            return json.load(f)
    return load_project_report(project_name)


def render_workspace(project_name: str | None):
    """Renders the main workspace based on the active project."""

    if not project_name:
        st.info("Select a project from the sidebar or click **'New Project'** to get started.")
        return

    # -------------------------------------------------------------------
    # AUTO-TRIGGER: Si la sesión activó el diálogo de merges, lo abre
    # -------------------------------------------------------------------
    if st.session_state.get("open_merge_dialog", False):
        st.session_state["open_merge_dialog"] = False
        render_merge_modal(project_name)

    projects_info = deduplic_get_projects_info()
    status = projects_info.get(project_name)

    # -------------------------------------------------------------------
    # CASE 1: COMMITTED
    # -------------------------------------------------------------------
    if status == "committed":
        st.markdown(
            f"""
            <span style="font-size: 35px; font-weight: bold;">{project_name}</span> 
            <span style="font-size: 13px; color: gray;">🟢 Committed</span>
            """,
            unsafe_allow_html=True
        )

        dedup_data = load_dedup_corpus(project_name)
        if dedup_data is not None:
            json_string = json.dumps(dedup_data, ensure_ascii=False, indent=2)

            col_title, col_download = st.columns([9, 1])
            with col_title:
                st.write("### Final Deduplicated Corpus")
            with col_download:
                st.download_button(
                    label="Download",
                    data=json_string,
                    file_name=f"{project_name}_dedup.json",
                    mime="application/json",
                    type="primary",
                    use_container_width=True
                )

            st.json(dedup_data, expanded=False)
        else:
            st.error("The file 'dedup_corpus.json' could not be found.")

    # -------------------------------------------------------------------
    # CASE 2: IN PROGRESS
    # -------------------------------------------------------------------
    else:
        st.markdown(
            f"""
            <span style="font-size: 35px; font-weight: bold;">{project_name}</span> 
            <span style="font-size: 13px; color: gray;">🟡 In Progress</span>
            """,
            unsafe_allow_html=True
        )

        clusters = get_active_report(project_name)

        if clusters is None:
            st.warning("No report file was found for this project.")
            return

        clusters = [
            c for c in clusters 
            if c.get("nodes")
        ]

        if not clusters:
            st.success("All clusters have been resolved! You are ready to commit your changes.")

        mtime = get_corpus_mtime(project_name)
        corpus_lookup = get_cached_corpus(project_name, mtime)

        total_clusters = len(clusters)
        st.caption(f"Total pending clusters: **{total_clusters}**")

        # --- PAGINACIÓN DE CLUSTERS ---
        ITEMS_PER_PAGE = 15
        total_pages = (total_clusters + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

        if total_pages > 1:
            p_col1, p_col2 = st.columns([1, 3])
            with p_col1:
                current_page = st.number_input(
                    f"Page (1 - {total_pages})",
                    min_value=1,
                    max_value=total_pages,
                    value=1,
                    step=1,
                    key=f"pagination_{project_name}"
                )
            with p_col2:
                st.write(" ")
                st.write(" ")
                st.caption(
                    f"Clusters **{(current_page - 1) * ITEMS_PER_PAGE + 1}** "
                    f"to **{min(current_page * ITEMS_PER_PAGE, total_clusters)}** of **{total_clusters}**"
                )

            start_idx = (current_page - 1) * ITEMS_PER_PAGE
            end_idx = start_idx + ITEMS_PER_PAGE
            visible_clusters = clusters[start_idx:end_idx]
        else:
            start_idx = 0
            visible_clusters = clusters

        st.markdown("---")

        # --- RENDERIZADO DE CLUSTERS ---
        for rel_idx, component in enumerate(visible_clusters):
            render_component_item(
                project_name,
                component, 
                start_idx, 
                rel_idx, 
                corpus_lookup
            )

        # --- SECCIÓN GLOBAL INFERIOR ---
        render_project_global_actions(project_name, total_clusters)
