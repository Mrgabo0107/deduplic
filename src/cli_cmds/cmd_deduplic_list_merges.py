import argparse
import json
from pathlib import Path
from core.merge_manager import list_pending_merges


def main():
    parser = argparse.ArgumentParser(
        description="Lista todos los borradores de merge pendientes con su estado dinámico recalculado."
    )
    parser.add_argument(
        "project_path",
        type=Path,
        help="Ruta al directorio del proyecto."
    )

    args = parser.parse_args()

    try:
        pending = list_pending_merges(args.project_path)
        print(json.dumps(pending, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error al listar los merges: {e}")


if __name__ == "__main__":
    main()