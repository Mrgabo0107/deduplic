from .utils import (
    get_next_corpus_id,
    load_threshold_from_project,
    clean_record,
    deprecate_source_records,
    collect_neighbors_and_untouched_edges,
    recompute_edges_for_synthetic_node,
    update_cluster_structure
)


def _build_synthetic_record_last(rec_b: dict, node_a_id: int, node_b_id: int) -> dict:
    """Creates synthetic record C as an exact copy of the LAST record (B)."""
    synthetic_record = clean_record(rec_b)
    synthetic_record["_status"] = "active"
    synthetic_record["_merged_from"] = [int(node_a_id), int(node_b_id)]
    return synthetic_record


def keep_last(
    corpus: dict,
    report: list,
    target_info: dict,
) -> tuple[dict, list]:
    """Applies the Keep-Last deduplication strategy on a specific cluster edge."""
    cluster_idx = target_info["cluster_idx"]
    edge_idx = target_info["edge_idx"]
    threshold = load_threshold_from_project(target_info.get("project_path"))

    cluster = report[cluster_idx]
    edges = cluster.get("edges_trazability", [])

    if not (0 <= edge_idx < len(edges)):
        return corpus, report

    target_edge = edges[edge_idx]
    pair = target_edge.get("pair", [])
    if len(pair) < 2:
        return corpus, report
    if pair[0] == pair[1]:
        return corpus, report

    node_a_id, node_b_id = pair[0], pair[1]
    str_a, str_b = str(node_a_id), str(node_b_id)

    rec_a = corpus.get(str_a, {})
    rec_b = corpus.get(str_b, {})

    details = target_edge.get("details", {})
    keys_for_similarity = list(details.keys()) if details else [
        k for k in rec_a.keys() if not k.startswith("_")
    ]

    # 1. Crear el registro sintético C copiando el ÚLTIMO registro (rec_b)
    synthetic_record = _build_synthetic_record_last(rec_b, node_a_id, node_b_id)
    str_c = get_next_corpus_id(corpus)
    int_c = int(str_c)
    corpus[str_c] = synthetic_record

    # 2. Marcar A y B como 'deprecated'
    deprecate_source_records(corpus, str_a, str_b, str_c)

    # 3. Recolectar vecinos y re-evaluar con do_reports
    neighbor_ids, untouched_edges = collect_neighbors_and_untouched_edges(edges, node_a_id, node_b_id)
    new_edges_for_c = recompute_edges_for_synthetic_node(
        corpus, synthetic_record, int_c, neighbor_ids, keys_for_similarity, threshold
    )

    # 4. Actualizar cluster
    update_cluster_structure(cluster, untouched_edges + new_edges_for_c)
    # from core.merge_manager import refresh_cluster_merges
    # component_id = cluster.get("component_id")
    # project_path = target_info.get("project_path")
    # refresh_cluster_merges(project_path, component_id)

    return corpus, report