from .utils import (
    load_threshold_from_project,
    get_next_corpus_id,
    deprecate_source_records,
    collect_neighbors_and_untouched_edges,
    recompute_edges_for_synthetic_node,
    update_cluster_structure,
    resolve_active_node,
    load_comparison_keys_from_project
)


def build_merge_preview(corpus: dict, report: list, cluster_idx: int, edge_idx: int) -> dict:
    """
    Builds the preview (draft) structure for a merge.
    Automatically traces whether the edge's nodes have already been merged into other nodes.
    """
    cluster = report[cluster_idx]
    edges = cluster.get("edges_trazability", [])

    if not (0 <= edge_idx < len(edges)):
        raise IndexError(f"Edge index {edge_idx} out of range for cluster {cluster_idx}.")

    target_edge = edges[edge_idx]
    pair = target_edge.get("pair", [])
    if len(pair) < 2:
        raise ValueError(f"Invalid edge pair at index {edge_idx}.")

    # 1. RESOLVE THE CURRENT ACTIVE NODES IN THE CORPUS
    raw_a_id, raw_b_id = pair[0], pair[1]
    active_a_id = int(resolve_active_node(corpus, raw_a_id))
    active_b_id = int(resolve_active_node(corpus, raw_b_id))

    # If both nodes resolve to the same active node (self-merge), return an invalid preview
    if active_a_id == active_b_id:
        return {}

    # 2. RETRIEVE THE CURRENT RECORDS OF THE ACTIVE NODES
    rec_a = corpus.get(str(active_a_id), {})
    rec_b = corpus.get(str(active_b_id), {})

    # Get the union of all non-internal keys
    all_keys = set(rec_a.keys()) | set(rec_b.keys())
    clean_keys = sorted([k for k in all_keys if not k.startswith("_")])

    fields = {}
    for key in clean_keys:
        fields[key] = {
            "keep": False,
            "source": None,  # "a" or "b"
            "edit": None     # str or None
        }

    return {
        "cluster_idx": cluster_idx,
        "edge_idx": edge_idx,
        "node_a_id": active_a_id,  # Store the current active node ID
        "node_b_id": active_b_id,  # Store the current active node ID
        "rec_a": rec_a,
        "rec_b": rec_b,
        "fields": fields,
    }


def apply_merge_decision(
    corpus: dict,
    report: list,
    merge_data: dict,
    project_path=None
) -> tuple[dict, list]:
    """
    Applies a validated merge decision to the corpus and report,
    creating a synthetic node C and deprecating nodes A and B.
    """
    cluster_idx = merge_data["cluster_idx"]
    node_a_id = merge_data["node_a_id"]
    node_b_id = merge_data["node_b_id"]
    fields = merge_data.get("fields", {})

    str_a, str_b = str(node_a_id), str(node_b_id)
    rec_a = corpus.get(str_a, {})
    rec_b = corpus.get(str_b, {})

    # 1. Build the synthetic record C using the selected values and fallbacks
    synthetic_record = {}
    for key, rule in fields.items():
        if not rule.get("keep"):
            continue

        edit_val = rule.get("edit")
        if edit_val is not None:
            synthetic_record[key] = edit_val
            continue

        source = rule.get("source")
        val = None

        # Automatic fallback if the selected source does not contain the key
        if source == node_a_id:
            val = rec_a.get(key)
            if val is None:
                val = rec_b.get(key)
        elif source == node_b_id:
            val = rec_b.get(key)
            if val is None:
                val = rec_a.get(key)
        else:
            raise ValueError(f"error: for key: {key} invalid source \"{source}\"")

        synthetic_record[key] = val

    # Traceability metadata
    synthetic_record["_status"] = "active"
    synthetic_record["_merged_from"] = [int(node_a_id), int(node_b_id)]

    # 2. Assign a new ID and insert the synthetic node into the corpus
    str_c = get_next_corpus_id(corpus)
    int_c = int(str_c)
    corpus[str_c] = synthetic_record

    # 3. Deprecate A and B, pointing them to C
    deprecate_source_records(corpus, str_a, str_b, str_c)

    # 4. Re-evaluate connections with the rest of the cluster
    cluster = report[cluster_idx]
    edges = cluster.get("edges_trazability", [])

    threshold = load_threshold_from_project(project_path) if project_path else 0.8
    keys_for_similarity = load_comparison_keys_from_project(project_path)

    neighbor_ids, untouched_edges = collect_neighbors_and_untouched_edges(
        edges,
        node_a_id,
        node_b_id
    )
    new_edges_for_c = recompute_edges_for_synthetic_node(
        corpus,
        synthetic_record,
        int_c,
        neighbor_ids,
        keys_for_similarity,
        threshold
    )

    # 5. Update the cluster structure
    update_cluster_structure(cluster, untouched_edges + new_edges_for_c)

    return corpus, report