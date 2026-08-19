import os
import pandas as pd
from typing import List, Dict, Set

# Hardcoded path relative to the location of this file
DEFAULT_CSV_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "../../data_real/data_2/GT_europresse/201401_data-GT/GT1_201401.csv"
    )
)


def load_predict_clusters_idx(csv_path: str = DEFAULT_CSV_PATH) -> List[List[str]]:
    """
    Loads the Ground Truth CSV and returns a list of lists of indices/IDs.
    Each sublist represents a cluster of duplicate elements.

    :param csv_path: Path to the CSV file.
    :return: List[List[str]] representing the clusters.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found at: {csv_path}")

    # Try to read with automatic separator detection (commas or semicolons)
    try:
        df = pd.read_csv(csv_path, sep=None, engine="python")
    except Exception:
        df = pd.read_csv(csv_path)

    # Normalize column names to lowercase to make searching easier
    cols_map = {col: str(col).strip().lower() for col in df.columns}
    df.rename(columns=cols_map, inplace=True)

    clusters_dict: Dict[str, Set[str]] = {}

    # Case A: The CSV has an explicit Cluster/Group column and an ID column
    cluster_col = next(
        (c for c in df.columns if "cluster" in c or "group" in c or "label" in c),
        None
    )
    id_col = next(
        (c for c in df.columns if c in ["id", "identifiant", "doc_id", "article_id"]),
        None
    )

    if cluster_col and id_col:
        for _, row in df.iterrows():
            c_id = str(row[cluster_col]).strip()
            item_id = str(row[id_col]).strip()

            if c_id not in clusters_dict:
                clusters_dict[c_id] = set()

            clusters_dict[c_id].add(item_id)

        # Filter clusters containing at least one element
        return [list(group) for group in clusters_dict.values() if len(group) > 0]

    # Case B: The CSV is structured as pairs (id_1, id_2)
    # -> Build connected components
    id1_col = next(
        (c for c in df.columns if "1" in c or "src" in c or "a" in c),
        None
    )
    id2_col = next(
        (c for c in df.columns if "2" in c or "dst" in c or "b" in c),
        None
    )

    if id1_col and id2_col:
        adj: Dict[str, Set[str]] = {}
        all_nodes: Set[str] = set()

        for _, row in df.iterrows():
            u, v = str(row[id1_col]).strip(), str(row[id2_col]).strip()

            all_nodes.update([u, v])
            adj.setdefault(u, set()).add(v)
            adj.setdefault(v, set()).add(u)

        # BFS / DFS to extract connected components
        visited: Set[str] = set()
        connected_components: List[List[str]] = []

        for node in all_nodes:
            if node not in visited:
                component = []
                queue = [node]
                visited.add(node)

                while queue:
                    curr = queue.pop(0)
                    component.append(curr)

                    for neighbor in adj.get(curr, []):
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)

                connected_components.append(component)

        return connected_components

    # Case C: Fallback if there is only one ID column per row
    # or if the format is non-standard
    first_col = df.columns[0]
    raw_clusters = []

    for val in df[first_col].dropna().unique():
        raw_clusters.append([str(val).strip()])

    return raw_clusters