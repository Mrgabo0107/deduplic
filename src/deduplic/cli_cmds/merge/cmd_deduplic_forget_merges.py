import argparse
import sys
from pathlib import Path

from deduplic import DeduplicError, deduplic_forget_merges
from deduplic.cli_cmds.utils import get_cli_settings


def _parser():
    parser = argparse.ArgumentParser(
        prog="deduplic_forget_merges",
        description="Deletes the entire 'merges/' directory and all pending merge draft files for a project.",
    )

    parser.add_argument(
        "project_name",
        type=str,
        help="Name of the project directory (located within the active workspace).",
    )

    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force deletion without asking for confirmation (ideal for scripts).",
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

        if not args.force:
            response = (
                input(
                    f"Are you sure you want to delete all pending merges for project '{args.project_name}'? [y/N]: "
                )
                .strip()
                .lower()
            )
            if response not in ("y", "yes"):
                print("Operation canceled.")
                sys.exit(0)

        deduplic_forget_merges(project_path=project_path, confirm=True)

        print(
            f"Successfully removed 'merges/' directory and all draft merges for project '{args.project_name}'."
        )

    except DeduplicError as e:
        print(f"Deduplic Error: {e}", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()