import json
from datetime import datetime
from pathlib import Path
from core.do_reports import do_reports

# ==========================================
# 1. Parsing and Date Utilities
# ==========================================

def get_first_present_key(record: dict, keys: list[str]):
    """Helper to retrieve the first matching value from a list of candidate keys."""
    for k in keys:
        if k in record and record[k] is not None:
            return record[k]
    return None

# ==========================================
# 2. Corpus and Graph Utilities
# ==========================================

def get_next_corpus_id(corpus: dict) -> str:
    """Returns the next available numeric ID for the corpus."""
    if not corpus:
        return "0"
    existing_ids = [int(k) for k in corpus.keys() if k.isdigit()]
    next_id = max(existing_ids) + 1 if existing_ids else len(corpus)
    return str(next_id)


def load_threshold_from_project(project_path: Path | str) -> float:
    """Loads the similarity threshold from the project's metadata.json file."""
    if isinstance(project_path, (str, Path)):
        metadata_file = Path(project_path) / "metadata.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, "r", encoding="utf-8") as f:
                    return float(json.load(f).get("threshold", 0.8))
            except Exception as e:
                print(f"Error loading metadata: {e}")
    return 0.8


def clean_record(record: dict) -> dict:
    """Removes internal metadata keys (prefixed with '_') for comparison purposes."""
    return {k: v for k, v in record.items() if not k.startswith("_")}


def deprecate_source_records(corpus: dict, str_a: str, str_b: str, str_c: str) -> None:
    """Marks source records A and B as deprecated and points them to the merged record C."""
    if str_a in corpus:
        corpus[str_a]["_status"] = "deprecated"
        corpus[str_a]["_merged_to"] = str_c
    if str_b in corpus:
        corpus[str_b]["_status"] = "deprecated"
        corpus[str_b]["_merged_to"] = str_c


def collect_neighbors_and_untouched_edges(
    edges: list,
    node_a_id: int,
    node_b_id: int
) -> tuple[set, list]:
    """
    Collects the neighbors of nodes A and B while separating unaffected edges.
    """
    neighbor_ids = set()
    untouched_edges = []

    for edge in edges:
        p = edge.get("pair", [])
        if len(p) != 2:
            continue

        u, v = p[0], p[1]
        if u in (node_a_id, node_b_id) or v in (node_a_id, node_b_id):
            if u not in (node_a_id, node_b_id):
                neighbor_ids.add(u)
            if v not in (node_a_id, node_b_id):
                neighbor_ids.add(v)
        else:
            untouched_edges.append(edge)

    return neighbor_ids, untouched_edges


def recompute_edges_for_synthetic_node(
    corpus: dict,
    synthetic_record: dict,
    int_c: int,
    neighbor_ids: set,
    keys_to_compare: list,
    threshold: float
) -> list:
    """
    Runs do_reports on the micro-corpus (synthetic node C + neighbors)
    and returns the validated edges.
    """
    if not neighbor_ids:
        return []

    micro_corpus_list = [clean_record(synthetic_record)]
    index_to_real_id = {0: int_c}

    for idx, neighbor_id in enumerate(sorted(neighbor_ids), start=1):
        neighbor_rec = corpus.get(str(neighbor_id), {})
        micro_corpus_list.append(clean_record(neighbor_rec))
        index_to_real_id[idx] = neighbor_id

    sub_reports = do_reports(
        data=micro_corpus_list,
        keys_to_check=keys_to_compare,
        threshold=threshold
    )

    new_edges = []
    if sub_reports:
        for sub_rep in sub_reports:
            for edge in sub_rep.get("edges_trazability", []):
                sub_p = edge.get("pair", [])
                if 0 in sub_p:
                    other_idx = sub_p[1] if sub_p[0] == 0 else sub_p[0]
                    real_neighbor_id = index_to_real_id[other_idx]

                    new_edge = edge.copy()
                    new_edge["pair"] = [int_c, real_neighbor_id]
                    new_edges.append(new_edge)

    return new_edges


def update_cluster_structure(cluster: dict, all_cluster_edges: list) -> None:
    """
    Rebuilds the cluster's nodes, node degrees, and leader after updates.
    """
    cluster["edges_trazability"] = all_cluster_edges

    node_degrees = {}
    nodes_set = set()

    for edge in all_cluster_edges:
        u, v = edge["pair"]
        nodes_set.add(u)
        nodes_set.add(v)
        node_degrees[str(u)] = node_degrees.get(str(u), 0) + 1
        node_degrees[str(v)] = node_degrees.get(str(v), 0) + 1

    if not node_degrees:
        cluster["nodes"] = []
        cluster["node_degrees"] = {}
        cluster["leader"] = None
    else:
        cluster["nodes"] = list(nodes_set)
        cluster["node_degrees"] = node_degrees
        new_leader_str = max(node_degrees, key=lambda k: node_degrees[k])
        cluster["leader"] = int(new_leader_str)

def resolve_active_node(corpus: dict, node_id: str) -> str:
    """
    Recursively follows merge relationships until the active node is found.

    If the given node has been deprecated and merged into another node,
    the function continues traversing the `_merged_to` chain until it
    reaches a node whose status is not 'deprecated'.
    """
    current = str(node_id)

    while corpus.get(current, {}).get("_status") == "deprecated":
        next_node = corpus[current].get("_merged_to")
        if not next_node or next_node == current:
            break
        current = str(next_node)

    return current