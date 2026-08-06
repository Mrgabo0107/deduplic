import argparse
import shutil
import sys

from deduplic import DeduplicError, deduplic_purge_workspace
from ..utils import CONFIG_DIR, get_cli_settings


def _parser():
    parser = argparse.ArgumentParser(
        prog="deduplic_purge_workspace",
        description="""Purges all projects and temporary draft data from the active workspace directory, 
and resets the CLI user configuration directory.

Warning: This action is destructive and cannot be undone.
""",
    )

    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force purge without asking for user confirmation.",
    )

    return parser.parse_args()


def main():
    args = _parser()

    get_cli_settings()

    if not args.force:
        response = (
            input(
                "Are you sure you want to purge the current workspace AND clear configuration? [y/N]: "
            )
            .strip()
            .lower()
        )
        if response not in ("y", "yes"):
            print("Purge aborted by user.", file=sys.stderr)
            sys.exit(0)

    try:
        deduplic_purge_workspace(confirm=True)

        if CONFIG_DIR.exists():
            shutil.rmtree(CONFIG_DIR)

        print("Workspace and user configuration purged successfully.")

    except DeduplicError as e:
        print(f"Deduplic Error: {e}", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()