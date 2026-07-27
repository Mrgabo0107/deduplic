import json
from pathlib import Path
from src.streamlit_gui.utils.project_loader import PROJECTS_DIR
from src.core.deduplic import deduplic_connection, deduplic_cluster, deduplic_all


def _get_draft_paths(project_name: str) -> tuple[Path, Path]:
    """Retorna las rutas a los archivos dentro de la carpeta .draft/"""
    draft_dir = PROJECTS_DIR / project_name / ".draft"
    draft_dir.mkdir(parents=True, exist_ok=True)

    corpus_path = draft_dir / "corpus.json"
    report_path = draft_dir / "report.json"

    # Si no existen en .draft aún, los inicializamos copiando los originales
    if not corpus_path.exists():
        orig = PROJECTS_DIR / project_name / "corpus.json"
        if orig.exists():
            corpus_path.write_bytes(orig.read_bytes())

    if not report_path.exists():
        orig = PROJECTS_DIR / project_name / "report.json"
        if orig.exists():
            report_path.write_bytes(orig.read_bytes())

    return corpus_path, report_path


def resolve_edge_action(
    project_name: str, component_id: int | str, edge_idx: int, method_name: str
):
    """Aplica una estrategia sobre UNA conexión específica dentro de un cluster."""
    _get_draft_paths(project_name)
    project_path = PROJECTS_DIR / project_name

    corpus_path, report_path = _get_draft_paths(project_name)
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    # Buscamos el índice real dentro del archivo JSON sin filtrar
    real_cluster_idx = next(
        (
            i
            for i, c in enumerate(report)
            if c.get("component_id") == component_id
            or c.get("id") == component_id
        ),
        None,
    )

    if real_cluster_idx is None:
        raise ValueError(
            f"No se encontró el cluster con component_id '{component_id}' en report.json"
        )

    deduplic_connection(project_path, real_cluster_idx, edge_idx, method_name)


def resolve_cluster_action(
    project_name: str, component_id: int | str, method_name: str
):
    """Aplica una estrategia sobre TODO un cluster."""
    _get_draft_paths(project_name)
    project_path = PROJECTS_DIR / project_name

    corpus_path, report_path = _get_draft_paths(project_name)
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    # Buscamos el índice real dentro del archivo JSON sin filtrar a partir del component_id
    real_cluster_idx = next(
        (
            i
            for i, c in enumerate(report)
            if c.get("component_id") == component_id
            or c.get("id") == component_id
        ),
        None,
    )

    if real_cluster_idx is None:
        raise ValueError(
            f"No se encontró el cluster con component_id '{component_id}' en report.json"
        )

    # Ejecutamos la deduplicación del cluster completo
    deduplic_cluster(project_path, real_cluster_idx, method_name)

    # src/streamlit_gui/services/dedup_service.py


def resolve_all_action(project_name: str, method_name: str):
    """Aplica una estrategia de deduplicación masiva sobre TODO el proyecto."""
    _get_draft_paths(project_name)
    project_path = PROJECTS_DIR / project_name

    deduplic_all(project_path, method_name)