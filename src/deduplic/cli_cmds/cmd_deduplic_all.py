import argparse
from pathlib import Path

from deduplic.core.deduplic import deduplic_all


def resolve_project_path(project_name: str) -> Path:
    path_input = Path(project_name)

    # If the provided path already exists (absolute or relative)
    if path_input.exists():
        return path_input.resolve()

    # Otherwise, look for the project in the repository's 'projects' directory
    repo_root = Path(__file__).resolve().parent.parent.parent
    return repo_root / "projects" / project_name


def main():
    parser = argparse.ArgumentParser(
        description="Apply a deduplication method to all clusters in the report."
    )

    # Required argument
    parser.add_argument(
        "project_name",
        type=str,
        help="Project name (located in the 'projects' directory) or the full path to the project."
    )

    # Optional deduplication method
    parser.add_argument(
        "--method",
        "-m",
        type=str,
        default="keep_all",
        help="Deduplication method to apply to all clusters (default: 'keep_all')."
    )

    args = parser.parse_args()

    # Resolve the project path independently of the current working directory
    project_path = resolve_project_path(args.project_name)

    if not project_path.exists():
        print(f"Error: Project directory '{project_path}' does not exist.")
        return

    # Execute the deduplication
    try:
        deduplic_all(
            project_path=project_path,
            method=args.method,
        )

        print(
            f"Method '{args.method}' successfully applied to "
            f"all clusters in '{project_path.name}'."
        )

    except Exception as e:
        print(f"Error during bulk deduplication: {e}")


if __name__ == "__main__":
    main()