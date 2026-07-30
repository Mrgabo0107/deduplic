from .utils import (
    collect_neighbors_and_untouched_edges,
    deprecate_source_records,
    get_next_corpus_id,
    load_threshold_from_project,
    recompute_edges_for_synthetic_node,
    update_cluster_structure,
)


def _build_synthetic_record_largest(
    rec_a: dict,
    rec_b: dict,
    node_a_id: int,
    node_b_id: int,
) -> dict:
    """Creates synthetic record C selecting the longest text representation for each key."""
    synthetic_record = {}
    all_keys = set(rec_a.keys()) | set(rec_b.keys())
    clean_keys = {k for k in all_keys if not k.startswith("_")}

    for key in clean_keys:
        val_a = rec_a.get(key)
        val_b = rec_b.get(key)

        str_a = str(val_a) if val_a is not None else ""
        str_b = str(val_b) if val_b is not None else ""

        synthetic_record[key] = val_a if len(str_a) >= len(str_b) else val_b

    synthetic_record["_status"] = "active"
    synthetic_record["_merged_from"] = [int(node_a_id), int(node_b_id)]
    return synthetic_record


def keep_largest(
    corpus: dict,
    report: list,
    target_info: dict,
) -> tuple[dict, list]:
    """Applies Keep-Largest deduplication strategy on a specific cluster edge."""
    cluster_idx = target_info["cluster_idx"]
    edge_idx = target_info["edge_idx"]
    threshold = load_threshold_from_project(target_info.get("project_path"))

    cluster = report[cluster_idx]
    edges = cluster.get("edges_trazability", [])

    if not (0 <= edge_idx < len(edges)):
        return corpus, report

    target_edge = edges[edge_idx]
    pair = target_edge.get("pair", [])
    if len(pair) < 2 or pair[0] == pair[1]:
        return corpus, report

    node_a_id, node_b_id = pair[0], pair[1]
    str_a, str_b = str(node_a_id), str(node_b_id)

    rec_a = corpus.get(str_a, {})
    rec_b = corpus.get(str_b, {})

    details = target_edge.get("details", {})
    keys_for_similarity = (
        list(details.keys())
        if details
        else [k for k in rec_a.keys() if not k.startswith("_")]
    )

    synthetic_record = _build_synthetic_record_largest(rec_a, rec_b, node_a_id, node_b_id)
    str_c = get_next_corpus_id(corpus)
    int_c = int(str_c)
    corpus[str_c] = synthetic_record

    deprecate_source_records(corpus, str_a, str_b, str_c)

    neighbor_ids, untouched_edges = collect_neighbors_and_untouched_edges(
        edges, node_a_id, node_b_id
    )
    new_edges_for_c = recompute_edges_for_synthetic_node(
        corpus, synthetic_record, int_c, neighbor_ids, keys_for_similarity, threshold
    )

    update_cluster_structure(cluster, untouched_edges + new_edges_for_c)
    return corpus, report