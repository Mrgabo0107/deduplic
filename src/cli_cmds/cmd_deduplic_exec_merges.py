import argparse
from pathlib import Path
from core.merge_manager import execute_merge


def main():
    parser = argparse.ArgumentParser(
        description="Ejecuta la consolidación de un borrador de merge entre dos nodos."
    )
    parser.add_argument(
        "project_path",
        type=Path,
        help="Ruta al directorio del proyecto."
    )
    parser.add_argument(
        "node_a_id",
        type=int,
        help="ID del primer nodo involucrado en el merge."
    )
    parser.add_argument(
        "node_b_id",
        type=int,
        help="ID del segundo nodo involucrado en el merge."
    )

    args = parser.parse_args()

    try:
        status = execute_merge(args.project_path, args.node_a_id, args.node_b_id)
        print(f"Resultado de la operación: {status}")
    except Exception as e:
        print(f"Error al ejecutar el merge: {e}")


if __name__ == "__main__":
    main()