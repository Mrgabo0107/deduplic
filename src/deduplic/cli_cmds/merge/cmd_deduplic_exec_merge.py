import argparse
import sys
from pathlib import Path

from deduplic import DeduplicError, deduplic_execute_merge
from ..utils import get_cli_settings


def _parser():
    parser = argparse.ArgumentParser(
        prog="deduplic_exec_merge",
        description="Executes or updates the state of a pending merge draft between two records (nodes).",
    )

    parser.add_argument(
        "project_name",
        type=str,
        help="Name of the project directory (located within the active workspace).",
    )

    parser.add_argument(
        "node_a_id",
        type=int,
        help="ID of the first record node involved in the merge (integer).",
    )

    parser.add_argument(
        "node_b_id",
        type=int,
        help="ID of the second record node involved in the merge (integer).",
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

        status = deduplic_execute_merge(
            project_path=project_path,
            node_a_id=args.node_a_id,
            node_b_id=args.node_b_id,
        )

        print(f"Merge operation completed with status: '{status}'")

    except DeduplicError as e:
        print(f"Deduplic Error: {e}", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()