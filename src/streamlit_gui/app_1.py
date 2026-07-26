import json
import streamlit as st
from pathlib import Path

# Locate the projects/ directory relative to the project structure (src/streamlit_gui/app.py)
PROJECTS_DIR = Path(__file__).resolve().parents[2] / "projects"

st.set_page_config(
    page_title="Deduplicator Studio",
    page_icon="⚡",
    layout="wide"
)

# --- UTILITY FUNCTION ---
def get_projects_info():
    """Scans the projects/ directory and retrieves the status of each project from its metadata.json."""
    projects = {}
    if PROJECTS_DIR.exists():
        for p in PROJECTS_DIR.iterdir():
            if p.is_dir():
                meta_file = p / "metadata.json"
                if meta_file.exists():
                    try:
                        with open(meta_file, "r", encoding="utf-8") as f:
                            meta = json.load(f)
                            projects[p.name] = meta.get("status", "unknown")
                    except Exception:
                        projects[p.name] = "error"
                else:
                    projects[p.name] = "no_metadata"
    return projects


# --- SIDEBAR ---
with st.sidebar:
    st.title("📂 Projects")

    projects_info = get_projects_info()

    if not projects_info:
        st.warning("No projects were found in the 'projects/' directory.")
        selected_project_name = None
    else:
        # Format the project list with an icon representing its status
        options = list(projects_info.keys())

        def format_project_label(name):
            status = projects_info.get(name)
            icon = "🟢" if status == "committed" else "🟡"
            return f"{icon} {name} ({status})"

        selected_project_name = st.selectbox(
            "Select a project:",
            options=options,
            index=None,
            placeholder="Choose a project...",
            format_func=format_project_label
        )

    st.markdown("---")
    st.caption("🟢 Committed | 🟡 In Progress")


# --- MAIN CONTENT ---
st.title("Deduplicator Workspace")

if selected_project_name:
    project_path = PROJECTS_DIR / selected_project_name
    current_status = projects_info.get(selected_project_name)

    st.subheader(f"Active project: `{selected_project_name}`")

    # CASE 1: Finished project (committed)
    if current_status == "committed":
        st.success("Project committed")

        dedup_corpus_file = project_path / "dedup_corpus.json"
        if dedup_corpus_file.exists():
            with open(dedup_corpus_file, "r", encoding="utf-8") as f:
                dedup_data = json.load(f)

            st.write("### Final Deduplicated Corpus")
            st.json(dedup_data, expanded=False)
        else:
            st.error("The file 'dedup_corpus.json' could not be found in the project root.")

    # CASE 2: Project in progress
    else:
        st.info("🟡 Project in progress")

        # Prefer reading from .draft/report.json, falling back to report.json in the project root
        draft_report = project_path / ".draft" / "report.json"
        root_report = project_path / "report.json"

        report_file = draft_report if draft_report.exists() else root_report

        if report_file.exists():
            with open(report_file, "r", encoding="utf-8") as f:
                report_data = json.load(f)

            st.write("### Raw Report (Draft)")
            st.json(report_data, expanded=True)
        else:
            st.warning("No report file was found for this project.")

else:
    st.info("Select a project from the sidebar to get started.")