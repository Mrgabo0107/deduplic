import json
import streamlit as st
from deduplic.streamlit_gui.utils.diff_utils import render_diff_html
from deduplic.streamlit_gui.utils.project_loader import PROJECTS_DIR


def save_merge_draft_file(project_name: str, filename: str, merge_status: dict):
    """Escribe el objeto merge_status directamente en el archivo JSON del disco."""
    file_path = PROJECTS_DIR / project_name / "merges" / filename
    if file_path.exists():
        clean_data = {k: v for k, v in merge_status.items() if not k.startswith("_")}
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(clean_data, f, ensure_ascii=False, indent=2)


def render_focused_editor(project_name: str, filename: str):
    """Renderiza la sub-vista de edición dividida en dos columnas: Izq (Editor) / Der (Diff)."""
    merge_status = st.session_state["merge_status"]
    rec_a = merge_status.get("rec_a", {})
    rec_b = merge_status.get("rec_b", {})

    edit_info = st.session_state["active_edit_key"]
    e_key = edit_info["key"]
    e_base_source = edit_info["base_source"]  # "a" o "b"

    if e_base_source == "a":
        base_text = str(rec_a.get(e_key, "")).strip()
        compare_text = str(rec_b.get(e_key, "")).strip()
    else:
        base_text = str(rec_b.get(e_key, "")).strip()
        compare_text = str(rec_a.get(e_key, "")).strip()

    saved_edit_val = merge_status.get("fields", {}).get(e_key, {}).get("edit")
    if saved_edit_val is not None:
        current_custom_val = str(saved_edit_val).strip()
    else:
        current_custom_val = base_text

    diff_html = render_diff_html(base_text, compare_text)

    col_left, col_right = st.columns(2)
    text_area_key = f"modal_focused_editor_{e_key}"

    # --- COLUMNA IZQUIERDA: EDITOR ---
    with col_left:
        st.text_area(
            "Edit content:",
            value=current_custom_val,
            height=380,
            key=text_area_key,
            label_visibility="collapsed"
        )

        col_save, col_restore, col_cancel = st.columns([2, 2, 1])
        
        with col_save:
            if st.button("Apply Edit", type="primary", use_container_width=True):
                fresh_typed_value = st.session_state.get(text_area_key, "").strip()

                field_data = merge_status["fields"].get(e_key, {})
                field_data["keep"] = True
                field_data["source"] = e_base_source
                field_data["edit"] = fresh_typed_value
                merge_status["fields"][e_key] = field_data

                save_merge_draft_file(project_name, filename, merge_status)
                
                del st.session_state["active_edit_key"]
                st.session_state["open_merge_dialog"] = True
                st.rerun()

        with col_restore:
            if st.button("Restore", type="secondary", use_container_width=True):
                if "fields" in merge_status and e_key in merge_status["fields"]:
                    merge_status["fields"][e_key]["edit"] = None
                    
                save_merge_draft_file(project_name, filename, merge_status)
                
                del st.session_state["active_edit_key"]
                st.session_state["open_merge_dialog"] = True
                st.rerun()

        with col_cancel:
            if st.button("Cancel", type="secondary", use_container_width=True):
                if "fields" in merge_status and e_key in merge_status["fields"]:
                    merge_status["fields"][e_key]["edit"] = None

                save_merge_draft_file(project_name, filename, merge_status)

                del st.session_state["active_edit_key"]
                st.session_state["open_merge_dialog"] = True
                st.rerun()

    # --- COLUMNA DERECHA: DIFF VISUAL ---
    with col_right:
        diff_styled_html = f"""<style>
.diff-container del, .diff-container strike {{
    text-decoration: none !important;
    background-color: rgba(255, 0, 0, 0.25) !important;
    color: #ff6b6b !important;
}}
</style>
<div class="diff-container" style="
    background-color: #1a1a1a;
    color: #e0e0e0;
    padding: 12px;
    border: 1px solid #333;
    border-radius: 6px;
    font-family: monospace;
    font-size: 13px;
    height: 380px;
    overflow-y: auto;
    text-align: left;
    text-indent: 0px !important;
    white-space: pre-wrap;
    word-break: break-word;
">
    {diff_html}
</div>"""
        st.markdown(diff_styled_html, unsafe_allow_html=True)