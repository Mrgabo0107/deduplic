import argparse
from pathlib import Path

from core.deduplic import restore


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
        description="Restore the project to its original state by reverting corpus.json and report.json."
    )

    # Required argument
    parser.add_argument(
        "project_name",
        type=str,
        help="Project name (located in the 'projects' directory) or the full path to the project."
    )

    args = parser.parse_args()

    # Resolve the project path independently of the current working directory
    project_path = resolve_project_path(args.project_name)

    if not project_path.exists():
        print(f"Error: Project directory '{project_path}' does not exist.")
        return

    # Execute the restore operation
    try:
        restore(project_path)
        print(f"Restore completed successfully for '{project_path.name}'.")
    except Exception as e:
        print(f"Error during restore: {e}")


if __name__ == "__main__":
    main()