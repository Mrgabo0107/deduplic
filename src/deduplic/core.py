import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse.csgraph import connected_components
from itertools import combinations
from deduplic.gui import launch_gui


def _get_cos_similarity_matrix(data: list[dict], key: str) -> tuple[np.ndarray, np.ndarray]:
    # mask to recognize registers without the key. (similarity_matrix needs "" in the places 
    # of inexistent keys)
    presence_mask = np.array([bool(record.get(key)) for record in data])
    
    # add key with "" in similarity matrix
    text_corpus = [str(record.get(key, "")) for record in data]
    
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(text_corpus)
    similarity_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)
    
    return similarity_matrix, presence_mask


def _extract_adjacency_by_key(matrix: np.ndarray, threshold: float, mask: np.ndarray) -> np.ndarray:
    """
    Binarizes the similarity matrix based on the threshold AND ensures both
    records actually possessed the key originally to avoid empty-string false positives.
    """
    meets_threshold = matrix >= threshold
    
    valid_connections = np.outer(mask, mask)
    
    return (meets_threshold & valid_connections).astype(int)


def _build_component_reports(total: np.ndarray, by_key: dict, cos: dict) -> list:
    n_components, labels = connected_components(csgraph=total, directed=False, return_labels=True)
    
    reports = []
    
    for comp_id in range(n_components):
        nodes = np.where(labels == comp_id)[0]
        
        if len(nodes) <= 1:
            continue
            
        node_degrees = {}
        for node in nodes:
            total_connections_with_neighbors = np.sum(total[node]) - total[node, node]
            node_degrees[int(node)] = int(total_connections_with_neighbors)
            
        sorted_nodes = sorted(node_degrees.items(), key=lambda item: item[1], reverse=True)
        
        # --- trazability ---
        edges_trazability = []
        
        # unique pair generation
        for node_a, node_b in combinations(nodes, 2):
            total_connections = total[node_a, node_b]
            
            if total_connections > 0:
                details = {}
                
                for key, adj_matrix in by_key.items():
                    if adj_matrix[node_a, node_b] == 1:
                        raw_cos = cos[key][node_a, node_b]
                        
                        # reescale to porcentage
                        angle_rad = np.arccos(np.clip(raw_cos, -1.0, 1.0))
                        linear_similarity = 1.0 - (angle_rad / (np.pi / 2))
                        
                        details[key] = float(round(linear_similarity, 4))
                
                # Añadimos la arista con su auditoría completa
                edges_trazability.append({
                    "pair": (int(node_a), int(node_b)),
                    "total_connections": int(total_connections),
                    "details": details
                })
        # --------------------------------------------------------
        
        component_report = {
            "component_id": int(comp_id),
            "nodes": [int(n) for n in nodes],
            "node_degrees": node_degrees,
            "leader": sorted_nodes[0][0],
            "edges_trazability": edges_trazability
        }
        
        reports.append(component_report)
        
    return reports


def do_reports(data: list[dict], keys_to_check: list[str], threshold: float = 0.7) -> list[dict]:
    if not (0.0 <= threshold <= 1.0):
        raise ValueError(f"The threshold has to be between 0 and 1, is a propability")
    
    cos_similarity = {}
    presence_masks = {}
    
    for key in keys_to_check:
        
        matrix, mask = _get_cos_similarity_matrix(data, key)
        cos_similarity[key] = matrix
        presence_masks[key] = mask
    adyacent_matrix_by_key = {}

    # Mapping the linear threshold (e.g., 0.80) to the target angle in radians.
    # If threshold is 0.80 -> (1 - 0.80) * 90 degrees = 18 degrees.
    # A tester whitout
    target_angle_rad = (1 - threshold) * np.pi / 2
    cos_threshold = np.cos(target_angle_rad)



    for key ,matrix in cos_similarity.items():
        adyacent_matrix_by_key[key] = _extract_adjacency_by_key(matrix, cos_threshold, presence_masks[key])

    
    total_connectivity_matrix = np.add.reduce(list(adyacent_matrix_by_key.values()))
    return(_build_component_reports(total_connectivity_matrix, adyacent_matrix_by_key, cos_similarity))


def deduplicate(data: list[dict], keys_to_check: list[str], threshold: float = 0.7) -> list[dict]:
    report = do_reports(data, keys_to_check, threshold)
    launch_gui(report)
    # print (report)