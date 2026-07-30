import argparse
from pathlib import Path

from deduplic.core.deduplic import deduplic_cluster


def resolve_project_path(project_name: str) -> Path:
    path_input = Path(project_name)

    # If the provided path already exists (absolute or relative)
    if path_input.exists():
        return path_input.resolve()

    # Otherwise, look for the project inside the repository's 'projects' directory
    repo_root = Path(__file__).resolve().parent.parent.parent
    project_in_projects = repo_root / "projects" / project_name

    return project_in_projects


def main():
    parser = argparse.ArgumentParser(
        description="Apply a deduplication method to an entire cluster in the report."
    )

    # Required arguments
    parser.add_argument(
        "project_name",
        type=str,
        help="Project name (looked up in the 'projects' directory) or a path to the project."
    )

    parser.add_argument(
        "cluster_idx",
        type=int,
        help="Index of the cluster to process in the report (integer >= 0)."
    )

    # Optional argument
    parser.add_argument(
        "--method",
        "-m",
        type=str,
        default="keep_all",
        help="Deduplication method to apply (default: 'keep_all')."
    )

    args = parser.parse_args()

    # Basic CLI validation
    if args.cluster_idx < 0:
        print("Error: 'cluster_idx' must be an integer greater than or equal to 0.")
        return

    project_path = resolve_project_path(args.project_name)

    if not project_path.exists():
        print(f"Error: Project directory '{project_path}' does not exist.")
        return

    # Execute deduplication
    try:
        deduplic_cluster(
            project_path=project_path,
            cluster_idx=args.cluster_idx,
            method=args.method,
        )

        print(
            f"Method '{args.method}' successfully applied to "
            f"cluster {args.cluster_idx} in '{project_path.name}'."
        )

    except Exception as e:
        print(f"Error while deduplicating the cluster: {e}")


if __name__ == "__main__":
    main()