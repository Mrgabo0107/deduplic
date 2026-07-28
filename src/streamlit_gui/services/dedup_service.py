import json
from pathlib import Path
import streamlit as st

from streamlit_gui.utils.project_loader import PROJECTS_DIR
from core.deduplic import (
    deduplic_connection,
    deduplic_cluster,
    deduplic_all,
    commit,
    restore,
)
from core.merge_manager import (
    has_pending_merges,
    forget_merges,
    execute_merge,
    refresh_cluster_merges,
    forget_single_merge,
    list_pending_merges,
)


def _get_draft_paths(project_name: str) -> tuple[Path, Path]:
    """Retorna las rutas a los archivos dentro de la carpeta .draft/"""
    draft_dir = PROJECTS_DIR / project_name / ".draft"
    draft_dir.mkdir(parents=True, exist_ok=True)
    
    corpus_path = draft_dir / "corpus.json"
    report_path = draft_dir / "report.json"

    if not corpus_path.exists():
        orig = PROJECTS_DIR / project_name / "corpus.json"
        if orig.exists():
            corpus_path.write_bytes(orig.read_bytes())
            
    if not report_path.exists():
        orig = PROJECTS_DIR / project_name / "report.json"
        if orig.exists():
            report_path.write_bytes(orig.read_bytes())

    return corpus_path, report_path


def resolve_edge_action(project_name: str, component_id: int | str, edge_idx: int, method_name: str):
    _get_draft_paths(project_name)
    project_path = PROJECTS_DIR / project_name

    _, report_path = _get_draft_paths(project_name)
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    real_cluster_idx = next(
        (i for i, c in enumerate(report) if c.get("component_id") == component_id or c.get("id") == component_id),
        None
    )

    if real_cluster_idx is None:
        raise ValueError(f"No se encontró el cluster con component_id '{component_id}' en report.json")
    
    deduplic_connection(project_path, real_cluster_idx, edge_idx, method_name)

    # ✅ Si el método es 'merge', disparamos la apertura automática del modal
    if method_name == "merge":
        st.session_state["open_merge_dialog"] = True


def resolve_cluster_action(project_name: str, component_id: int | str, method_name: str):
    _get_draft_paths(project_name)
    project_path = PROJECTS_DIR / project_name

    _, report_path = _get_draft_paths(project_name)
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    real_cluster_idx = next(
        (i for i, c in enumerate(report) if c.get("component_id") == component_id or c.get("id") == component_id),
        None
    )

    if real_cluster_idx is None:
        raise ValueError(f"No se encontró el cluster con component_id '{component_id}' en report.json")

    deduplic_cluster(project_path, real_cluster_idx, method_name)

    # ✅ Si el método es 'merge', disparamos la apertura automática del modal
    if method_name == "merge":
        st.session_state["open_merge_dialog"] = True


def resolve_all_action(project_name: str, method_name: str):
    _get_draft_paths(project_name)
    project_path = PROJECTS_DIR / project_name
    deduplic_all(project_path, method_name)


# --- NUEVAS ACCIONES DE PROYECTO ---

def check_pending_merges_service(project_name: str) -> bool:
    """Verifica si existen borrones de merge sin resolver."""
    project_path = PROJECTS_DIR / project_name
    return has_pending_merges(project_path)


def commit_project_action(project_name: str, remaining_clusters_count: int):
    """
    Ejecuta el commit del proyecto. Si existen clusters activos pendientes,
    aplica 'keep_all' masivo antes de consolidar el cambio.
    """
    project_path = PROJECTS_DIR / project_name

    # 1. Bloqueo de seguridad: No se puede hacer commit si hay merges en curso
    if has_pending_merges(project_path):
        raise RuntimeError("There are unresolved pending merges. Please resolve or forget them before committing.")

    # 2. Si quedan clusters sin resolver, aplicamos 'keep_all' por defecto
    if remaining_clusters_count > 0:
        deduplic_all(project_path, method="keep_all")

    # 3. Consolidación de borrador a producción
    commit(project_path)


def restore_project_action(project_name: str):
    """Restaura el proyecto a su estado original descartando el borrador actual."""
    project_path = PROJECTS_DIR / project_name
    restore(project_path)


# --- SERVICIOS DE MERGE MANAGER ---



def execute_single_merge_service(project_name: str, node_a_id: int, node_b_id: int, component_id: int | str):
    """
    Aplica el merge entre node_a y node_b y luego auto-limpia 
    los borradores obsoletos de ese mismo cluster.
    """
    project_path = PROJECTS_DIR /project_name 
    
    # 1. Ejecutar la fusión con el component_id calculado
    result = execute_merge(project_path, node_a_id, node_b_id, component_id)
    # 2. Refrescar la carpeta merges/ en la raíz para ese cluster
    refresh_cluster_merges(project_path, component_id)
    
    return result




def execute_all_merges_service(project_name: str, strategy: str = "Keep Most Complete") -> bool:
    """
    Procesa iterativamente todos los merges pendientes en lote aplicando
    las fusiones guardadas en cada borrador.
    """
    pending = get_pending_merges_service(project_name)
    for merge_item in pending:
        filename = merge_item.get("_file_name")
        node_a_id = merge_item.get("node_a_id")
        node_b_id = merge_item.get("node_b_id")
        component_id = merge_item.get("component_id", "cluster")

        execute_single_merge_service(
            project_name=project_name,
            node_a_id=node_a_id,
            node_b_id=node_b_id,
            component_id=component_id
        )
    return True


def forget_single_merge_service(project_name: str, filename: str):
    """Elimina únicamente el borrador especificado de la carpeta merges/"""
    project_path = PROJECTS_DIR / project_name
    return forget_single_merge(project_path, filename)


def get_pending_merges_service(project_name: str) -> list[dict]:
    """Retorna la lista de merges pendientes actualizados con su estado actual."""
    project_path = PROJECTS_DIR / project_name
    return list_pending_merges(project_path)


def forget_all_merges_service(project_name: str):
    """Elimina la carpeta completa de merges/ del proyecto."""
    project_path = PROJECTS_DIR / project_name
    forget_merges(project_path, confirm=True)

