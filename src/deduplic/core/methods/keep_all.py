def keep_all(
    corpus: dict,
    report: list,
    target_info: dict,
) -> tuple[dict, list]:
    """
    Keep All strategy:
    Preserves all records in corpus unchanged and removes target edge from report,
    updating node degrees according to edge weight.
    """
    cluster_idx = target_info["cluster_idx"]
    edge_idx = target_info["edge_idx"]

    cluster = report[cluster_idx]
    edges = cluster.get("edges_trazability", [])

    if not (0 <= edge_idx < len(edges)):
        return corpus, report

    target_edge = edges[edge_idx]
    pair = target_edge.get("pair", [])

    if len(pair) < 2 or pair[0] == pair[1]:
        return corpus, report

    weight = target_edge.get("total_connections", 1)

    node_degrees = cluster.get("node_degrees", {})
    nodes_list = cluster.get("nodes", [])

    for node_id in pair:
        node_key = str(node_id)

        if node_key in node_degrees:
            node_degrees[node_key] -= weight

            if node_degrees[node_key] <= 0:
                del node_degrees[node_key]
                if node_id in nodes_list:
                    nodes_list.remove(node_id)

    edges.pop(edge_idx)

    if node_degrees:
        current_leader = cluster.get("leader")
        if current_leader not in nodes_list:
            new_leader_str = max(node_degrees, key=lambda k: node_degrees[k])
            cluster["leader"] = int(new_leader_str)
    else:
        cluster["leader"] = None

    return corpus, report