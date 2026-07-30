# import json
# from pathlib import Path
# import streamlit as st
# import shutil
# from deduplic.cli_cmds.cmd_deduplic_init import deduplic_init, init_workspace

# PROJECTS_DIR = Path(__file__).resolve().parents[3] / "projects"


# def delete_project_directory(project_name: str) -> bool:
#     """Elimina completamente la carpeta del proyecto del disco."""
#     if not project_name:
#         return False
#     project_path = PROJECTS_DIR / project_name
#     if project_path.exists() and project_path.is_dir():
#         shutil.rmtree(project_path)
#         return True
#     return False


# def get_projects_info() -> dict:
#     """Scans the projects/ directory and reads the metadata for each project."""
#     projects = {}
#     if PROJECTS_DIR.exists():
#         for p in PROJECTS_DIR.iterdir():
#             if p.is_dir():
#                 meta_file = p / "metadata.json"
#                 if meta_file.exists():
#                     try:
#                         with open(meta_file, "r", encoding="utf-8") as f:
#                             metadata = json.load(f)
#                             projects[p.name] = metadata.get("status", "unknown")
#                     except Exception:
#                         projects[p.name] = "error"
#                 else:
#                     projects[p.name] = "no_metadata"
#     return projects


# def load_project_report(project_name: str, force_reload: bool = False) -> dict | None:
#     """Loads report.json into session_state for instant navigation."""
#     key = f"report_data_{project_name}"
    
#     if force_reload or key not in st.session_state:
#         project_path = PROJECTS_DIR / project_name
#         draft_report = project_path / ".draft" / "report.json"
#         root_report = project_path / "report.json"

#         report_file = draft_report if draft_report.exists() else root_report

#         if report_file.exists():
#             with open(report_file, "r", encoding="utf-8") as f:
#                 st.session_state[key] = json.load(f)
#         else:
#             st.session_state[key] = None

#     return st.session_state[key]


# @st.cache_data(show_spinner="Loading deduplicated corpus...")
# def load_dedup_corpus(project_name: str) -> list[dict] | None:
#     """Carga dedup_corpus.json de un proyecto committed de forma optimizada en memoria."""
#     dedup_file = PROJECTS_DIR / project_name / "dedup_corpus.json"
#     if dedup_file.exists():
#         with open(dedup_file, "r", encoding="utf-8") as f:
#             data = json.load(f)
            
#             # Normalizamos si viene como dict o list
#             if isinstance(data, dict):
#                 return [{"id": k, **(v if isinstance(v, dict) else {"value": v})} for k, v in data.items()]
#             elif isinstance(data, list):
#                 return data
#     return None


# def create_new_project_from_upload(uploaded_file, selected_keys: list, threshold: float) -> tuple[Path | None, str]:
#     """Processes the uploaded file and creates a new project using deduplic_init and init_workspace."""
#     raw_data = json.load(uploaded_file)
#     base_name = Path(uploaded_file.name).stem

#     created_path = deduplic_init(
#         raw_input=raw_data,
#         keys=selected_keys,
#         name=base_name,
#         threshold=threshold
#     )

#     if created_path is None:
#         return None, base_name

#     init_workspace(created_path)
#     return created_path, base_name

#----------------------------------
import json
from pathlib import Path
import streamlit as st


from deduplic.config import settings
from deduplic.core.deduplic import (
    deduplic_delete_project,
    deduplic_get_projects_info as core_deduplic_get_projects_info,
    deduplic_init,
)

PROJECTS_DIR = settings.projects_dir


def delete_project_directory(project_name: str) -> bool:
    """Delegates project deletion to the core library."""
    if not project_name:
        return False
    project_path = PROJECTS_DIR / project_name
    return deduplic_delete_project(project_path)




def deduplic_get_projects_info() -> dict:
    """Delegates project scanning to the core library."""
    return core_deduplic_get_projects_info(PROJECTS_DIR)


def create_new_project_from_upload(
    uploaded_file, selected_keys: list, threshold: float
) -> tuple[Path | None, str]:
    """Processes the uploaded file and creates a new project using deduplic_init."""
    raw_data = json.load(uploaded_file)
    base_name = Path(uploaded_file.name).stem

    created_path = deduplic_init(
        raw_input=raw_data,
        keys=selected_keys,
        name=base_name,
        threshold=threshold,
        projects_dir=PROJECTS_DIR,
    )

    if created_path is None:
        return None, base_name

    # Ya no se requiere init_workspace() porque deduplic_init lo hace internamente
    return created_path, base_name


def load_project_report(project_name: str, force_reload: bool = False) -> dict | None:
    """Loads report.json into session_state for instant navigation."""
    key = f"report_data_{project_name}"
    
    if force_reload or key not in st.session_state:
        project_path = PROJECTS_DIR / project_name
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
def load_dedup_corpus(project_name: str) -> list[dict] | None:
    """Loads dedup_corpus.json for a committed project."""
    dedup_file = PROJECTS_DIR / project_name / "dedup_corpus.json"
    if dedup_file.exists():
        with open(dedup_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return [{"id": k, **(v if isinstance(v, dict) else {"value": v})} for k, v in data.items()]
            elif isinstance(data, list):
                return data
    return None

