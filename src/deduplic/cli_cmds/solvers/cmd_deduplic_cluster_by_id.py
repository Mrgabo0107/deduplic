import argparse
import sys

from deduplic import DeduplicError, deduplic_cluster_by_comp_id
from ..utils import get_cli_settings


def _parser():
    parser = argparse.ArgumentParser(
        prog="deduplic_cluster_by_comp_id",
        description="Applies a deduplication method to all clusters belonging to a specific component_id.",
    )

    parser.add_argument(
        "project_name",
        type=str,
        help="Name of the project directory (located within the active workspace).",
    )

    parser.add_argument(
        "component_id",
        type=int,
        help="ID of the component to deduplicate (integer >= 0).",
    )

    parser.add_argument(
        "-m",
        "--method",
        type=str,
        default=None,  # Si es None, el core usará settings.default_resolution_method
        help="Deduplication strategy to apply. If omitted, uses global default.",
    )

    return parser.parse_args()


def main():
    args = _parser()

    if args.component_id < 0:
        print(
            "Error: 'component_id' must be an integer greater than or equal to 0.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        # 1. Cargar el workspace activo
        cfg = get_cli_settings()

        # 2. Resolver la ruta del proyecto
        project_path = cfg.projects_dir / args.project_name

        if not project_path.exists():
            print(
                f"Error: Project directory '{project_path}' does not exist in active workspace.",
                file=sys.stderr,
            )
            sys.exit(1)

        # 3. Delegar la resolución por component_id al core
        deduplic_cluster_by_comp_id(
            project_path=project_path,
            id_to_find=args.component_id,
            method=args.method,
        )

        used_method = args.method or cfg.default_resolution_method
        print(
            f"Method '{used_method}' successfully applied to "
            f"project '{args.project_name}', component_id {args.component_id}."
        )

    except DeduplicError as e:
        print(f"Deduplic Error: {e}", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()