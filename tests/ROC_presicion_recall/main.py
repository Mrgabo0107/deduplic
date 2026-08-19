import sys
import os
from typing import List, Dict

# Asegurar que el directorio de esta carpeta esté disponible en PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from csv_manager import load_predict_clusters_idx, DEFAULT_CSV_PATH


def solve_cluster_in_sub_corpus(target_cluster_ids: List[str]) -> None:
    """
    Función Stub / Marcador de posición.
    En el futuro, esta función procesará el clúster actual.
    """
    pass


def main():
    print("==================================================")
    print("   ROC_precision_recall - Carga e Inspección CSV  ")
    print("==================================================")
    print(f"Target CSV path:\n  -> {DEFAULT_CSV_PATH}\n")

    try:
        predicted_clusters = load_predict_clusters_idx()

        total_clusters = len(predicted_clusters)
        total_elements = sum(len(c) for c in predicted_clusters)

        print("CSV loaded successfully.")
        print(f" - Total clusters detected: {total_clusters}")
        print(f" - Total records/IDs involved: {total_elements}")

        # Clasificar clústeres por tamaño
        clusters_by_size: Dict[int, List[List[str]]] = {}
        for cluster in predicted_clusters:
            size = len(cluster)
            clusters_by_size.setdefault(size, []).append(cluster)

        print("\n--- Muestra de Clústeres filtrados por Tamaño ---")
        for target_size in [2, 3, 4]:
            found = clusters_by_size.get(target_size, [])
            print(f"\n📌 Clústeres de tamaño {target_size} (Encontrados en total: {len(found)}):")
            
            if not found:
                print(f"   (No se encontraron clústeres de tamaño {target_size})")
            else:
                for i, c in enumerate(found[:2], 1):
                    print(f"   #{i}: {c}")

        print("\n--- Procesando clústeres uno a uno ---")
        for i, cluster_ids in enumerate(predicted_clusters, 1):
            solve_cluster_in_sub_corpus(cluster_ids)
            
            if i % 50 == 0 or i == total_clusters:
                print(f" Iteración {i}/{total_clusters} procesada...")

        print("\n🎉 Recorrido completado exitosamente.")

    except Exception as e:
        print(f"Error while processing the CSV: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()