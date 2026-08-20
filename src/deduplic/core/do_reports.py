import logging
from collections import defaultdict
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ..config import settings
from ..exceptions import DeduplicConfigError

logger = logging.getLogger(__name__)


def _get_cos_similarity_matrix(
    data: list[dict], key: str
) -> tuple[csr_matrix, np.ndarray]:
    """
    Computes the TF-IDF cosine similarity matrix for a specific key.

    Args:
        data (list[dict]): List of normalized records.
        key (str): Metadata key to vectorize and compare.

    Returns:
        tuple[csr_matrix, np.ndarray]: 
            - similarity_matrix: Sparse matrix containing cosine similarity scores.
            - presence_mask: Boolean vector tracking which records actually possessed the key.
    """
    presence_mask = np.array([bool(record.get(key)) for record in data])
    text_corpus = [str(record.get(key, "")) for record in data]

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(text_corpus)

    similarity_matrix = cosine_similarity(tfidf_matrix, dense_output=False)

    return similarity_matrix, presence_mask


def _extract_adjacency_by_key(
    matrix: csr_matrix, threshold: float, mask: np.ndarray
) -> csr_matrix:
    """
    Binarizes the similarity matrix into an adjacency graph based on a cosine threshold.
    Ensures both records originally contained the metadata key to eliminate empty-string connections.

    Args:
        matrix (csr_matrix): Cosine similarity matrix.
        threshold (float): Mapped cosine threshold value.
        mask (np.ndarray): Presence mask for the metadata key.

    Returns:
        csr_matrix: Binarized adjacency matrix representing valid similarity connections.
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


def _extract_subcorpus_by_indexes(
    indexes: list[int] | set[int], full_corpus: list[dict]
) -> tuple[list[dict], dict[int, int]]:
    """
    Extracts a subset of records from the main corpus given a collection of global indexes.

    Args:
        indexes (list[int] | set[int]): Sequence or set of zero-based record indexes to extract.
        full_corpus (list[dict]): The complete list of normalized dataset records.

    Returns:
        tuple[list[dict], dict[int, int]]:
            - subcorpus: Filtered list of records corresponding to requested indexes.
            - local_to_global_map: Dictionary mapping local subcorpus index -> global corpus index.
    """
    sorted_indexes = sorted(set(indexes))
    subcorpus = []
    local_to_global_map = {}

    for local_idx, global_idx in enumerate(sorted_indexes):
        if 0 <= global_idx < len(full_corpus):
            subcorpus.append(full_corpus[global_idx])
            local_to_global_map[local_idx] = global_idx

    return subcorpus, local_to_global_map


def _process_batch_edges(
    global_edges: dict[tuple[int, int], dict],
    local_to_global_map: dict[int, int],
    data: list[dict],
    keys_to_check: list[str],
    threshold: float,
) -> None:
    """
    Computes sparse similarity matrices for a subcorpus batch, extracts valid edges,
    maps indexes back to global scope, and updates the global edge registry in-place.

    Args:
        global_edges (dict[tuple[int, int], dict]): Shared edge accumulator registry.
        local_to_global_map (dict[int, int]): Mapping from subcorpus index to global index.
        data (list[dict]): Subcorpus slice containing records to evaluate.
        keys_to_check (list[str]): List of metadata keys to evaluate for duplicates.
        threshold (float): Linear similarity threshold (0.0 to 1.0).
    """
    cos_similarity = {}
    presence_masks = {}

    for key in keys_to_check:
        logger.debug(f"Computing TF-IDF similarity for key: '{key}' in batch")
        matrix, mask = _get_cos_similarity_matrix(data, key)
        cos_similarity[key] = matrix
        presence_masks[key] = mask

    adjacency_matrix_by_key = {}
    target_angle_rad = (1 - threshold) * np.pi / 2
    cos_threshold = np.cos(target_angle_rad)

    for key, matrix in cos_similarity.items():
        adjacency_matrix_by_key[key] = _extract_adjacency_by_key(
            matrix, cos_threshold, presence_masks[key]
        )

    first_key = keys_to_check[0]
    total_connectivity_matrix = csr_matrix(
        adjacency_matrix_by_key[first_key].shape, dtype=int
    )

    for adj_matrix in adjacency_matrix_by_key.values():
        total_connectivity_matrix = total_connectivity_matrix + adj_matrix

    coo = total_connectivity_matrix.tocoo()

    for u_local, v_local, total_conn in zip(coo.row, coo.col, coo.data):
        if u_local >= v_local or total_conn <= 0:
            continue

        u_global = local_to_global_map[u_local]
        v_global = local_to_global_map[v_local]
        edge_key = (min(u_global, v_global), max(u_global, v_global))

        details = {}
        for key, adj_matrix in adjacency_matrix_by_key.items():
            if adj_matrix[u_local, v_local] == 1:
                raw_cos = cos_similarity[key][u_local, v_local]
                angle_rad = np.arccos(np.clip(raw_cos, -1.0, 1.0))
                linear_similarity = 1.0 - (angle_rad / (np.pi / 2))
                details[key] = float(round(linear_similarity, 4))

        if edge_key not in global_edges:
            global_edges[edge_key] = {
                "total_connections": int(total_conn),
                "details": details,
            }


def _build_component_reports(
    global_edges: dict[tuple[int, int], dict], total_records: int
) -> list[dict]:
    """
    Finds independent connected groups (clusters of duplicates) from global edges.
    Computes node degrees, identifies cluster leaders, and generates traceability reports.

    Args:
        global_edges (dict[tuple[int, int], dict]): Accumulated global edge dictionary.
        total_records (int): Total number of records in the original dataset.

    Returns:
        list[dict]: Detailed cluster reports identifying duplicates and traceability.
    """
    if not global_edges:
        return []

    row_indexes = []
    col_indexes = []
    for u, v in global_edges.keys():
        row_indexes.extend([u, v])
        col_indexes.extend([v, u])

    data_ones = np.ones(len(row_indexes), dtype=int)
    adj_graph = csr_matrix(
        (data_ones, (row_indexes, col_indexes)), shape=(total_records, total_records)
    )

    n_components, labels = connected_components(
        csgraph=adj_graph, directed=False, return_labels=True
    )

    reports = []
    for comp_id in range(n_components):
        nodes = np.where(labels == comp_id)[0]
        if len(nodes) <= 1:
            continue

        node_set = set(nodes)
        node_degrees = defaultdict(int)
        cluster_edges = []

        for (u, v), edge_info in global_edges.items():
            if u in node_set and v in node_set:
                node_degrees[u] += 1
                node_degrees[v] += 1
                cluster_edges.append(
                    {
                        "pair": [int(u), int(v)],
                        "total_connections": edge_info["total_connections"],
                        "details": edge_info["details"],
                    }
                )

        if not cluster_edges:
            continue

        sorted_nodes = sorted(
            [(int(node), deg) for node, deg in node_degrees.items()],
            key=lambda item: item[1],
            reverse=True,
        )

        component_report = {
            "component_id": int(comp_id),
            "nodes": [int(n) for n in sorted(nodes)],
            "node_degrees": {str(node): deg for node, deg in sorted_nodes},
            "leader": sorted_nodes[0][0],
            "edges_trazability": cluster_edges,
        }
        reports.append(component_report)

    return reports


def deduplic_do_reports(
    data: list[dict], keys_to_check: list[str], threshold: float | None = None
) -> list[dict]:
    """
    Orchestrates the report generation pipeline using a memory-safe batch strategy.

    Computes sparse similarities by partitions, handles linear-to-angular threshold mapping,
    accumulates global edge connections, and returns the list of cluster reports.

    Args:
        data (list[dict]): List of normalized records.
        keys_to_check (list[str]): List of metadata keys to evaluate for duplicates.
        threshold (float | None): Similarity threshold (0.0 to 1.0). If None, uses system default.

    Returns:
        list[dict]: Detailed cluster reports identifying duplicates and traceability.

    Raises:
        DeduplicConfigError: If the provided threshold is outside the [0.0, 1.0] range.
    """
    if threshold is None:
        threshold = settings.default_threshold

    if not (0.0 <= threshold <= 1.0):
        raise DeduplicConfigError(
            f"The threshold must be between 0.0 and 1.0, got: {threshold}"
        )

    total_records = len(data)
    batch_size = settings.default_batch_size
    logger.info(
        f"Starting report generation for {total_records} records across keys: {keys_to_check}"
    )

    global_edges = {}
    blocks = [
        list(range(i, min(i + batch_size, total_records)))
        for i in range(0, total_records, batch_size)
    ]
    total_blocks = len(blocks)

    logger.debug(f"total blocks: {total_blocks}")
    for i in range(total_blocks):
        for j in range(i, total_blocks):
            logger.debug(f"batching blocks: {i,j}")
            if i == j and total_blocks > 1:
                continue
            if i == j:
                target_indexes = blocks[i]
            else:
                target_indexes = blocks[i] + blocks[j]

            subcorpus, local_to_global_map = _extract_subcorpus_by_indexes(
                target_indexes, data
            )

            _process_batch_edges(
                global_edges=global_edges,
                local_to_global_map=local_to_global_map,
                data=subcorpus,
                keys_to_check=keys_to_check,
                threshold=threshold,
            )

    reports = _build_component_reports(global_edges, total_records)
    logger.info(f"Report generation completed. Found {len(reports)} duplicate clusters.")
    return reports