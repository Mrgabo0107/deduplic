# """Merge Manager Modal Component for Deduplic Streamlit GUI.

# Location: src/deduplic/streamlit_gui/components/merge_view.py
# """

# import json
# import streamlit as st

# from deduplic.streamlit_gui.services.dedup_service import (
#     get_pending_merges_service,
#     execute_single_merge_service,
#     forget_single_merge_service,
#     forget_all_merges_service,
# )
# from deduplic.streamlit_gui.components.merge_view_src.merge_editor_view import (
#     render_focused_editor,
#     save_merge_draft_file,
# )


# def render_text_box(text_content: str, max_height: int = 150):
#     """Renderiza un cuadro de texto formateado con scroll."""
#     if not text_content or text_content == "None":
#         text_content = "<i style='color: #888;'>Empty / None</i>"
#     else:
#         text_content = text_content.strip().replace("<", "&lt;").replace(">", "&gt;")

#     html_code = f"""
#     <div style="
#         background-color: #1e1e1e;
#         color: #e0e0e0;
#         border: 1px solid #333;
#         border-radius: 6px;
#         padding: 10px;
#         max-height: {max_height}px;
#         overflow-y: auto;
#         font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
#         font-size: 13px;
#         line-height: 1.5;
#         text-align: left;
#         text-indent: 0px !important;
#         white-space: pre-wrap;
#         word-break: break-word;
#     ">
#         {text_content}
#     </div>
#     """
#     st.markdown(html_code, unsafe_allow_html=True)


# @st.dialog("Merge manager", width="large")
# def render_merge_modal(project_name: str):
#     pending_merges = get_pending_merges_service(project_name)

#     if not pending_merges:
#         st.info("No pending merges to resolve!")
#         if st.button("Close", use_container_width=True):
#             st.rerun()
#         return

#     options_map = {
#         f"Node {m.get('node_a_id')} ↔ Node {m.get('node_b_id')}": idx
#         for idx, m in enumerate(pending_merges)
#     }

#     col_sel, _, col_skip, col_skip_all = st.columns([4, 0.5, 1.2, 1.3])

#     with col_sel:
#         selected_label = st.selectbox(
#             "Select Merge Draft:",
#             options=list(options_map.keys()),
#             key=f"merge_modal_select_{project_name}",
#             label_visibility="collapsed",
#         )

#     current_idx = options_map[selected_label]
#     merge_item_disk = pending_merges[current_idx]
#     filename = merge_item_disk.get("_file_name", "")

#     if "merge_status" not in st.session_state or st.session_state.get("_current_merge_filename") != filename:
#         st.session_state["merge_status"] = json.loads(json.dumps(merge_item_disk))
#         st.session_state["_current_merge_filename"] = filename
#         st.session_state.pop("active_edit_key", None)

#     merge_status = st.session_state["merge_status"]

#     rec_a = merge_status.get("rec_a", {})
#     rec_b = merge_status.get("rec_b", {})
#     saved_fields = merge_status.get("fields", {})

#     node_a_id = merge_status.get("node_a_id")
#     node_b_id = merge_status.get("node_b_id")

#     with col_skip:
#         if st.button("Skip", key=f"btn_forget_{filename}", type="secondary", use_container_width=True):
#             forget_single_merge_service(project_name, filename)
#             st.toast(f"Discarded merge {filename}")
#             st.session_state.pop("merge_status", None)
#             st.session_state.pop("active_edit_key", None) # <--- LIMPIEZA CLAVE
#             st.session_state["open_merge_dialog"] = True
#             st.rerun()

#     with col_skip_all:
#         if st.button("Skip All", key=f"btn_forget_all_{project_name}", type="secondary", use_container_width=True):
#             forget_all_merges_service(project_name)
#             st.toast("Discarded all pending merges!")
#             st.session_state.pop("merge_status", None)
#             st.session_state.pop("active_edit_key", None) # <--- LIMPIEZA CLAVE
#             st.rerun()

#     st.markdown("---")

#     # VISTA ENFOCADA DE EDICIÓN AMPLIADA
#     if "active_edit_key" in st.session_state:
#         render_focused_editor(project_name, filename)
#         return

#     # VISTA GENERAL DE CAMPOS
#     all_keys = sorted(list(set(rec_a.keys()) | set(rec_b.keys())))

#     with st.container(height=500):
#         for key in all_keys:
#             if key.startswith("_"):
#                 continue

#             val_a = str(rec_a.get(key, ""))
#             val_b = str(rec_b.get(key, ""))

#             key_saved = saved_fields.get(key, {})
#             init_keep = key_saved.get("keep", False)
#             init_source = key_saved.get("source", "a") or "a"
#             init_edit = key_saved.get("edit", None)

#             with st.container(border=True):
#                 col_title, col_toggle = st.columns([5, 1])
#                 with col_title:
#                     st.markdown(f"### `{key}`")
#                 with col_toggle:
#                     toggle_key = f"toggle_{filename}_{key}"
#                     keep_field = st.toggle("Keep", value=init_keep, key=toggle_key)

#                 if "fields" not in merge_status:
#                     merge_status["fields"] = {}

#                 if not keep_field:
#                     merge_status["fields"][key] = {"keep": False, "source": None, "edit": None}
#                 else:
#                     col_a, col_b = st.columns(2)

#                     val_a_display = init_edit if (init_source == "a" and init_edit is not None) else val_a
#                     val_b_display = init_edit if (init_source == "b" and init_edit is not None) else val_b

#                     with col_a:
#                         st.markdown(
#                             f"**{node_a_id}**"
#                             + (" *(Edited)*" if init_source == "a" and init_edit is not None else "")
#                         )
#                         render_text_box(val_a_display, max_height=140)

#                     with col_b:
#                         st.markdown(
#                             f"**{node_b_id}**"
#                             + (" *(Edited)*" if init_source == "b" and init_edit is not None else "")
#                         )
#                         render_text_box(val_b_display, max_height=140)

#                     col_rad, col_btn_edit = st.columns([3, 1])
#                     radio_options = [f"{node_a_id}", f"{node_b_id}"]
#                     init_radio_idx = 1 if init_source == "b" else 0

#                     with col_rad:
#                         source_selected = st.radio(
#                             f"Select Source for `{key}`:",
#                             options=radio_options,
#                             index=init_radio_idx,
#                             horizontal=True,
#                             key=f"radio_src_{filename}_{key}",
#                             label_visibility="collapsed",
#                         )

#                     selected_src_code = node_a_id if source_selected == radio_options[0] else node_b_id

#                     with col_btn_edit:
#                         if st.button("Edit", key=f"btn_edit_{filename}_{key}", use_container_width=True):
#                             st.session_state["active_edit_key"] = {
#                                 "key": key,
#                                 "base_source": selected_src_code,
#                             }
#                             st.session_state["open_merge_dialog"] = True
#                             st.rerun()

#                     merge_status["fields"][key] = {
#                         "keep": True,
#                         "source": selected_src_code,
#                         "edit": init_edit if selected_src_code == init_source else None,
#                     }

#     save_merge_draft_file(project_name, filename, merge_status)

#     st.markdown("---")

#     if st.button("Apply Merge Decision", type="primary", use_container_width=True):
#         save_merge_draft_file(project_name, filename, merge_status)

#         target_component_id = merge_status.get("component_id", "cluster")
#         target_node_a = merge_status.get("node_a_id", node_a_id)
#         target_node_b = merge_status.get("node_b_id", node_b_id)

#         result = execute_single_merge_service(
#             project_name=project_name,
#             node_a_id=target_node_a,
#             node_b_id=target_node_b,
#             component_id=target_component_id,
#         )

#         if result == "applied":
#             st.toast("Merge applied successfully!")
#             if "merge_status" in st.session_state:
#                 del st.session_state["merge_status"]
#             if "_current_merge_filename" in st.session_state:
#                 del st.session_state["_current_merge_filename"]
#         elif result == "not_ready":
#             st.warning("The merge decision is incomplete. Please keep at least one field and select its source.")
#         else:
#             st.info(f"Merge status updated: {result}")

#         st.session_state["open_merge_dialog"] = True
#         st.rerun()

"""Merge Manager Modal Component for Deduplic Streamlit GUI.

Location: src/deduplic/streamlit_gui/components/merge_view.py
"""

import json
import streamlit as st

from deduplic.streamlit_gui.services.dedup_service import (
    get_pending_merges_service,
    execute_single_merge_service,
    forget_single_merge_service,
    forget_all_merges_service,
)
from deduplic.streamlit_gui.components.merge_view_src.merge_editor_view import (
    render_focused_editor,
    save_merge_draft_file,
)


def render_text_box(text_content: str, max_height: int = 150):
    """Renderiza un cuadro de texto formateado con scroll."""
    if not text_content or text_content == "None":
        text_content = "<i style='color: #888;'>Empty / None</i>"
    else:
        text_content = text_content.strip().replace("<", "&lt;").replace(">", "&gt;")

    html_code = f"""
    <div style="
        background-color: #1e1e1e;
        color: #e0e0e0;
        border: 1px solid #333;
        border-radius: 6px;
        padding: 10px;
        max-height: {max_height}px;
        overflow-y: auto;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 13px;
        line-height: 1.5;
        text-align: left;
        text-indent: 0px !important;
        white-space: pre-wrap;
        word-break: break-word;
    ">
        {text_content}
    </div>
    """
    st.markdown(html_code, unsafe_allow_html=True)


@st.dialog("Merge manager", width="large")
def render_merge_modal(project_name: str):
    pending_merges = get_pending_merges_service(project_name)

    if not pending_merges:
        st.info("No pending merges to resolve!")
        if st.button("Close", use_container_width=True):
            st.rerun()
        return

    options_map = {
        f"Node {m.get('node_a_id')} ↔ Node {m.get('node_b_id')}": idx
        for idx, m in enumerate(pending_merges)
    }

    col_sel, _, col_skip, col_skip_all = st.columns([4, 0.5, 1.2, 1.3])

    with col_sel:
        selected_label = st.selectbox(
            "Select Merge Draft:",
            options=list(options_map.keys()),
            key=f"merge_modal_select_{project_name}",
            label_visibility="collapsed",
        )

    current_idx = options_map[selected_label]
    merge_item_disk = pending_merges[current_idx]
    filename = merge_item_disk.get("_file_name", "")

    if "merge_status" not in st.session_state or st.session_state.get("_current_merge_filename") != filename:
        st.session_state["merge_status"] = json.loads(json.dumps(merge_item_disk))
        st.session_state["_current_merge_filename"] = filename
        st.session_state.pop("active_edit_key", None)

    merge_status = st.session_state["merge_status"]

    rec_a = merge_status.get("rec_a", {})
    rec_b = merge_status.get("rec_b", {})
    saved_fields = merge_status.get("fields", {})

    node_a_id = merge_status.get("node_a_id")
    node_b_id = merge_status.get("node_b_id")

    with col_skip:
        if st.button("Skip", key=f"btn_forget_{filename}", type="secondary", use_container_width=True):
            forget_single_merge_service(project_name, filename)
            st.toast(f"Discarded merge {filename}")
            st.session_state.pop("merge_status", None)
            st.session_state.pop("active_edit_key", None)
            st.session_state["open_merge_dialog"] = True
            st.rerun()

    with col_skip_all:
        if st.button("Skip All", key=f"btn_forget_all_{project_name}", type="secondary", use_container_width=True):
            forget_all_merges_service(project_name)
            st.toast("Discarded all pending merges!")
            st.session_state.pop("merge_status", None)
            st.session_state.pop("active_edit_key", None)
            st.rerun()

    st.markdown("---")

    # VISTA ENFOCADA DE EDICIÓN AMPLIADA
    if "active_edit_key" in st.session_state:
        render_focused_editor(project_name, filename)
        return

    # VISTA GENERAL DE CAMPOS
    all_keys = sorted(list(set(rec_a.keys()) | set(rec_b.keys())))

    with st.container(height=500):
        for key in all_keys:
            if key.startswith("_"):
                continue

            val_a = str(rec_a.get(key, ""))
            val_b = str(rec_b.get(key, ""))

            key_saved = saved_fields.get(key, {})
            init_keep = key_saved.get("keep", False)
            init_source = key_saved.get("source", "a") or "a"
            init_edit = key_saved.get("edit", None)

            with st.container(border=True):
                col_title, col_toggle = st.columns([5, 1])
                with col_title:
                    st.markdown(f"### `{key}`")
                with col_toggle:
                    toggle_key = f"toggle_{filename}_{key}"
                    keep_field = st.toggle("Keep", value=init_keep, key=toggle_key)

                if "fields" not in merge_status:
                    merge_status["fields"] = {}

                if not keep_field:
                    merge_status["fields"][key] = {"keep": False, "source": None, "edit": None}
                else:
                    col_a, col_b = st.columns(2)

                    # Se valida contra la fuente "a" o "b" estándar
                    val_a_display = init_edit if (init_source == "a" and init_edit is not None) else val_a
                    val_b_display = init_edit if (init_source == "b" and init_edit is not None) else val_b

                    with col_a:
                        st.markdown(
                            f"**{node_a_id}**"
                            + (" *(Edited)*" if init_source == "a" and init_edit is not None else "")
                        )
                        render_text_box(val_a_display, max_height=140)

                    with col_b:
                        st.markdown(
                            f"**{node_b_id}**"
                            + (" *(Edited)*" if init_source == "b" and init_edit is not None else "")
                        )
                        render_text_box(val_b_display, max_height=140)

                    col_rad, col_btn_edit = st.columns([3, 1])
                    radio_options = [f"{node_a_id}", f"{node_b_id}"]
                    init_radio_idx = 1 if init_source == "b" else 0

                    with col_rad:
                        source_selected = st.radio(
                            f"Select Source for `{key}`:",
                            options=radio_options,
                            index=init_radio_idx,
                            horizontal=True,
                            key=f"radio_src_{filename}_{key}",
                            label_visibility="collapsed",
                        )

                    # Mapeamos la selección a "a" o "b" de manera uniforme
                    selected_src_code = "a" if source_selected == radio_options[0] else "b"

                    with col_btn_edit:
                        if st.button("Edit", key=f"btn_edit_{filename}_{key}", use_container_width=True):
                            st.session_state["active_edit_key"] = {
                                "key": key,
                                "base_source": selected_src_code,
                            }
                            st.session_state["open_merge_dialog"] = True
                            st.rerun()

                    merge_status["fields"][key] = {
                        "keep": True,
                        "source": selected_src_code,
                        "edit": init_edit if selected_src_code == init_source else None,
                    }

    save_merge_draft_file(project_name, filename, merge_status)

    st.markdown("---")

    if st.button("Apply Merge Decision", type="primary", use_container_width=True):
        save_merge_draft_file(project_name, filename, merge_status)

        target_component_id = merge_status.get("component_id", "cluster")
        target_node_a = merge_status.get("node_a_id", node_a_id)
        target_node_b = merge_status.get("node_b_id", node_b_id)

        result = execute_single_merge_service(
            project_name=project_name,
            node_a_id=target_node_a,
            node_b_id=target_node_b,
            component_id=target_component_id,
        )

        if result == "applied":
            st.toast("Merge applied successfully!")
            if "merge_status" in st.session_state:
                del st.session_state["merge_status"]
            if "_current_merge_filename" in st.session_state:
                del st.session_state["_current_merge_filename"]
        elif result == "not_ready":
            st.warning("The merge decision is incomplete. Please keep at least one field and select its source.")
        else:
            st.info(f"Merge status updated: {result}")

        st.session_state["open_merge_dialog"] = True
        st.rerun()