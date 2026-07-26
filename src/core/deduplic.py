import json
import shutil
from pathlib import Path
from core.methods import apply_method
from core.draft_io import load_draft, save_draft
from core.merge_manager import create_pending_merge, has_pending_merges, forget_merges


def _process_edge(
    corpus: dict, 
    report: list, 
    cluster_idx: int, 
    edge_idx: int,
    method: str="keep_all",
    project_path: str=None
) -> tuple[dict, list]:
    """
    Valida límites y aplica el método a una conexión específica directamente en RAM.
    No realiza I/O de archivos (ideal para bucles masivos).
    """
    # 1. Validar que el cluster_idx exista en el reporte
    if not (0 <= cluster_idx < len(report)):
        raise IndexError(
            f"Cluster index {cluster_idx} is out of bounds. "
            f"The report contains {len(report)} clusters (valid range: 0 to {len(report) - 1})."
        )

    cluster = report[cluster_idx]
    edges = cluster.get("edges_trazability", [])

    # 2. Validar que el edge_idx exista dentro de edges_trazability
    if not (0 <= edge_idx < len(edges)):
        raise IndexError(
            f"Edge index {edge_idx} is out of bounds for cluster {cluster_idx}. "
            f"The cluster contains {len(edges)} connections (valid range: 0 to {len(edges) - 1})."
        )

    # 3. Extraer la conexión objetivo
    target_edge = edges[edge_idx]

    # 4. Delegar la resolución al registro de métodos en RAM
    target_info = {
        "project_path": project_path,
        "cluster_idx": cluster_idx,
        "edge_idx": edge_idx,
        "edge": target_edge
    }
    
    return apply_method(method, corpus, report, target_info)


def _process_cluster(
    corpus: dict, 
    report: list, 
    cluster_idx: int, 
    method: str = "keep_all"
) -> tuple[dict, list]:

    if not (0 <= cluster_idx < len(report)):
        raise IndexError(
            f"Cluster index {cluster_idx} is out of bounds. "
            f"The report contains {len(report)} clusters."
        )

    cluster = report[cluster_idx]
    
    while cluster.get("edges_trazability"):
        corpus, report = _process_edge(corpus, report, cluster_idx, 0, method)
        cluster = report[cluster_idx]
    
    return corpus, report



def deduplic_connection(project_path: Path, cluster_idx: int, edge_idx: int, method: str = "keep_all"):
    if method == "merge":
        create_pending_merge(project_path, cluster_idx, edge_idx)
        return
    corpus, report = load_draft(project_path)
    
    try:
        corpus, report = _process_edge(corpus, report, cluster_idx, edge_idx, method, project_path)
    except Exception as e:
        print(f"Error: {e}")
    
    save_draft(project_path, corpus, report)



def deduplic_cluster(project_path: Path, cluster_idx: int, method: str = "keep_all"):
    if method == "merge":
        _, report = load_draft(project_path)
        cluster = report[cluster_idx]
        edges = cluster.get("edges_trazability", [])
        for edge_idx in range(len(edges)):
            create_pending_merge(project_path, cluster_idx, edge_idx)
        return

    corpus, report = load_draft(project_path)
    try:
        corpus, report = _process_cluster(corpus, report, cluster_idx, method)
    except Exception as e:
        print(f"Error: {e}")
        return
    save_draft(project_path, corpus, report)

def deduplic_cluster_by_comp_id(project_path: Path, id_to_find: int, method: str = "keep_all"):
    _, report = load_draft(project_path)
    
    for cluster_idx, cluster in enumerate(report):
        if cluster.get("component_id") == id_to_find:
            deduplic_cluster(project_path, cluster_idx, method)


def deduplic_all(project_path: Path, method: str = "keep_all"):
    if method == "merge":
        _, report = load_draft(project_path)
        for cluster_idx in range(len(report)):
            edges = report[cluster_idx].get("edges_trazability", [])
            for edge_idx in range(len(edges)):
                create_pending_merge(project_path, cluster_idx, edge_idx)
        return

    corpus, report = load_draft(project_path)
    try:
        for cluster_idx in range(len(report)):
            corpus, report = _process_cluster(corpus, report, cluster_idx, method)
    except Exception as e:
        print(f"Error: {e}")
        return
    save_draft(project_path, corpus, report)



def get_state(project_path: Path) -> Path:
    """
    Generates a consolidated 'dedup_corpus.json' file in the project root.
    Removes deprecated records, strips internal metadata, and reindexes the keys.
    """
    corpus_draft, _ = load_draft(project_path)

    # 1. Keep only active records
    active_items = [
        (old_key, rec) for old_key, rec in corpus_draft.items()
        if rec.get("_status") != "deprecated"
    ]

    # 2. Build the exportable corpus with reindexed keys and no temporary metadata
    clean_corpus = {}
    for new_idx, (_, record) in enumerate(active_items):
        clean_record = record.copy()
        clean_record.pop("_status", None)
        clean_record.pop("_merged_from", None)
        clean_record.pop("_merged_to", None)
        clean_corpus[str(new_idx)] = clean_record

    # 3. Save the final output in the project root
    output_file = project_path / "dedup_corpus.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(clean_corpus, f, indent=4, ensure_ascii=False)

    print(f"-> snapshot successfully generated: '{output_file.name}'")
    return output_file


def commit(project_path: Path) -> None:
    """
    Commits the changes from .draft/ to the project root.
    The operation is blocked if there are pending merge drafts in merges/.
    """
    # VALIDATION GATE: Prevent commit if there are pending merge drafts
    if has_pending_merges(project_path):
        raise RuntimeError(
            "Commit cannot be performed: there are pending merge drafts in the 'merges/' directory. "
            "Resolve them by running 'deduplic_execute_merge' or discard them with 'forget_merges'."
        )

    get_state(project_path)


    root_report_file = project_path / "report.json"
    if root_report_file.exists():
        root_report_file.unlink()

    root_original_corp_file = project_path / "corpus.json"
    if root_original_corp_file.exists():
        root_original_corp_file.unlink()

    draft_dir = project_path / ".draft"
    if not draft_dir.exists():
        raise FileNotFoundError(
            f"No draft (.draft) found to commit in {project_path}."
        )
    shutil.rmtree(draft_dir)

    metadata_file = project_path / "metadata.json"
    if metadata_file.exists():
        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        
        metadata["status"] = "committed"
        
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4, ensure_ascii=False)

    print(f"-> Changes successfully committed to {project_path.name}.")




def restore(project_path: Path) -> None:
    """
    Restaura el proyecto a su estado original.
    Copia corpus.json y report.json desde .original/ hacia la raíz del proyecto 
    y hacia la carpeta .draft/.
    """
    original_dir = project_path / "original"
    draft_dir = project_path / ".draft"

    # 1. Validar que la carpeta .original exista
    if not original_dir.exists():
        raise FileNotFoundError(
            f"Cannot restore: '.original/' directory not found in '{project_path}'."
        )

    # 2. Asegurar que la carpeta .draft/ exista
    draft_dir.mkdir(parents=True, exist_ok=True)

    # 3. Sobrescribir la raíz del proyecto (Current State) desde .original/
    shutil.copy2(original_dir / "corpus.json", project_path / "corpus.json")
    shutil.copy2(original_dir / "report.json", project_path / "report.json")

    # 4. Sobrescribir la carpeta .draft/ desde .original/
    shutil.copy2(original_dir / "corpus.json", draft_dir / "corpus.json")
    shutil.copy2(original_dir / "report.json", draft_dir / "report.json")

    dedup_file = project_path / "dedup_corpus.json"
    if dedup_file.exists():
        dedup_file.unlink()

    forget_merges(project_path, True)

    print(f"-> Restore successful for '{project_path.name}'. Reverted to original state.")
