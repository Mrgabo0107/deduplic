import argparse
from pathlib import Path
from core.merge_manager import forget_merges


def main():
    parser = argparse.ArgumentParser(
        description="Elimina todos los borradores de merge pendientes en la carpeta 'merges/'."
    )
    parser.add_argument(
        "project_path",
        type=Path,
        help="Ruta al directorio del proyecto."
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirmación explícita requerida para eliminar la carpeta merges/."
    )

    args = parser.parse_args()

    if not args.confirm:
        print("Error: Operación cancelada. Debe incluir la bandera '--confirm' para descartar los merges pendientes.")
        return

    try:
        forget_merges(args.project_path, confirm=True)
    except Exception as e:
        print(f"Error al descartar los merges: {e}")


if __name__ == "__main__":
    main()