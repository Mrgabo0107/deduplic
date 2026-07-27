# def keep_all(
#     corpus: dict,
#     report: list,
#     target_info: dict
# ) -> tuple[dict, list]:
#     """
#     Keep All strategy:
#     Preserves all records in the corpus unchanged and only removes
#     the specified connection (edge) from the report.

#     Updates node degrees, removes isolated nodes (degree 0) from the cluster,
#     recalculates the cluster leader if necessary, and deletes the edge from
#     edges_trazability.
#     """
#     cluster_idx = target_info["cluster_idx"]
#     edge_idx = target_info["edge_idx"]

#     # 1. Leave the corpus unchanged
#     # (No records or keys are modified)

#     # 2. Retrieve the target cluster and its structures
#     cluster = report[cluster_idx]
#     edges = cluster.get("edges_trazability", [])

#     if not (0 <= edge_idx < len(edges)):
#         return corpus, report

#     # 3. Get the nodes connected by the target edge
#     target_edge = edges[edge_idx]
#     pair = target_edge.get("pair", [])  # Example: [50, 51]

#     if pair[0] == pair[1]:
#         return corpus, report

#     node_degrees = cluster.get("node_degrees", {})
#     nodes_list = cluster.get("nodes", [])

#     # 4. Decrement the degree of each node in the pair
#     for node_id in pair:
#         node_key = str(node_id)

#         if node_key in node_degrees:
#             node_degrees[node_key] -= 1

#             # Remove nodes that become isolated (degree 0)
#             if node_degrees[node_key] <= 0:
#                 del node_degrees[node_key]

#                 # Remove the node from the cluster node list
#                 if node_id in nodes_list:
#                     nodes_list.remove(node_id)

#     # 5. Remove the edge from edges_trazability
#     edges.pop(edge_idx)

#     # 6. Update the cluster leader if necessary
#     if node_degrees:
#         # The new leader is the node with the highest remaining degree
#         current_leader = cluster.get("leader")
#         if current_leader not in nodes_list:
#             # Recompute the leader based on the maximum node degree
#             new_leader_str = max(node_degrees, key=lambda k: node_degrees[k])
#             cluster["leader"] = int(new_leader_str)
#     else:
#         # No connected nodes remain in the cluster
#         cluster["leader"] = None

#     return corpus, report



def keep_all(
    corpus: dict,
    report: list,
    target_info: dict
) -> tuple[dict, list]:
    """
    Keep All strategy:
    Preserves all records in the corpus unchanged and removes
    the specified connection (edge) from the report, updating
    node degrees according to total_connections of that edge.
    """
    cluster_idx = target_info["cluster_idx"]
    edge_idx = target_info["edge_idx"]

    # 1. Retrieve the target cluster and its structures
    cluster = report[cluster_idx]
    edges = cluster.get("edges_trazability", [])

    if not (0 <= edge_idx < len(edges)):
        return corpus, report

    # 2. Get the target edge and its weight (total_connections)
    target_edge = edges[edge_idx]
    pair = target_edge.get("pair", [])  # Example: [199, 200]

    if len(pair) < 2 or pair[0] == pair[1]:
        return corpus, report

    # ✅ Extraemos el peso real de la arista (por defecto 1 si no existiera la clave)
    weight = target_edge.get("total_connections", 1)

    node_degrees = cluster.get("node_degrees", {})
    nodes_list = cluster.get("nodes", [])

    # 3. Decrement the degree of each node in the pair by the actual WEIGHT
    for node_id in pair:
        node_key = str(node_id)

        if node_key in node_degrees:
            # ✅ Restamos la cantidad total de sub-conexiones que esa arista aportaba
            node_degrees[node_key] -= weight

            # Remove nodes that become isolated (degree <= 0)
            if node_degrees[node_key] <= 0:
                del node_degrees[node_key]

                # Remove the node from the cluster node list
                if node_id in nodes_list:
                    nodes_list.remove(node_id)

    # 4. Remove the edge from edges_trazability
    edges.pop(edge_idx)

    # 5. Update the cluster leader if necessary
    if node_degrees:
        current_leader = cluster.get("leader")
        if current_leader not in nodes_list:
            # Recompute the leader based on the maximum remaining node degree
            new_leader_str = max(node_degrees, key=lambda k: node_degrees[k])
            cluster["leader"] = int(new_leader_str)
    else:
        # No connected nodes remain in the cluster
        cluster["leader"] = None

    return corpus, report