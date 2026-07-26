import streamlit as st
from streamlit_gui.components.sidebar import render_sidebar
from streamlit_gui.components.workspace import render_workspace

st.set_page_config(
    page_icon="🖇️",
    layout="wide"
)

# 1. Renderizar Sidebar
selected_project, status = render_sidebar()

# 2. Renderizar Workspace principal
render_workspace(selected_project, status)