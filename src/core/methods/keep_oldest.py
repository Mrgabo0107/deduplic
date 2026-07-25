from datetime import datetime, timezone
from typing import Optional
from .utils import (
    get_next_corpus_id,
    load_threshold_from_project,
    clean_record,
    deprecate_source_records,
    collect_neighbors_and_untouched_edges,
    recompute_edges_for_synthetic_node,
    update_cluster_structure,
    get_first_present_key
)

def _extract_timestamp(record: dict) -> Optional[float]:
    """Extracts a normalized float timestamp (seconds since epoch) from a record

    using a robust multi-language key hierarchy (FR, EN, ES).
    """
    if not isinstance(record, dict):
        return None

    # 1. Direct Numeric Epoch/Timestamp
    epoch_val = get_first_present_key(
        record, ["epoch", "timestamp", "created_at_epoch", "ts"]
    )
    if epoch_val is not None:
        try:
            return float(epoch_val)
        except (ValueError, TypeError):
            pass

    # 2. String Date Parsing (ISO-like formats)
    date_str = get_first_present_key(
        record, ["date", "datetime", "created_at", "published_at", "fecha"]
    )
    if date_str and isinstance(date_str, str):
        cleaned_str = date_str.strip()
        # Reemplazar espacios por 'T' si viene en formato "YYYY MM DD T hh:mm:ss" o "YYYY-MM-DD HH:MM:SS"
        cleaned_str = cleaned_str.replace(" ", "T") if " " in cleaned_str else cleaned_str
        
        # Intentar parsear ISO format
        try:
            dt = datetime.fromisoformat(cleaned_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.timestamp()
        except ValueError:
            pass

    # 3. Individual Year/Month/Day components (FR, EN, ES)
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


def _build_synthetic_record_oldest(
    rec_a: dict, 
    rec_b: dict, 
    node_a_id: int, 
    node_b_id: int
) -> dict:
    """Creates synthetic record C by selecting an exact copy of the OLDEST record.

    Falls back to rec_a (first record) in case of equal dates or unparseable dates.
    """
    ts_a = _extract_timestamp(rec_a)
    ts_b = _extract_timestamp(rec_b)

    # Caso A & B: Comparar cuando ambos o uno solo tiene fecha
    if ts_a is not None and ts_b is not None:
        winner_rec = rec_a if ts_a <= ts_b else rec_b
    elif ts_a is not None:
        winner_rec = rec_a
    elif ts_b is not None:
        winner_rec = rec_b
    else:
        # Caso C: Ninguno tiene fecha -> Fallback al primero (rec_a)
        winner_rec = rec_a

    # Copia ÍNTEGRA del registro ganador descartando metadatos antiguos
    synthetic_record = clean_record(winner_rec)

    # Metadatos de trazabilidad
    synthetic_record["_status"] = "active"
    synthetic_record["_merged_from"] = [int(node_a_id), int(node_b_id)]

    return synthetic_record


def keep_oldest(
    corpus: dict,
    report: list,
    target_info: dict,
) -> tuple[dict, list]:
    """Applies the Keep-Oldest deduplication strategy on a specific cluster edge."""
    cluster_idx = target_info["cluster_idx"]
    edge_idx = target_info["edge_idx"]
    threshold = load_threshold_from_project(target_info.get("project_path"))

    cluster = report[cluster_idx]
    edges = cluster.get("edges_trazability", [])

    if not (0 <= edge_idx < len(edges)):
        return corpus, report

    target_edge = edges[edge_idx]
    pair = target_edge.get("pair", [])
    if len(pair) < 2:
        return corpus, report
    if pair[0] == pair[1]:
        return corpus, report

    node_a_id, node_b_id = pair[0], pair[1]
    str_a, str_b = str(node_a_id), str(node_b_id)

    rec_a = corpus.get(str_a, {})
    rec_b = corpus.get(str_b, {})

    details = target_edge.get("details", {})
    keys_for_similarity = list(details.keys()) if details else [
        k for k in rec_a.keys() if not k.startswith("_")
    ]

    # 1. Crear el registro sintético C seleccionando la copia ÍNTEGRA del más antiguo
    synthetic_record = _build_synthetic_record_oldest(rec_a, rec_b, node_a_id, node_b_id)
    str_c = get_next_corpus_id(corpus)
    int_c = int(str_c)
    corpus[str_c] = synthetic_record

    # 2. Marcar A y B como 'deprecated' apuntando a C
    deprecate_source_records(corpus, str_a, str_b, str_c)

    # 3. Recolectar vecinos y calcular nuevas aristas con do_reports
    neighbor_ids, untouched_edges = collect_neighbors_and_untouched_edges(edges, node_a_id, node_b_id)
    new_edges_for_c = recompute_edges_for_synthetic_node(
        corpus, synthetic_record, int_c, neighbor_ids, keys_for_similarity, threshold
    )

    # 4. Actualizar la estructura final del cluster
    update_cluster_structure(cluster, untouched_edges + new_edges_for_c)

    return corpus, report