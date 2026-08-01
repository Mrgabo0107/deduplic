from datetime import datetime, timezone
from typing import Any, Literal

from .utils import (
    clean_record,
    collect_neighbors_and_untouched_edges,
    deprecate_source_records,
    get_first_present_key,
    get_next_corpus_id,
    load_threshold_from_project,
    recompute_edges_for_synthetic_node,
    update_cluster_structure,
)


def _extract_timestamp(record: dict[str, Any]) -> float | None:
    """Extracts a normalized float timestamp from a record using multi-language keys."""
    if not isinstance(record, dict):
        return None

    epoch_val = get_first_present_key(record, ["epoch", "timestamp", "created_at_epoch", "ts"])
    if epoch_val is not None:
        try:
            return float(epoch_val)
        except (ValueError, TypeError):
            pass

    date_str = get_first_present_key(record, ["date", "datetime", "created_at", "published_at", "fecha"])
    if date_str and isinstance(date_str, str):
        cleaned_str = date_str.strip().replace(" ", "T")
        try:
            dt = datetime.fromisoformat(cleaned_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.timestamp()
        except ValueError:
            pass

    year = get_first_present_key(record, ["annee", "year", "anio", "año"])
    month = get_first_present_key(record, ["mois", "month", "mes"]) or 1
    day = get_first_present_key(record, ["jour", "day", "dia"]) or 1
    hour = get_first_present_key(record, ["heure", "hour", "hora"]) or 0
    minute = get_first_present_key(record, ["minute", "minuto"]) or 0
    second = get_first_present_key(record, ["seconde", "second", "segundo"]) or 0

    if year is not None:
        try:
            dt = datetime(
                year=int(year),
                month=int(month),
                day=int(day),
                hour=int(hour),
                minute=int(minute),
                second=int(second),
                tzinfo=timezone.utc,
            )
            return dt.timestamp()
        except (ValueError, TypeError):
            pass

    return None


def _keep_by_time_base(
    corpus: dict,
    report: list,
    target_info: dict,
    mode: Literal["newest", "oldest"],
) -> tuple[dict, list]:
    """Base helper function that handles timestamp extraction, comparison, and graph update."""
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

    rec_a, rec_b = corpus.get(str_a, {}), corpus.get(str_b, {})

    ts_a = _extract_timestamp(rec_a)
    ts_b = _extract_timestamp(rec_b)

    # Lógica unificada de comparación según el modo
    if ts_a is not None and ts_b is not None:
        is_winner = (ts_a >= ts_b) if mode == "newest" else (ts_a <= ts_b)
        winner_rec = rec_a if is_winner else rec_b
    elif ts_a is not None:
        winner_rec = rec_a
    elif ts_b is not None:
        winner_rec = rec_b
    else:
        winner_rec = rec_a

    # Reestructuración común del corpus y gráfico
    synthetic_record = clean_record(winner_rec)
    synthetic_record["_status"] = "active"
    synthetic_record["_merged_from"] = [int(node_a_id), int(node_b_id)]

    str_c = get_next_corpus_id(corpus)
    int_c = int(str_c)
    corpus[str_c] = synthetic_record

    deprecate_source_records(corpus, str_a, str_b, str_c)

    details = target_edge.get("details", {})
    keys_for_similarity = list(details.keys()) if details else [k for k in rec_a.keys() if not k.startswith("_")]

    neighbor_ids, untouched_edges = collect_neighbors_and_untouched_edges(edges, node_a_id, node_b_id)
    new_edges_for_c = recompute_edges_for_synthetic_node(
        corpus, synthetic_record, int_c, neighbor_ids, keys_for_similarity, threshold
    )

    update_cluster_structure(cluster, untouched_edges + new_edges_for_c)
    return corpus, report


def keep_newest(corpus: dict, report: list, target_info: dict) -> tuple[dict, list]:
    """Applies Keep-Newest strategy based on extracted timestamps."""
    return _keep_by_time_base(corpus, report, target_info, mode="newest")


def keep_oldest(corpus: dict, report: list, target_info: dict) -> tuple[dict, list]:
    """Applies Keep-Oldest strategy based on extracted timestamps."""
    return _keep_by_time_base(corpus, report, target_info, mode="oldest")