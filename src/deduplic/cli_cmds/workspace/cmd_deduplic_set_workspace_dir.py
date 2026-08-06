import argparse
import sys
from pathlib import Path

from deduplic import DeduplicError, deduplic_set_workspace_dir
from ..utils import get_cli_settings, set_cli_settings


def _parser():
    parser = argparse.ArgumentParser(
        prog="deduplic_set_workspace_dir",
        description="""Sets or resets the global active workspace directory for deduplic projects.

If a path is provided, all future operations will target this directory.
If no path is provided or the --reset flag is used, it restores the default OS user data directory.
""",
    )

    parser.add_argument(
        "path",
        type=str,
        nargs="?",
        default=None,
        help="Optional target directory path for projects (e.g., '/path/to/workspace').",
    )

    parser.add_argument(
        "-r",
        "--reset",
        action="store_true",
        help="Reset the workspace directory to the default OS user data location.",
    )

    return parser.parse_args()


def main():
    args = _parser()

    try:
        get_cli_settings()

        target_path = None if args.reset else args.path
        resolved_path = deduplic_set_workspace_dir(target_path)

        set_cli_settings()

        print(f" Workspace directory set to: {Path(resolved_path).resolve()}")

    except DeduplicError as e:
        print(f"Deduplic Error: {e}", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()