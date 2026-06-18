import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse.csgraph import connected_components
from itertools import combinations
from deduplic.gui import launch_gui
import pprint
import time


def _get_cos_similarity_matrix(data: list[dict], key: str) -> tuple[np.ndarray, np.ndarray]:
    """
    Computes the dense TF-IDF cosine similarity matrix for a specific metadata key.
    
    Returns:
        - similarity_matrix: NxN dense matrix containing cosine similarity scores.
        - presence_mask: Boolean vector tracking which records actually possessed the key.
    """
    # Create a boolean mask to track valid keys and avoid false positives from empty fields
    presence_mask = np.array([bool(record.get(key)) for record in data])
    
    # Fallback to an empty string if the key does not exist to maintain matrix alignment
    text_corpus = [str(record.get(key, "")) for record in data]
    
    # Vectorize the text corpus and compute the NxN similarity scores
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(text_corpus)
    similarity_matrix = cosine_similarity(tfidf_matrix)
    
    return similarity_matrix, presence_mask


def _extract_adjacency_by_key(matrix: np.ndarray, threshold: float, mask: np.ndarray) -> np.ndarray:
    """
    Binarizes the dense similarity matrix into an adjacency graph based on a cosine threshold.
    Ensures both records originally contained the metadata key to eliminate empty-string connections.
    """
    # Keep connections that meet or exceed the calculated cosine threshold
    meets_threshold = matrix >= threshold
    
    # Generate an NxN logical matrix where an edge is valid ONLY if both nodes have the key
    valid_connections = np.outer(mask, mask)
    
    # Perform element-wise AND to get the final binary adjacency matrix for this key
    return (meets_threshold & valid_connections).astype(int)


def _build_component_reports(total: np.ndarray, by_key: dict, cos: dict, threshold: float) -> list:
    """
    Finds independent connected groups (clusters of duplicates) in the unified graph.
    Computes node degrees, identifies cluster leaders, and generates a traceability report.
    """
    # Identify connected components in the graph using SciPy's Graph Theory module
    n_components, labels = connected_components(csgraph=total, directed=False, return_labels=True)
    
    reports = []
    
    # Analyze each isolated component (cluster) found
    for comp_id in range(n_components):
        nodes = np.where(labels == comp_id)[0]
        
        # If a component contains only 1 node, it has no duplicates; skip it
        if len(nodes) <= 1:
            continue
            
        # Calculate the degree of each node within this specific component
        node_degrees = {}
        for node in nodes:
            # Total connections excluding self-loops (diagonal)
            total_connections_with_neighbors = np.sum(total[node]) - total[node, node]
            node_degrees[int(node)] = int(total_connections_with_neighbors)
            
        # Sort nodes by degree in descending order to identify the cluster "leader" (most connected node)
        sorted_nodes = sorted(node_degrees.items(), key=lambda item: item[1], reverse=True)
        
        # --- Traceability / Audit Trail ---
        edges_trazability = []
        
        # Generate all unique node pairs in the cluster to audit their metadata links
        for node_a, node_b in combinations(nodes, 2):
            total_connections = total[node_a, node_b]
            
            # If the two nodes are connected, break down the similarity metrics per key
            if total_connections > 0:
                details = {}
                
                for key, adj_matrix in by_key.items():
                    # If this specific key contributed to the connection, compute its linear similarity
                    if adj_matrix[node_a, node_b] == 1:
                        raw_cos = cos[key][node_a, node_b]
                        
                        # Rescale cosine similarity into a linear percentage based on the angle
                        angle_rad = np.arccos(np.clip(raw_cos, -1.0, 1.0))
                        linear_similarity = 1.0 - (angle_rad / (np.pi / 2))
                        
                        details[key] = float(round(linear_similarity, 4))
                
                # Append the edge data with its complete cross-key audit
                edges_trazability.append({
                    "pair": (int(node_a), int(node_b)),
                    "total_connections": int(total_connections),
                    "details": details
                })
        # --------------------------------------------------------
        
        # Build the structured dictionary for this cluster
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
    Orchestrates the pipeline: computes similarities, handles linear-to-angular 
    threshold mapping, builds the unified graph, and triggers the reporting phase.
    """
    if not (0.0 <= threshold <= 1.0):
        raise ValueError(f"The threshold has to be between 0 and 1, is a probability")
    
    print("aca seguro")
    cos_similarity = {}
    presence_masks = {}
    
    # Step 1: Compute raw similarity matrices and presence masks for every key requested
    for key in keys_to_check:
        matrix, mask = _get_cos_similarity_matrix(data, key)
        cos_similarity[key] = matrix
        presence_masks[key] = mask
        
    adyacent_matrix_by_key = {}
    print("aca adyacent")

    # Step 2: Convert the user's linear threshold into an angular threshold in radians.
    # Formula: If threshold is 0.80 -> (1 - 0.80) * 90 degrees = 18 degrees target angle.
    target_angle_rad = (1 - threshold) * np.pi / 2
    cos_threshold = np.cos(target_angle_rad)

    # Step 3: Binarize individual similarity matrices into key-specific adjacency graphs
    for key, matrix in cos_similarity.items():
        adyacent_matrix_by_key[key] = _extract_adjacency_by_key(matrix, cos_threshold, presence_masks[key])
    print("aca adyacent par key")

    # Step 4: Sum all individual adjacency graphs into a single unified connectivity matrix
    total_connectivity_matrix = np.add.reduce(list(adyacent_matrix_by_key.values()))
    
    print("haciendo reportes")
    # Step 5: Extract clusters and generate the final audit report
    return _build_component_reports(total_connectivity_matrix, adyacent_matrix_by_key, cos_similarity, threshold)


def deduplicate(data: list[dict], keys_to_check: list[str], threshold: float = 0.8) -> list[dict]:
    """
    Main entry point for the deduplication execution. Triggers reporting and launches the GUI view.
    """
    start = time.perf_counter()
    report = do_reports(data, keys_to_check, threshold)
    end = time.perf_counter()
    print(f"execution time: {(end - start):.4f}")
    pprint.pprint(report)
    launch_gui(report)