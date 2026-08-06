import argparse
import sys
from pathlib import Path

from deduplic import DeduplicError, deduplic_forget_single_merge
from ..utils import get_cli_settings


def _parser():
    parser = argparse.ArgumentParser(
        prog="deduplic_forget_single_merge",
        description="Deletes a specific pending JSON merge draft file from the project's 'merges/' directory.",
    )

    parser.add_argument(
        "project_name",
        type=str,
        help="Name of the project directory (located within the active workspace).",
    )

    parser.add_argument(
        "filename",
        type=str,
        help="Base filename of the target JSON merge file (e.g., 'merge_cluster_0_edge_1.json').",
    )

    return parser.parse_args()


def main():
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

        removed = deduplic_forget_single_merge(
            project_path=project_path,
            filename=args.filename,
        )

        if removed:
            print(f"Successfully deleted merge draft '{args.filename}' from project '{args.project_name}'.")
        else:
            print(
                f"Warning: Merge draft file '{args.filename}' was not found in 'merges/' directory.",
                file=sys.stderr,
            )
            sys.exit(1)

    except DeduplicError as e:
        print(f"Deduplic Error: {e}", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()