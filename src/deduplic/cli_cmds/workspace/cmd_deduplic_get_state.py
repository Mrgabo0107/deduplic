import argparse
import sys
from pathlib import Path

from deduplic import DeduplicError, deduplic_get_state
from ..utils import get_cli_settings


def _parser():
    parser = argparse.ArgumentParser(
        prog="deduplic_get_state",
        description="""Generates a consolidated, active-only JSON corpus snapshot for a given project.

Filters out deprecated records, strips internal metadata, and re-indexes keys sequentially starting from 0.
The snapshot will be saved as 'dedup_corpus.json' within the project directory.
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

        out_file = deduplic_get_state(project_path=project_path, output_path=None)

        print(f" Corpus snapshot generated: {Path(out_file).resolve()}")

    except DeduplicError as e:
        print(f"Deduplic Error: {e}", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()