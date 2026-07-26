import streamlit as st
from streamlit_gui.utils.project_loader import get_projects_info


def render_sidebar() -> tuple[str | None, str | None]:
    """
    Renderiza el panel lateral y retorna (selected_project_name, project_status).
    """
    with st.sidebar:
        st.title("📂 Projects")

        projects_info = get_projects_info()

        if not projects_info:
            st.warning("No projects were found in 'projects/'.")
            selected_name = None
        else:
            options = list(projects_info.keys())

            def format_label(name):
                if not name:
                    return ""
                status = projects_info.get(name)
                icon = "🟢" if status == "committed" else "🟡"
                return f"{icon} {name} ({status})"

            selected_name = st.selectbox(
                "Select a project:",
                options=options,
                index=None,
                placeholder="Choose a project...",
                format_func=format_label
            )

        st.markdown("---")
        st.caption("🟢 Committed | 🟡 In Progress")

    status = projects_info.get(selected_name) if selected_name else None
    return selected_name, status