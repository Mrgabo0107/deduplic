"""Cluster View & Connection Explorer Component for Deduplic Streamlit GUI.

Location: src/deduplic/streamlit_gui/components/cluster_view.py
"""

import json
import streamlit as st
from deduplic.config import settings
from deduplic.streamlit_gui.services.dedup_service import (
    resolve_edge_action,
    resolve_cluster_action,
)

AVAILABLE_METHODS = [
    "keep_all",
    "keep_first",
    "keep_last",
    "keep_largest",
    "keep_shortest",
    "keep_newest",
    "keep_oldest",
    "merge",
]

EXCLUDED_METHODS = ["merge"]


@st.cache_data(show_spinner="Updating corpus...")
def get_cached_corpus(project_name: str, last_modified: float) -> dict:
    """Carga el corpus y lo mantiene en RAM con caché condicional al mtime."""
    draft_corpus_path = settings.projects_dir / project_name / ".draft" / "corpus.json"
    if not draft_corpus_path.exists():
        draft_corpus_path = settings.projects_dir / project_name / "corpus.json"

    if draft_corpus_path.exists():
        try:
            with open(draft_corpus_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return {idx: rec for idx, rec in enumerate(data)}
                elif isinstance(data, dict):
                    return data
        except Exception:
            pass
    return {}


def get_corpus_mtime(project_name: str) -> float:
    """Obtiene la fecha de última modificación del archivo de corpus."""
    draft_path = settings.projects_dir / project_name / ".draft" / "corpus.json"
    if not draft_path.exists():
        draft_path = settings.projects_dir / project_name / "corpus.json"

    return draft_path.stat().st_mtime if draft_path.exists() else 0.0


def _on_resolve_edge(project_name: str, component_id: int | str, edge_idx: int, method_key: str):
    """Callback para resolver una conexión específica."""
    method = st.session_state.get(method_key)

    resolve_edge_action(
        project_name=project_name,
        component_id=component_id,
        edge_idx=edge_idx,
        method_name=method,
    )

    st.session_state["active_cluster_id"] = component_id
    st.toast("Connection resolved successfully")


def _on_resolve_cluster(project_name: str, component_id: int | str, method_key: str):
    """Callback para resolver un cluster completo."""
    method = st.session_state.get(method_key)

    resolve_cluster_action(
        project_name=project_name,
        component_id=component_id,
        method_name=method,
    )

    st.session_state["active_cluster_id"] = component_id
    st.toast("Cluster resolved successfully")


def render_connection_explorer(
    project_name: str,
    component_id: int | str,
    c_idx: int,
    edges: list,
    corpus_lookup: dict,
):
    """Renderiza el explorador lateral/detallado de conexiones dentro de un cluster."""
    if not edges:
        st.info("No connections found for this component.")
        return

    col_nav, col_detail = st.columns([1, 9])
    total_edges = len(edges)
    MAX_EDGES_PER_PAGE = 10

    with col_nav:
        st.markdown("##### Connections")

        if total_edges > MAX_EDGES_PER_PAGE:
            max_e_pages = (total_edges + MAX_EDGES_PER_PAGE - 1) // MAX_EDGES_PER_PAGE
            e_page = st.number_input(
                f"Page (1 - {max_e_pages})",
                min_value=1,
                max_value=max_e_pages,
                value=1,
                key=f"e_page_{component_id}_{c_idx}",
            )
            e_start = (e_page - 1) * MAX_EDGES_PER_PAGE
            e_end = min(e_page * MAX_EDGES_PER_PAGE, total_edges)
            current_edges = edges[e_start:e_end]

            st.caption(f"connections **{e_start + 1}** to **{e_end}** of **{total_edges}**")
        else:
            e_start = 0
            current_edges = edges

        edge_options = {
            f"🔹 `{e.get('pair', ['?','?'])[0]}` ↔ `{e.get('pair', ['?','?'])[1]}`": (
                e_start + idx,
                e,
            )
            for idx, e in enumerate(current_edges)
        }

        selected_label = st.radio(
            "Connections list",
            options=list(edge_options.keys()),
            key=f"radio_edge_{component_id}_{c_idx}",
            label_visibility="collapsed",
        )

        e_idx, selected_edge = edge_options[selected_label]

    with col_detail:
        pair = selected_edge.get("pair", ["N/A", "N/A"])
        elem_a, elem_b = pair[0], pair[1]
        details = selected_edge.get("details", {})

        data_a = corpus_lookup.get(elem_a) or corpus_lookup.get(str(elem_a)) or {"id": elem_a}
        data_b = corpus_lookup.get(elem_b) or corpus_lookup.get(str(elem_b)) or {"id": elem_b}

        st.markdown(f"### `{elem_a}` ↔ `{elem_b}`")

        if details:
            st.markdown("**Scores:**")
            lines = [f"- **{key_name}**: `{score * 100:.1f}%`" for key_name, score in details.items()]
            st.markdown("\n".join(lines))

        st.markdown("---")

        col_a, col_b = st.columns(2)
        with col_a:
            st.caption(f"Record ID: `{elem_a}`")
            st.json(data_a, expanded=False)

        with col_b:
            st.caption(f"Record ID: `{elem_b}`")
            st.json(data_b, expanded=False)

        st.markdown("---")

        st.markdown("##### Resolve connection by method:")
        m_col, b_col, _ = st.columns([3, 1, 5])
        method_key = f"method_edge_{component_id}_{c_idx}_{e_idx}"

        with m_col:
            st.selectbox(
                "Method",
                options=AVAILABLE_METHODS,
                key=method_key,
                label_visibility="collapsed",
            )
        with b_col:
            st.button(
                "Resolve",
                key=f"btn_edge_{component_id}_{c_idx}_{e_idx}",
                on_click=_on_resolve_edge,
                args=(project_name, component_id, e_idx, method_key),
            )


def render_component_item(
    project_name: str,
    component: dict,
    start_idx: int,
    rel_idx: int,
    corpus_lookup: dict,
):
    """Renderiza un Cluster individual dentro del expansor."""
    c_idx = start_idx + rel_idx
    component_id = component.get("component_id", c_idx)
    nodes = component.get("nodes", [])
    edges = component.get("edges_trazability", [])

    if not nodes and not edges:
        return

    MAX_NODES_TO_SHOW = 6
    nodes_str = ", ".join(map(str, nodes[:MAX_NODES_TO_SHOW]))
    if len(nodes) > MAX_NODES_TO_SHOW:
        nodes_str += f" (+{len(nodes) - MAX_NODES_TO_SHOW} more)"

    label = f"**[{nodes_str}]** — ({len(edges)} connections)"
    is_expanded = st.session_state.get("active_cluster_id") == component_id

    with st.expander(label, expanded=is_expanded):
        render_connection_explorer(project_name, component_id, c_idx, edges, corpus_lookup)
        st.markdown("---")
        st.markdown("##### Resolve cluster by method:")
        c1, _, c2 = st.columns([3, 6, 1])
        cluster_method_key = f"method_comp_{component_id}_{c_idx}"

        with c1:
            st.selectbox(
                "Method",
                options=AVAILABLE_METHODS,
                key=cluster_method_key,
                label_visibility="collapsed",
            )
        with c2:
            st.button(
                "Resolve",
                key=f"btn_comp_{component_id}_{c_idx}",
                type="primary",
                on_click=_on_resolve_cluster,
                args=(project_name, component_id, cluster_method_key),
            )