import streamlit as st
from streamlit_gui.components.sidebar import render_sidebar
from streamlit_gui.components.workspace import render_workspace

st.set_page_config(
    page_title="Deduplic",
    page_icon="🖇️",
    layout="wide"
)

# 1. Render the sidebar and retrieve the active project
selected_project = render_sidebar()

# 2. Render the main workspace
render_workspace(selected_project)