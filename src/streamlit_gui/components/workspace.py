import streamlit as st
from streamlit_gui.utils.project_loader import load_project_report, load_dedup_corpus


def render_workspace(project_name: str | None, status: str | None):
    """Renderiza el área de trabajo principal según el proyecto activo."""

    if not project_name:
        st.info("Select a project from the sidebar to get started.")
        return


    # CASO 1: Committed
    if status == "committed":
        st.markdown(
            f"""
            <span style="font-size: 45px; font-weight: bold;"> {project_name}:</span> 
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

    # CASO 2: In Progress
    else:
        st.markdown(
            f"""
            <span style="font-size: 45px; font-weight: bold;"> {project_name}:</span> 
            <span style="font-size: 30px; color: gray;">🟡 Project in progress</span>
            """,
            unsafe_allow_html=True
        )
        report_data = load_project_report(project_name)

        if report_data is not None:
            st.write("### Raw Report (Draft)")
            st.json(report_data, expanded=True)
        else:
            st.warning("No report file was found for this project.")