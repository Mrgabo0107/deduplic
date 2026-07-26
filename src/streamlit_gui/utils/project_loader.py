import json
from pathlib import Path

# Localizar la carpeta projects/
PROJECTS_DIR = Path(__file__).resolve().parents[3] / "projects"


def get_projects_info() -> dict:
    """Escanea la carpeta projects/ y lee la metadata de cada proyecto."""
    projects = {}
    if PROJECTS_DIR.exists():
        for p in PROJECTS_DIR.iterdir():
            if p.is_dir():
                meta_file = p / "metadata.json"
                if meta_file.exists():
                    try:
                        with open(meta_file, "r", encoding="utf-8") as f:
                            meta = json.load(f)
                            projects[p.name] = meta.get("status", "unknown")
                    except Exception:
                        projects[p.name] = "error"
                else:
                    projects[p.name] = "no_metadata"
    return projects


def load_project_report(project_name: str) -> dict | None:
    """Carga el report.json (priorizando .draft/report.json)."""
    project_path = PROJECTS_DIR / project_name
    draft_report = project_path / ".draft" / "report.json"
    root_report = project_path / "report.json"

    report_file = draft_report if draft_report.exists() else root_report

    if report_file.exists():
        with open(report_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def load_dedup_corpus(project_name: str) -> dict | None:
    """Carga el dedup_corpus.json de un proyecto en estado committed."""
    dedup_file = PROJECTS_DIR / project_name / "dedup_corpus.json"
    if dedup_file.exists():
        with open(dedup_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return None