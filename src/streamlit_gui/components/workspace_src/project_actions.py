import streamlit as st
from src.streamlit_gui.components.workspace_src.corpus_loader import AVAILABLE_METHODS, EXCLUDED_METHODS
from src.streamlit_gui.services.dedup_service import resolve_all_action


def _on_resolve_all(project_name: str, method_key: str):
    """Callback para ejecutar deduplic_all en todo el proyecto."""
    method = st.session_state.get(method_key)
    print(f"--> [DEBUG Callback] Resolviendo TODO el proyecto '{project_name}' con método '{method}'")
    
    resolve_all_action(project_name=project_name, method_name=method)
    st.toast("All pending clusters resolved successfully!", icon="🚀")


def render_project_global_actions(project_name: str, total_clusters: int):
    """Renderiza el panel de resolución global (Deduplicate All) al final de la página."""
    st.markdown("---")
    
    with st.container(border=True):
        st.markdown("##### Resolve corpus by method:")
        
        project_methods = [
            m for m in AVAILABLE_METHODS 
            if m not in EXCLUDED_METHODS
        ]

        global_method_key = f"global_dedup_method_{project_name}"

        col_m, col_b = st.columns([3, 1])
        with col_m:
            st.selectbox(
                "Global Strategy Method",
                options=project_methods,
                key=global_method_key,
                label_visibility="collapsed"
            )
            
        with col_b:
            # ✅ Callback para ejecutar deduplic_all sin perder estado
            st.button(
                "Resolve",
                key=f"btn_global_dedup_{project_name}",
                type="primary",
                on_click=_on_resolve_all,
                args=(project_name, global_method_key)
            )