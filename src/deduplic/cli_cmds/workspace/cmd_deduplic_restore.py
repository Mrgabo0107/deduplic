import argparse
import sys
from pathlib import Path

from deduplic import DeduplicError, deduplic_restore
from ..utils import get_cli_settings


def _parser():
    parser = argparse.ArgumentParser(
        prog="deduplic_restore",
        description="Restores the project to its original state by reverting draft corpus and report files.",
    )

    parser.add_argument(
        "project_name",
        type=str,
        help="Name of the project folder within the active workspace.",
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

        deduplic_restore(project_path=project_path)

        print(f"Project '{args.project_name}' successfully restored to its original state.")

    except DeduplicError as e:
        print(f"Deduplic Error: {e}", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()