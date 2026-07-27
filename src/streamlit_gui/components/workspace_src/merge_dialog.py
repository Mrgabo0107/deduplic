# src/streamlit_gui/components/workspace_src/merge_dialog.py

import streamlit as st
import difflib
from src.streamlit_gui.services.dedup_service import (
    get_pending_merges_service,
    execute_single_merge_service,
    forget_single_merge_service,
    forget_all_merges_service, # <-- Nuevo servicio
)


def _render_diff_html(text_a: str, text_b: str) -> str:
    """Genera un HTML simple con diferencias resaltadas en verde/rojo entre dos textos."""
    matcher = difflib.SequenceMatcher(None, text_a, text_b)
    html_a = []
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            html_a.append(text_a[i1:i2])
        elif tag == 'delete' or tag == 'replace':
            html_a.append(f"<span style='background-color: #ff4d4d; color: white; padding: 0 2px;'>{text_a[i1:i2]}</span>")
        elif tag == 'insert':
            html_a.append(f"<span style='background-color: #2eb82e; color: white; padding: 0 2px;'>{text_b[j1:j2]}</span>")
            
    return "".join(html_a)


@st.dialog("Merge manager", width="large")
def render_merge_modal(project_name: str):
    pending_merges = get_pending_merges_service(project_name)

    if not pending_merges:
        st.info("No pending merges to resolve!")
        if st.button("Close", use_container_width=True):
            st.rerun()
        return

    # 1. Mapa de Opciones
    options_map = {
        f"{m.get('node_a_id')} ↔ {m.get('node_b_id')}": idx
        for idx, m in enumerate(pending_merges)
    }

    # Controles superiores (Selectbox + Skip + Skip All)
    col_sel, _, col_skip, col_skip_all = st.columns([4,1, 1, 1])

    with col_sel:
        selected_label = st.selectbox(
            "Select Merge Draft:",
            options=list(options_map.keys()),
            key=f"merge_modal_select_{project_name}",
            label_visibility="collapsed"
        )

    # Extraemos los datos del merge seleccionado de forma anticipada
    current_idx = options_map[selected_label]
    merge_item = pending_merges[current_idx]
    filename = merge_item.get("_file_name", "")
    node_a = merge_item.get("node_a", {})
    node_b = merge_item.get("node_b", {})
    node_a_id = merge_item.get("node_a_id")
    node_b_id = merge_item.get("node_b_id")
    component_id = merge_item.get("component_id", "cluster")

    with col_skip:
        if st.button("Skip", key=f"btn_forget_{filename}", type="secondary", use_container_width=True):
            forget_single_merge_service(project_name, filename)
            st.toast(f"Discarded merge {filename}")
            st.session_state["open_merge_dialog"] = True
            st.rerun()

    with col_skip_all:
        if st.button("Skip All", key=f"btn_forget_all_{project_name}", type="secondary", use_container_width=True):
            forget_all_merges_service(project_name)
            st.toast("Discarded all pending merges!")
            st.rerun()

    st.markdown("---")

    # 2. Encabezado de información
    st.caption(f"Status: **{merge_item.get('_status', 'draft').upper()}** | File: `{filename}`")

    # 3. Comparación de llaves
    all_keys = sorted(list(set(node_a.keys()) | set(node_b.keys())))
    resolved_fields = {}

    for key in all_keys:
        if key.startswith("_"):
            continue

        val_a = str(node_a.get(key, ""))
        val_b = str(node_b.get(key, ""))

        with st.container(border=True):
            st.markdown(f"**Field: `{key}`**")
            col_a, col_b = st.columns(2)

            with col_a:
                st.markdown(f"**Record A (ID: {node_a_id})**")
                st.code(val_a if val_a else "None", language=None)

            with col_b:
                st.markdown(f"**Record B (ID: {node_b_id})**")
                st.code(val_b if val_b else "None", language=None)

            choice = st.radio(
                f"Keep for `{key}`:",
                options=["Record A", "Record B", "Custom Edit"],
                horizontal=True,
                key=f"radio_{filename}_{key}"
            )

            if choice == "Record A":
                resolved_fields[key] = val_a
            elif choice == "Record B":
                resolved_fields[key] = val_b
            else:
                if val_a != val_b:
                    diff_html = _render_diff_html(val_a, val_b)
                    st.markdown("**Difference Preview (Diff):**", unsafe_allow_html=True)
                    st.markdown(f"<div style='background-color: #1e1e1e; padding: 8px; border-radius: 4px;'>{diff_html}</div>", unsafe_allow_html=True)

                custom_val = st.text_area(
                    f"Edit value for `{key}`:",
                    value=val_a,
                    key=f"custom_{filename}_{key}"
                )
                resolved_fields[key] = custom_val

    st.markdown("---")

    # 4. Confirmar Fusión
    if st.button("✅ Apply Merge Decision", type="primary", use_container_width=True):
        execute_single_merge_service(
            project_name=project_name,
            node_a_id=node_a_id,
            node_b_id=node_b_id,
            component_id=component_id
        )
        st.toast("Merge applied successfully!", icon="✨")
        st.session_state["open_merge_dialog"] = True
        st.rerun()