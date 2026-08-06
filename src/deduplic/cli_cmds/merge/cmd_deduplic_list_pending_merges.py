import argparse
import json
import sys
from pathlib import Path

from deduplic import DeduplicError, deduplic_list_pending_merges
from ..utils import get_cli_settings


def _parser():
    parser = argparse.ArgumentParser(
        prog="deduplic_list_pending_merges",
        description="Lists all pending interactive merge preview structures for a given project.",
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

        merges_list = deduplic_list_pending_merges(project_path=project_path)

        # 4. Imprimir el resultado formateado en JSON por stdout
        print(json.dumps(merges_list, indent=2, ensure_ascii=False))

    except DeduplicError as e:
        print(f"Deduplic Error: {e}", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()