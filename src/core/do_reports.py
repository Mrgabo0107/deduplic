import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse.csgraph import connected_components
from scipy.sparse import csr_matrix
from itertools import combinations
from pathlib import Path
import json
import time

CORE_DIR = Path(__file__).resolve().parent
MAX_CLUSTER_SIZE_THRESHOLD = 1000

def _get_cos_similarity_matrix(data: list[dict], key: str) -> tuple[csr_matrix, np.ndarray]:
    """
    Computes the TF-IDF cosine similarity matrix for a specific metadata key.
    
    Returns:
        - similarity_matrix: NxN SPARSE matrix (csr_matrix) containing cosine similarity scores.
        - presence_mask: Boolean vector tracking which records actually possessed the key.
    """
    presence_mask = np.array([bool(record.get(key)) for record in data])
    text_corpus = [str(record.get(key, "")) for record in data]
    
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(text_corpus)
    
    similarity_matrix = cosine_similarity(tfidf_matrix, dense_output=False)
    
    return similarity_matrix, presence_mask


def _extract_adjacency_by_key(matrix: csr_matrix, threshold: float, mask: np.ndarray) -> csr_matrix:
    """
    Binarizes the similarity matrix into an adjacency graph based on a cosine threshold.
    Ensures both records originally contained the metadata key to eliminate empty-string connections.
    """
    threshold_mask = matrix.data >= threshold

    filtered_matrix = matrix.copy()
    filtered_matrix.data = threshold_mask.astype(np.float64)
    filtered_matrix.eliminate_zeros()

    coo = filtered_matrix.tocoo()
    valid_edges = mask[coo.row] & mask[coo.col]

    final_rows = coo.row[valid_edges]
    final_cols = coo.col[valid_edges]
    final_data = np.ones(len(final_rows), dtype=int)

    return csr_matrix((final_data, (final_rows, final_cols)), shape=matrix.shape)


def _validate_cluster_safety(labels: np.ndarray, danger_threshold: int) -> None:
    """
    Analyzes the sizes of connected components before deep processing.
    Raises a RuntimeError if any cluster exceeds the safety threshold.
    """
    if len(labels) == 0:
        return

    component_sizes = np.bincount(labels)
    
    if len(component_sizes) > 0:
        max_cluster_size = component_sizes.max()
        
        if max_cluster_size > danger_threshold:
            bad_component_id = component_sizes.argmax()
            example_node = np.where(labels == bad_component_id)[0][0]
            
            raise RuntimeError(
                f"[SAFETY TRIGGER ACTIVATED] Operation aborted to prevent RAM exhaustion.\n"
                f"A massive cluster containing {max_cluster_size} interconnected records was detected.\n"
                f"Record index ({example_node}) or its associated metadata keys are generating too many "
                f"artificial duplicates.\n"
                f"Please review data consistency and look for empty/generic fields before running the pipeline again."
            )


def _build_component_reports(total: csr_matrix, by_key: dict, cos: dict) -> list[dict]:
    """
    Finds independent connected groups (clusters of duplicates) in the unified graph.
    Computes node degrees, identifies cluster leaders, and generates a traceability report.
    """
    n_components, labels = connected_components(
        csgraph=total,
        directed=False,
        return_labels=True
    )

    _validate_cluster_safety(labels, danger_threshold=MAX_CLUSTER_SIZE_THRESHOLD)

    reports = []

    for comp_id in range(n_components):
        nodes = np.where(labels == comp_id)[0]

        if len(nodes) <= 1:
            continue

        node_degrees = {}

        for node in nodes:
            total_connections_with_neighbors = total[node].sum() - total[node, node]
            node_degrees[int(node)] = int(total_connections_with_neighbors)

        sorted_nodes = sorted(
            node_degrees.items(),
            key=lambda item: item[1],
            reverse=True
        )

        edges_trazability = []

        for node_a, node_b in combinations(nodes, 2):
            total_connections = total[node_a, node_b]

            if total_connections > 0:
                details = {}

                for key, adj_matrix in by_key.items():
                    if adj_matrix[node_a, node_b] == 1:
                        raw_cos = cos[key][node_a, node_b]

                        angle_rad = np.arccos(np.clip(raw_cos, -1.0, 1.0))
                        linear_similarity = 1.0 - (angle_rad / (np.pi / 2))

                        details[key] = float(round(linear_similarity, 4))

                edges_trazability.append({
                    "pair": (int(node_a), int(node_b)),
                    "total_connections": int(total_connections),
                    "details": details
                })

        component_report = {
            "component_id": int(comp_id),
            "nodes": [int(n) for n in nodes],
            "node_degrees": node_degrees,
            "leader": sorted_nodes[0][0],
            "edges_trazability": edges_trazability
        }

        reports.append(component_report)

    return reports


def do_reports(data: list[dict], keys_to_check: list[str], threshold: float = 0.8) -> list[dict]:
    """
    Orchestrates the pipeline: computes sparse similarities, handles linear-to-angular
    threshold mapping, builds the unified sparse graph, and returns the raw list of clusters.
    """
    if not (0.0 <= threshold <= 1.0):
        raise ValueError("The threshold has to be between 0 and 1, as it represents a probability.")

    cos_similarity = {}
    presence_masks = {}

    # Step 1: Compute sparse similarity matrices and presence masks
    for key in keys_to_check:
        matrix, mask = _get_cos_similarity_matrix(data, key)
        cos_similarity[key] = matrix
        presence_masks[key] = mask

    adyacent_matrix_by_key = {}

    # Step 2: Threshold mapping
    target_angle_rad = (1 - threshold) * np.pi / 2
    cos_threshold = np.cos(target_angle_rad)

    # Step 3: Binarize matrices
    for key, matrix in cos_similarity.items():
        adyacent_matrix_by_key[key] = _extract_adjacency_by_key(
            matrix,
            cos_threshold,
            presence_masks[key]
        )

    # Step 4: Merge sparse adjacency matrices
    first_key = keys_to_check[0]
    total_connectivity_matrix = csr_matrix(
        adyacent_matrix_by_key[first_key].shape,
        dtype=int
    )

    for adj_matrix in adyacent_matrix_by_key.values():
        total_connectivity_matrix = total_connectivity_matrix + adj_matrix

    # Step 5: Generate and return raw list of cluster reports
    return _build_component_reports(
        total_connectivity_matrix,
        adyacent_matrix_by_key,
        cos_similarity,
    )
