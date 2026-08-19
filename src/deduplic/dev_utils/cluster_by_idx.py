import sys
import json
import argparse
from typing import Dict, Any, List, Union, Set, Iterable


def build_light_cluster(
    indices: Iterable[Union[int, str]], 
    corpus_data: Union[Dict[str, Any], List[Any]]
) -> List[Dict[str, Any]]:
    """
    Construye un sub-corpus/clúster extremadamente ligero dado un conjunto o lista de índices.
    Aplica una deduplicación automática de los índices usando `set` y es tolerante a 
    errores de límites u homónimos inexistentes.

    Solo conserva las llaves 'identifiant' y 'texte' para minimizar la memoria RAM.

    :param indices: Iterable (Set, List, Tuple) de identificadores a extraer.
    :param corpus_data: Corpus completo cargado (dict o list).
    :return: Lista de diccionarios reducidos: [{"identifiant": id, "texte": "..."}, ...]
    """
    extracted_cluster = []
    # Garantizamos unicidad de los índices mediante un set de strings para búsqueda rápida
    unique_indices: Set[str] = {str(idx).strip() for idx in indices}

    if isinstance(corpus_data, dict):
        for idx_str in unique_indices:
            # Buscar por llave de texto o entera si aplica
            record = corpus_data.get(idx_str)
            if record is None and idx_str.isdigit():
                record = corpus_data.get(int(idx_str))

            if isinstance(record, dict):
                text_content = record.get("texte")
                if text_content is not None:
                    extracted_cluster.append({
                        "identifiant": idx_str,
                        "texte": text_content
                    })

    elif isinstance(corpus_data, list):
        for idx_str in unique_indices:
            if idx_str.isdigit():
                idx_int = int(idx_str)
                if 0 <= idx_int < len(corpus_data):
                    record = corpus_data[idx_int]
                    if isinstance(record, dict):
                        text_content = record.get("texte")
                        if text_content is not None:
                            extracted_cluster.append({
                                "identifiant": idx_str,
                                "texte": text_content
                            })

    return extracted_cluster


def main():
    parser = argparse.ArgumentParser(
        description="Extrae un subcorpus ligero filtrado por índices únicos para pruebas de deduplicación."
    )
    parser.add_argument(
        "--corpus", 
        type=str, 
        required=True, 
        help="Ruta al archivo JSON del corpus."
    )
    parser.add_argument(
        "--indices", 
        type=int, 
        nargs="+", 
        required=True, 
        help="Lista de enteros separados por espacios que representan los índices a extraer."
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default=None, 
        help="Ruta opcional para guardar el subcorpus generado en un JSON ligero."
    )

    args = parser.parse_args()

    print(f"Cargando corpus desde: {args.corpus}...")
    with open(args.corpus, "r", encoding="utf-8") as f:
        corpus_data = json.load(f)

    # Convertir a set para asegurar la deduplicación de entradas recibidas por consola
    raw_indices: Set[int] = set(args.indices)
    print(f"Índices únicos recibidos por CLI: {len(raw_indices)}")

    subcorpus = build_light_cluster(raw_indices, corpus_data)
    print(f"Registros efectivamente extraídos: {len(subcorpus)}")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(subcorpus, f, ensure_ascii=False, indent=2)
        print(f"Subcorpus ligero guardado en: {args.output}")
    else:
        # Si no especifica salida, mostramos una muestra rápida en consola
        print("\nMuestra del subcorpus generado:")
        for doc in subcorpus[:3]:
            preview = doc['texte'][:80].replace('\n', ' ')
            print(f"  - ID: {doc['identifiant']} | Texto: '{preview}...'")


if __name__ == "__main__":
    main()