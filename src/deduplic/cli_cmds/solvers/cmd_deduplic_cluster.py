import argparse
import sys
from pathlib import Path

from deduplic import DeduplicError, deduplic_cluster
from ..utils import get_cli_settings


def _parser():
    parser = argparse.ArgumentParser(
        prog="deduplic_cluster",
        description="Apply a deduplication method to an entire cluster within a project.",
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
        "-m",
        "--method",
        type=str,
        default=None,  # If None, the core will use settings.default_resolution_method
        help="Deduplication strategy to apply. If omitted, uses global default.",
    )

    return parser.parse_args()


def main():
    # import logging

    # logging.basicConfig(
    #     level=logging.DEBUG,
    #     format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    #     stream=sys.stderr,
    # )
    args = _parser()

    if args.cluster_idx < 0:
        print(
            "Error: 'cluster_idx' must be an integer greater than or equal to 0.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        # 1. Hydrate the Singleton from the active configuration (.pkl)
        cfg = get_cli_settings()

        # 2. Resolve the path within the active workspace
        project_path = cfg.projects_dir / args.project_name

        if not project_path.exists():
            print(
                f"Error: Project directory '{project_path}' does not exist in active workspace.",
                file=sys.stderr,
            )
            sys.exit(1)

        # 3. Delegate resolution to the core function
        deduplic_cluster(
            project_path=project_path,
            cluster_idx=args.cluster_idx,
            method=args.method,
        )

        used_method = args.method or cfg.default_resolution_method
        print(
            f"Method '{used_method}' successfully applied to "
            f"project '{args.project_name}', cluster {args.cluster_idx}."
        )

    except DeduplicError as e:
        print(f"Deduplic Error: {e}", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()