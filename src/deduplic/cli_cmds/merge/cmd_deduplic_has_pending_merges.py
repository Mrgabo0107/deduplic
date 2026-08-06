import argparse
import sys
from pathlib import Path

from deduplic import DeduplicError, deduplic_has_pending_merges
from ..utils import get_cli_settings


def _parser():
    parser = argparse.ArgumentParser(
        prog="deduplic_has_pending_merges",
        description="Checks whether a project has any interactive merge draft files pending resolution in 'merges/'.",
    )

    parser.add_argument(
        "project_name",
        type=str,
        help="Name of the project directory (located within the active workspace).",
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

        has_merges = deduplic_has_pending_merges(project_path=project_path)

        if has_merges:
            print(f"There are pending merges in: `{project_path}/merges`")
        else:
            print(f"There are no pending merges for the project: `{args.project_name}`")

    except DeduplicError as e:
        print(f"Deduplic Error: {e}", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()