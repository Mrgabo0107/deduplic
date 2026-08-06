import argparse
import sys
from pathlib import Path

from deduplic import DeduplicError, deduplic_connection
from ..utils import get_cli_settings


def _parser():
    parser = argparse.ArgumentParser(
        prog="deduplic_connection",
        description="Apply a deduplication method to a specific connection (edge) within a cluster.",
    )

    parser.add_argument(
        "project_name",
        type=str,
        help="Name of the project directory (located within the active workspace).",
    )

    parser.add_argument(
        "cluster_idx",
        type=int,
        help="Index of the target cluster in the report (integer >= 0).",
    )

    parser.add_argument(
        "edge_idx",
        type=int,
        help="Index of the target connection (edge) within the cluster (integer >= 0).",
    )

    parser.add_argument(
        "-m",
        "--method",
        type=str,
        default=None,  # Al ser None, el core usará el settings.default_resolution_method activo
        help="Deduplication strategy to apply (e.g., 'keep_first', 'keep_newest', 'merge'). If omitted, uses global default.",
    )

    return parser.parse_args()


def main():
    args = _parser()

    if args.cluster_idx < 0 or args.edge_idx < 0:
        print(
            "Error: 'cluster_idx' and 'edge_idx' must be integers greater than or equal to 0.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        cfg = get_cli_settings()

        project_path = cfg.projects_dir / args.project_name

        if not project_path.exists():
            print(
                f"Error: Project directory '{project_path}' does not exist in active workspace.",
                file=sys.stderr,
            )
            sys.exit(1)

        # 3. Delegar la resolución a la función del core
        deduplic_connection(
            project_path=project_path,
            cluster_idx=args.cluster_idx,
            edge_idx=args.edge_idx,
            method=args.method,
        )

        used_method = args.method or cfg.default_resolution_method
        print(
            f"Method '{used_method}' successfully applied to "
            f"project '{args.project_name}', cluster {args.cluster_idx}, edge {args.edge_idx}."
        )

    except DeduplicError as e:
        print(f"Deduplic Error: {e}", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()