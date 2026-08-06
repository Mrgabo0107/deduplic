import argparse
import sys

from deduplic import DeduplicError, deduplic_delete_project
from ..utils import get_cli_settings


def _parser():
    parser = argparse.ArgumentParser(
        prog="deduplic_delete_project",
        description="Deletes a specific project directory from the active workspace.",
    )

    parser.add_argument(
        "project_name",
        type=str,
        help="Name of the project folder to delete.",
    )

    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force deletion of the project without asking for user confirmation.",
    )

    return parser.parse_args()


def main():
    args = _parser()

    cfg = get_cli_settings()

    target_project_path = cfg.projects_dir / args.project_name

    if not args.force:
        response = (
            input(
                f"Are you sure you want to delete project '{args.project_name}'? [y/N]: "
            )
            .strip()
            .lower()
        )
        if response not in ("y", "yes"):
            print("Delete project operation aborted by user.", file=sys.stderr)
            sys.exit(0)

    try:
        deduplic_delete_project(project_path=target_project_path, confirm=True)
        print(f"Project '{args.project_name}' deleted successfully.")

    except DeduplicError as e:
        print(f"Deduplic Error: {e}", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()