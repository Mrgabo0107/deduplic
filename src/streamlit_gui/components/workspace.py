import json
from pathlib import Path
import streamlit as st
from streamlit_gui.utils.project_loader import (
    load_project_report,
    load_dedup_corpus,
    get_projects_info,
    PROJECTS_DIR,
)

AVAILABLE_METHODS = ["keep_first", "keep_last", "merge", "manual_override"]
CONNECTION_ONLY_METHODS = ["merge"]


# -------------------------------------------------------------------
# CACHÉ DE LECTURA DE ARCHIVOS (Invalida automáticamente al modificar archivo)
# -------------------------------------------------------------------
@st.cache_data(show_spinner="Updating corpus...")
def _get_cached_corpus(project_name: str, last_modified: float) -> dict:
    """
    Carga el corpus y lo mantiene en RAM. 
    Se invalida automáticamente si 'last_modified' (mtime) cambia en disco.
    """
    draft_corpus_path = PROJECTS_DIR / project_name / ".draft" / "corpus.json"
    if not draft_corpus_path.exists():
        draft_corpus_path = PROJECTS_DIR / project_name / "corpus.json"

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


def _get_corpus_mtime(project_name: str) -> float:
    """Obtiene la fecha de última modificación del archivo de corpus."""
    draft_path = PROJECTS_DIR / project_name / ".draft" / "corpus.json"
    if not draft_path.exists():
        draft_path = PROJECTS_DIR / project_name / "corpus.json"
    
    return draft_path.stat().st_mtime if draft_path.exists() else 0.0


def render_workspace(project_name: str | None):
    """Renders the main workspace based on the active project."""

    if not project_name:
        st.info("👈 Select a project from the sidebar or click **'➕ New Project'** to get started.")
        return

    projects_info = get_projects_info()
    status = projects_info.get(project_name)

    # -------------------------------------------------------------------
    # CASE 1: COMMITTED
    # -------------------------------------------------------------------
    if status == "committed":
        st.markdown(
            f"""
            <span style="font-size: 45px; font-weight: bold;">{project_name}:</span> 
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

    # -------------------------------------------------------------------
    # CASE 2: IN PROGRESS
    # -------------------------------------------------------------------
    else:
        st.markdown(
            f"""
            <span style="font-size: 45px; font-weight: bold;">{project_name}:</span> 
            <span style="font-size: 30px; color: gray;">🟡 In Progress</span>
            """,
            unsafe_allow_html=True
        )

        clusters = load_project_report(project_name)

        if clusters is None:
            st.warning("No report file was found for this project.")
            return

        if not clusters:
            st.success("🎉 All clusters have been resolved! You are ready to commit.")
            if st.button("✅ Commit Project", type="primary"):
                st.toast("Project committed successfully!", icon="🚀")
            return

        # Cargar corpus desde la CACHÉ rastreando la fecha de modificación
        mtime = _get_corpus_mtime(project_name)
        corpus_lookup = _get_cached_corpus(project_name, mtime)

        total_clusters = len(clusters)
        st.caption(f"Total Pending Components/Clusters: **{total_clusters}**")

        # -------------------------------------------------------------------
        # PAGINACIÓN DE CLUSTERS
        # -------------------------------------------------------------------
        ITEMS_PER_PAGE = 15
        total_pages = (total_clusters + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

        if total_pages > 1:
            p_col1, p_col2 = st.columns([1, 3])
            with p_col1:
                current_page = st.number_input(
                    f"Page (1 - {total_pages})",
                    min_value=1,
                    max_value=total_pages,
                    value=1,
                    step=1,
                    key=f"pagination_{project_name}"
                )
            with p_col2:
                st.write(" ")
                st.write(" ")
                st.caption(
                    f"Showing clusters **{(current_page - 1) * ITEMS_PER_PAGE + 1}** "
                    f"to **{min(current_page * ITEMS_PER_PAGE, total_clusters)}** of **{total_clusters}**"
                )

            start_idx = (current_page - 1) * ITEMS_PER_PAGE
            end_idx = start_idx + ITEMS_PER_PAGE
            visible_clusters = clusters[start_idx:end_idx]
        else:
            start_idx = 0
            visible_clusters = clusters

        st.markdown("---")

        # -------------------------------------------------------------------
        # RENDERIZADO DE COMPONENTES
        # -------------------------------------------------------------------
        for rel_idx, component in enumerate(visible_clusters):
            c_idx = start_idx + rel_idx
            component_id = component.get("component_id", c_idx)
            nodes = component.get("nodes", [])
            edges = component.get("edges_trazability", [])

            MAX_NODES_TO_SHOW = 6
            nodes_str = ", ".join(map(str, nodes[:MAX_NODES_TO_SHOW]))
            if len(nodes) > MAX_NODES_TO_SHOW:
                nodes_str += f" (+{len(nodes) - MAX_NODES_TO_SHOW} more)"

            label = f"📦 **[{nodes_str}]** — ({len(edges)} connections)"

            with st.expander(label, expanded=False):

                # --- COMPONENT-LEVEL ACTIONS ---
                st.markdown("##### Resolve Entire Component")
                c1, c2 = st.columns([3, 1])
                with c1:
                    cluster_methods = [
                        m for m in AVAILABLE_METHODS
                        if m not in CONNECTION_ONLY_METHODS
                    ]
                    selected_cluster_method = st.selectbox(
                        "Deduplication Method",
                        options=cluster_methods,
                        key=f"method_comp_{component_id}_{c_idx}"
                    )
                with c2:
                    st.write(" ")
                    st.write(" ")
                    if st.button(
                        "⚡ Resolve Component",
                        key=f"btn_comp_{component_id}_{c_idx}",
                        type="primary"
                    ):
                        st.toast(
                            f"Resolving Component {component_id} using '{selected_cluster_method}'...",
                            icon="⚙️"
                        )

                st.markdown("---")

                # --- EDGES / CONNECTIONS (BARRA LATERAL + LISTA VISTA DETALLADA) ---
                st.markdown("##### Connections Explorer")

                if not edges:
                    st.info("No connections found for this component.")
                else:
                    col_nav, col_detail = st.columns([1, 3])

                    total_edges = len(edges)
                    MAX_EDGES_PER_PAGE = 10

                    with col_nav:
                        st.markdown("###### Connections")

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

                            # Mensaje explicativo de la paginación interna
                            st.caption(
                                f"Showing connections **{e_start + 1}** to **{e_end}** of **{total_edges}**"
                            )
                        else:
                            e_start = 0
                            current_edges = edges

                        # Opciones para la lista lateral
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

                        st.markdown(f"## `{elem_a}` ↔ `{elem_b}`")

                        # --- SIMILARITY SCORES EN LISTA VERTICAL ---
                        if details:
                            st.markdown("**Scores:**")
                            lines = [f"- **{key_name}**: `{score * 100:.1f}%`" for key_name, score in details.items()]
                            st.markdown("\n".join(lines))

                        st.markdown("---")

                        # --- RECORD DETAILS (A vs B) ---
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.caption(f"Record ID: `{elem_a}`")
                            st.json(data_a, expanded=False)

                        with col_b:
                            st.caption(f"Record ID: `{elem_b}`")
                            st.json(data_b, expanded=False)

                        st.markdown("---")

                        # --- DEDUPLICATION OPTIONS ---
                        st.markdown("###### Resolve Connection")
                        m_col, b_col = st.columns([3, 1])

                        with m_col:
                            conn_method = st.selectbox(
                                "Method",
                                options=AVAILABLE_METHODS,
                                key=f"method_edge_{component_id}_{c_idx}_{e_idx}"
                            )

                        with b_col:
                            st.write(" ")
                            st.write(" ")
                            if st.button(
                                "Resolve Connection",
                                key=f"btn_edge_{component_id}_{c_idx}_{e_idx}"
                            ):
                                st.toast(
                                    f"Resolved connection {elem_a} <-> {elem_b} using '{conn_method}'.",
                                    icon="✅"
                                )