"""Sidebar Navigation Component for Deduplic Streamlit GUI.

Location: src/deduplic/streamlit_gui/components/sidebar.py
"""

import json
from typing import Optional
import streamlit as st

from deduplic.streamlit_gui.services.project_service import (
    create_new_project_from_upload,
    delete_project_directory,
    deduplic_get_projects_info,
)


def _on_delete_project():
    """Callback execution before rendering to delete the selected project."""
    active_proj = st.session_state.get("selected_project_name")
    if active_proj:
        # 1. Borrado mediante el servicio delegado al core
        success = delete_project_directory(active_proj)

        if success:
            # 2. Limpieza de estado en Streamlit
            st.session_state["selected_project_name"] = None
            st.session_state["sidebar_project_selectbox"] = None

            report_key = f"report_data_{active_proj}"
            if report_key in st.session_state:
                del st.session_state[report_key]

            st.toast(f"Project '{active_proj}' deleted successfully.")
        else:
            st.error(f"Failed to delete project '{active_proj}'.")


def render_sidebar() -> Optional[str]:
    """Renders the sidebar with project creation, selection, and deletion."""
    with st.sidebar:
        st.title("Deduplic")

        # -------------------------------------------------------------------
        # 1. NEW PROJECT CREATION POPOVER
        # -------------------------------------------------------------------
        with st.popover("New Project", use_container_width=True):

            # Garantizar versión única para resetear el file uploader de forma nativa
            if "uploader_version" not in st.session_state:
                st.session_state["uploader_version"] = 0

            uploader_key = (
                f"sidebar_file_uploader_{st.session_state['uploader_version']}"
            )

            uploaded_file = st.file_uploader(
                "Select a JSON file", type=["json"], key=uploader_key
            )

            if uploaded_file is not None:
                try:
                    raw_bytes = uploaded_file.getvalue()
                    sample_data = json.loads(raw_bytes.decode("utf-8"))

                    sample_rec = (
                        sample_data[0]
                        if isinstance(sample_data, list) and len(sample_data) > 0
                        else {}
                    )
                    detected_keys = [
                        k for k in sample_rec.keys() if not k.startswith("_")
                    ]

                    st.caption(f"Detected records: **{len(sample_data)}**")

                    custom_keys_str = st.text_input(
                        "Fields to Compare (comma separated)",
                        value=", ".join(detected_keys[:2])
                        if detected_keys
                        else "",
                        placeholder="text, title, author, date",
                    )
                    selected_keys = [
                        k.strip()
                        for k in custom_keys_str.split(",")
                        if k.strip()
                    ]

                    threshold = st.slider(
                        "Similarity Threshold",
                        min_value=0.0,
                        max_value=1.0,
                        value=0.8,
                        step=0.05,
                    )

                    if st.button(
                        "Create Project",
                        type="primary",
                        use_container_width=True,
                    ):
                        if not selected_keys:
                            st.error("You must select at least one field.")
                        else:
                            with st.spinner("Analyzing and processing..."):
                                uploaded_file.seek(0)
                                (
                                    created_path,
                                    base_name,
                                ) = create_new_project_from_upload(
                                    uploaded_file, selected_keys, threshold
                                )

                            if created_path is None:
                                st.success(
                                    f"No duplicates were found in '{uploaded_file.name}' "
                                    f"using a threshold of {threshold}. No project was created."
                                )
                            else:
                                actual_name = created_path.name

                                if actual_name != base_name:
                                    st.toast(
                                        f"A project with that name already exists. Saved as '{actual_name}'."
                                    )
                                else:
                                    st.toast(
                                        f"Project '{actual_name}' created successfully.",
                                    )

                                # 1. Seleccionar el nuevo proyecto en el Session State
                                st.session_state["selected_project_name"] = (
                                    actual_name
                                )
                                st.session_state[
                                    "sidebar_project_selectbox"
                                ] = actual_name

                                # 2. Incrementar versión del uploader para resetearlo y cerrar el popover
                                st.session_state["uploader_version"] += 1

                                st.rerun()

                except Exception as e:
                    st.error(f"Error reading the file: {e}")

        st.markdown("---")

        # -------------------------------------------------------------------
        # 2. EXISTING PROJECT SELECTOR
        # -------------------------------------------------------------------
        st.subheader("Projects")
        projects_info = deduplic_get_projects_info()

        if not projects_info:
            st.caption("No projects found in the 'projects/' directory.")
            st.session_state["selected_project_name"] = None
            st.session_state["sidebar_project_selectbox"] = None
        else:
            options = list(projects_info.keys())

            def format_label(name):
                if not name:
                    return ""
                status = projects_info.get(name)
                icon = "🟢" if status == "committed" else "🟡"
                return f"{icon} {name} ({status})"

            # Si el proyecto guardado en la key del selectbox ya no existe entre las opciones, lo limpiamos
            if (
                st.session_state.get("sidebar_project_selectbox")
                not in options
            ):
                st.session_state["sidebar_project_selectbox"] = None

            selected_name = st.selectbox(
                "Select a project:",
                options=options,
                placeholder="Choose a project...",
                format_func=format_label,
                key="sidebar_project_selectbox",
            )

            # Mantenemos sincronizado selected_project_name
            st.session_state["selected_project_name"] = selected_name

        # -------------------------------------------------------------------
        # 3. DELETE PROJECT BUTTON
        # -------------------------------------------------------------------
        has_active_project = bool(
            st.session_state.get("selected_project_name")
        )

        st.button(
            "Delete Project",
            type="secondary",
            disabled=not has_active_project,
            use_container_width=True,
            key="btn_delete_project",
            on_click=_on_delete_project,
        )

        st.markdown("---")
        st.caption("🟢 Committed | 🟡 In Progress")

    return st.session_state.get("selected_project_name")