import json
import streamlit as st
from streamlit_gui.utils.project_loader import PROJECTS_DIR

# Métodos generales de deduplicación
AVAILABLE_METHODS = ["keep_all",
                     "keep_first",
                     "keep_last",
                     "keep_largest",
                     "keep_shortest",
                     "keep_newest",
                     "keep_oldest",
                     "merge"
                     ]

EXCLUDED_METHODS = ["merge"]

@st.cache_data(show_spinner="Updating corpus...")
def get_cached_corpus(project_name: str, last_modified: float) -> dict:
    """Carga el corpus y lo mantiene en RAM con caché condicional al mtime."""
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


def get_corpus_mtime(project_name: str) -> float:
    """Obtiene la fecha de última modificación del archivo de corpus."""
    draft_path = PROJECTS_DIR / project_name / ".draft" / "corpus.json"
    if not draft_path.exists():
        draft_path = PROJECTS_DIR / project_name / "corpus.json"
    
    return draft_path.stat().st_mtime if draft_path.exists() else 0.0