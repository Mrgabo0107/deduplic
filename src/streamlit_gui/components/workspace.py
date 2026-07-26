import streamlit as st
from utils.project_loader import load_project_report, load_dedup_corpus


def render_workspace(project_name: str | None, status: str | None):
    """Renderiza el área de trabajo principal según el proyecto activo."""
    st.title("Deduplicator Workspace")

    if not project_name:
        st.info("Select a project from the sidebar to get started.")
        return

    st.subheader(f"Active project: `{project_name}`")

    # CASO 1: Committed
    if status == "committed":
        st.success("Project committed")
        dedup_data = load_dedup_corpus(project_name)

        if dedup_data is not None:
            st.write("### Final Deduplicated Corpus")
            st.json(dedup_data, expanded=False)
        else:
            st.error("The file 'dedup_corpus.json' could not be found.")

    # CASO 2: In Progress
    else:
        st.info("🟡 Project in progress")
        report_data = load_project_report(project_name)

        if report_data is not None:
            st.write("### Raw Report (Draft)")
            st.json(report_data, expanded=True)
        else:
            st.warning("No report file was found for this project.")