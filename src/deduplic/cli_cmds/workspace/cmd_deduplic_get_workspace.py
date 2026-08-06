import argparse
import sys
from pathlib import Path

from ..utils import get_cli_settings


def _parser():
    parser = argparse.ArgumentParser(
        prog="deduplic_get_workspace",
        description="Displays the active deduplic workspace path and its physical status on disk.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Print only the raw path (ideal for scripts and piping).",
    )
    return parser.parse_args()


def main():
    args = _parser()

    try:
        cfg = get_cli_settings()

        workspace_path = cfg.projects_dir.resolve()
        exists = workspace_path.exists()

        if args.quiet:
            # Clean output for scripts
            print(workspace_path)
        else:
            # Option B: Informative output with physical status
            status_str = "EXISTS" if exists else "DOES NOT EXIST YET"
            print(f"Active Workspace: {workspace_path}")
            print(f"Status: {status_str}")

    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()