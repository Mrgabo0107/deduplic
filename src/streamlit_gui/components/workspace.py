import streamlit as st
from streamlit_gui.utils.project_loader import (
    load_project_report,
    load_dedup_corpus,
    get_projects_info,
)


def render_workspace(project_name: str | None):
    """Renders the main workspace based on the active project."""

    if not project_name:
        st.info("👈 Select a project from the sidebar or click **'➕ New Project'** to get started.")
        return

    # Get the current project status
    projects_info = get_projects_info()
    status = projects_info.get(project_name)

    # CASE 1: Committed
    if status == "committed":
        st.markdown(
            f"""
            <span style="font-size: 45px; font-weight: bold;">{project_name}:</span> 
            <span style="font-size: 30px; color: gray;">🟢 Committed</span>
            """,
            unsafe_allow_html=True
        )

        dedup_data = load_dedup_corpus(project_name)

        if dedup_data is not None:
            st.write("### Final Deduplicated Corpus")
            st.json(dedup_data, expanded=False)
        else:
            st.error("The file 'dedup_corpus.json' could not be found.")

    # CASE 2: In Progress
    else:
        st.markdown(
            f"""
            <span style="font-size: 45px; font-weight: bold;">{project_name}:</span> 
            <span style="font-size: 30px; color: gray;">🟡 Project in Progress</span>
            """,
            unsafe_allow_html=True
        )

        report_data = load_project_report(project_name)

        if report_data is not None:
            st.write("### Raw Report (Draft)")
            st.json(report_data, expanded=True)
        else:
            st.warning("No report file was found for this project.")