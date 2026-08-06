import argparse
import sys

from deduplic import DeduplicError, deduplic_delete_all
from ..utils import get_cli_settings


def _parser():
    parser = argparse.ArgumentParser(
        prog="deduplic_delete_all",
        description="""Deletes ALL projects stored within the active workspace directory.

Warning: This action is destructive and cannot be undone.
""",
    )

    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force deletion of all projects without asking for user confirmation.",
    )

    return parser.parse_args()


def main():
    args = _parser()

    cfg = get_cli_settings()

    if not args.force:
        response = (
            input(
                f"Are you sure you want to delete ALL projects in '{cfg.projects_dir}'? [y/N]: "
            )
            .strip()
            .lower()
        )
        if response not in ("y", "yes"):
            print("Delete all operation aborted by user.", file=sys.stderr)
            sys.exit(0)

    try:
        deduplic_delete_all(confirm=True)
        print("All projects deleted successfully.")

    except DeduplicError as e:
        print(f"Deduplic Error: {e}", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()