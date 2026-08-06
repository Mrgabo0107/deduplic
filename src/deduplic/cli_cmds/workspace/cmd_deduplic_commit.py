import argparse
import sys

from deduplic import DeduplicError, deduplic_commit
from ..utils import get_cli_settings


def _parser():
    parser = argparse.ArgumentParser(
        prog="deduplic_commit",
        description="""Consolidates and persists changes from '.draft/' into the project root.

Generates 'dedup_corpus.json', clears draft files, and updates project status to 'committed'.
Blocks execution if pending merge drafts remain unresolved.
""",
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

        deduplic_commit(project_path=project_path)

        print(f"Project '{args.project_name}' successfully committed at : {project_path}/dedup_corpus.json")

    except DeduplicError as e:
        print(f"Deduplic Error: {e}", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()