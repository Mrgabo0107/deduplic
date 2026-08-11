"""Project Management Service for Deduplic Streamlit GUI.

Consolidates workspace scanning, project creation from JSON uploads, 
deletion, and project report/corpus reading operations.
"""

import json
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
import streamlit as st

from deduplic.config import settings
from deduplic.core.deduplic import (
    deduplic_delete_project,
    deduplic_get_projects_info as core_deduplic_get_projects_info,
    deduplic_init,
)


def get_workspace_dir() -> Path:
    """Returns the current active projects workspace directory."""
    return settings.projects_dir


def delete_project_directory(project_name: str) -> bool:
    """Delegates project directory deletion to the core library."""
    if not project_name:
        return False
    project_path = get_workspace_dir() / project_name
    return deduplic_delete_project(project_path, True)


def deduplic_get_projects_info() -> Dict[str, str]:
    """Delegates project scanning to the core library."""
    return core_deduplic_get_projects_info(get_workspace_dir())


def create_new_project_from_upload(
    uploaded_file: Any, selected_keys: List[str], threshold: float
) -> Tuple[Optional[Path], str]:
    """Processes the uploaded file and creates a new project using deduplic_init."""
    raw_data = json.load(uploaded_file)
    base_name = Path(uploaded_file.name).stem

    created_path = deduplic_init(
        raw_input=raw_data,
        keys=selected_keys,
        name=base_name,
        threshold=threshold,
        projects_dir=get_workspace_dir(),
    )

    if created_path is None:
        return None, base_name

    return created_path, base_name


def load_project_report(project_name: str, force_reload: bool = False) -> Optional[List[Dict[str, Any]]]:
    """Loads report.json into session_state for instant navigation."""
    key = f"report_data_{project_name}"
    
    if force_reload or key not in st.session_state:
        project_path = get_workspace_dir() / project_name
        draft_report = project_path / ".draft" / "report.json"
        root_report = project_path / "report.json"

        report_file = draft_report if draft_report.exists() else root_report

        if report_file.exists():
            with open(report_file, "r", encoding="utf-8") as f:
                st.session_state[key] = json.load(f)
        else:
            st.session_state[key] = None

    return st.session_state[key]


@st.cache_data(show_spinner="Loading deduplicated corpus...")
def load_dedup_corpus(project_name: str) -> Optional[List[Dict[str, Any]]]:
    """Loads dedup_corpus.json for a committed project."""
    dedup_file = get_workspace_dir() / project_name / "dedup_corpus.json"
    if dedup_file.exists():
        with open(dedup_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return [{"id": k, **(v if isinstance(v, dict) else {"value": v})} for k, v in data.items()]
            elif isinstance(data, list):
                return data
    return None