import argparse
import sys
from pathlib import Path

from deduplic import DeduplicError, deduplic_all
from ..utils import get_cli_settings


def _parser():
    parser = argparse.ArgumentParser(
        prog="deduplic_all",
        description="Applies a deduplication method sequentially across all clusters in the project.",
    )

    parser.add_argument(
        "project_name",
        type=str,
        help="Name of the project directory (located within the active workspace).",
    )

    parser.add_argument(
        "-m",
        "--method",
        type=str,
        default=None,  # Si es None, el core usará settings.default_resolution_method
        help="Deduplication strategy to apply to all clusters. If omitted, uses global default.",
    )

    return parser.parse_args()


def main():
    import logging

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
    )
    args = _parser()

    try:
        cfg = get_cli_settings()

        project_path = cfg.projects_dir / args.project_name

        if not project_path.exists():
            print(
                f"Error: Project directory '{project_path}' does not exist in active workspace.",
                file=sys.stderr,
            )
            sys.exit(1)

        deduplic_all(
            project_path=project_path,
            method=args.method,
        )

        used_method = args.method or cfg.default_resolution_method
        print(
            f"Method '{used_method}' successfully applied across all clusters "
            f"in project '{args.project_name}'."
        )

    except DeduplicError as e:
        print(f"Deduplic Error: {e}", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()