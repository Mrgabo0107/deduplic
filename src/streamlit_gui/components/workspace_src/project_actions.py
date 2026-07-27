import streamlit as st
from src.streamlit_gui.components.workspace_src.corpus_loader import AVAILABLE_METHODS, EXCLUDED_METHODS


def render_project_global_actions(project_name: str, total_clusters: int):
    """Renderiza el panel de resolución global (Deduplicate All) al final de la página."""
    st.markdown("---")
    
    with st.container(border=True):
        # st.caption(
        #     "Apply a single deduplication strategy to **all remaining pending clusters** across the project."
        # )
        st.markdown("##### Resolve corpus by method:")
        
        # Filtra 'merge' para la desduplicación global
        project_methods = [
            m for m in AVAILABLE_METHODS 
            if m not in EXCLUDED_METHODS
        ]

        col_m, col_b = st.columns([3, 1])
        with col_m:
            selected_global_method = st.selectbox(
                "Global Strategy Method",
                options=project_methods,
                key=f"global_dedup_method_{project_name}",
                label_visibility="collapsed"
            )
        with col_b:
            if st.button(
                "Resolve",
                key=f"btn_global_dedup_{project_name}",
                type="primary",
            ):
                st.toast(
                    f"Processing all {total_clusters} clusters using '{selected_global_method}'..."
                )