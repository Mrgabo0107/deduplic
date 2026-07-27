import streamlit as st
from src.streamlit_gui.components.workspace_src.corpus_loader import AVAILABLE_METHODS, EXCLUDED_METHODS


def render_connection_explorer(
    component_id: int | str,
    c_idx: int,
    edges: list,
    corpus_lookup: dict
):
    """Renderiza el explorador lateral/detallado de conexiones dentro de un cluster."""

    if not edges:
        st.info("No connections found for this component.")
        return

    col_nav, col_detail = st.columns([1, 6])
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
                key=f"e_page_{component_id}_{c_idx}"
            )
            e_start = (e_page - 1) * MAX_EDGES_PER_PAGE
            e_end = min(e_page * MAX_EDGES_PER_PAGE, total_edges)
            current_edges = edges[e_start:e_end]

            st.caption(
                f"connections **{e_start + 1}** to **{e_end}** of **{total_edges}**"
            )
        else:
            e_start = 0
            current_edges = edges

        edge_options = {
            f"🔹 `{e.get('pair', ['?','?'])[0]}` ↔ `{e.get('pair', ['?','?'])[1]}`": (e_start + idx, e)
            for idx, e in enumerate(current_edges)
        }

        selected_label = st.radio(
            "Connections list",
            options=list(edge_options.keys()),
            key=f"radio_edge_{component_id}_{c_idx}",
            label_visibility="collapsed"
        )

        e_idx, selected_edge = edge_options[selected_label]

    with col_detail:
        pair = selected_edge.get("pair", ["N/A", "N/A"])
        elem_a, elem_b = pair[0], pair[1]
        details = selected_edge.get("details", {})

        data_a = (
            corpus_lookup.get(elem_a)
            or corpus_lookup.get(str(elem_a))
            or {"id": elem_a}
        )
        data_b = (
            corpus_lookup.get(elem_b)
            or corpus_lookup.get(str(elem_b))
            or {"id": elem_b}
        )

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
        m_col, b_col = st.columns([3, 1])

        with m_col:
            conn_method = st.selectbox(
                "Method",
                options=AVAILABLE_METHODS,
                key=f"method_edge_{component_id}_{c_idx}_{e_idx}",
                label_visibility="collapsed"
            )

        with b_col:
            if st.button(
                "Resolve",
                key=f"btn_edge_{component_id}_{c_idx}_{e_idx}"
            ):
                st.toast(
                    f"Resolved connection {elem_a} <-> {elem_b} using '{conn_method}'.",
                    icon="✅"
                )


def render_component_item(
    component: dict,
    start_idx: int,
    rel_idx: int,
    corpus_lookup: dict
):
    """Renderiza un Cluster individual dentro del expansor."""
    c_idx = start_idx + rel_idx
    component_id = component.get("component_id", c_idx)
    nodes = component.get("nodes", [])
    edges = component.get("edges_trazability", [])
    if not nodes or not edges:
        pass

    MAX_NODES_TO_SHOW = 6
    nodes_str = ", ".join(map(str, nodes[:MAX_NODES_TO_SHOW]))
    if len(nodes) > MAX_NODES_TO_SHOW:
        nodes_str += f" (+{len(nodes) - MAX_NODES_TO_SHOW} more)"

    label = f"**[{nodes_str}]** — ({len(edges)} connections)"

    with st.expander(label, expanded=False):
        st.markdown("##### Resolve cluster by method:")
        c1, c2 = st.columns([3, 1])
        with c1:
            cluster_methods = [
                m for m in AVAILABLE_METHODS
                if m not in EXCLUDED_METHODS
            ]
            selected_cluster_method = st.selectbox(
                "Deduplication Method",
                options=cluster_methods,
                key=f"method_comp_{component_id}_{c_idx}",
                label_visibility="collapsed"
            )
        with c2:
            if st.button(
                "Resolve",
                key=f"btn_comp_{component_id}_{c_idx}",
                type="primary"
            ):
                st.toast(
                    f"Resolving Cluster {component_id} using '{selected_cluster_method}'..."
                )

        st.markdown("---")
        render_connection_explorer(component_id, c_idx, edges, corpus_lookup)