"""Components package for Deduplic Streamlit GUI.

Location: src/deduplic/streamlit_gui/components/__init__.py
"""

from .sidebar import render_sidebar
from .workspace import render_workspace
from .cluster_view import (
    render_component_item,
    get_cached_corpus,
    get_corpus_mtime,
)
from .merge_view import render_merge_modal
from .global_actions import render_project_global_actions

__all__ = [
    "render_sidebar",
    "render_workspace",
    "render_component_item",
    "get_cached_corpus",
    "get_corpus_mtime",
    "render_merge_modal",
    "render_project_global_actions",
]