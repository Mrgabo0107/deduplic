import argparse
from pathlib import Path
from deduplic.core.deduplic import deduplic_connection


def main():
    parser = argparse.ArgumentParser(
        description="Apply a deduplication method to a specific connection (edge) within a cluster."
    )

    # 1. Required command-line arguments
    parser.add_argument(
        "project_name",
        type=str,
        help="Name of the project directory (located in 'projects/' or specified as a relative path)."
    )

    parser.add_argument(
        "cluster_idx",
        type=int,
        help="Index of the target cluster in the report (integer >= 0)."
    )

    parser.add_argument(
        "edge_idx",
        type=int,
        help="Index of the target connection (edge) within the cluster (integer >= 0)."
    )

    # 2. Optional deduplication method
    parser.add_argument(
        "--method",
        "-m",
        type=str,
        default="keep_all",
        help="Deduplication method to apply (default: 'keep_all')."
    )

    args = parser.parse_args()

    # 3. Basic CLI validation
    if args.cluster_idx < 0 or args.edge_idx < 0:
        print("Error: 'cluster_idx' and 'edge_idx' must be integers greater than or equal to 0.")
        return


    PROJECTS_DIR = Path(__file__).resolve().parent.parent.parent / "projects"
    project_path = PROJECTS_DIR / args.project_name

    if not project_path.exists():
        print(f"Error: Project directory '{project_path}' does not exist.")
        return

    # 5. Delegate execution to the core logic
    try:
        deduplic_connection(
            project_path=project_path,
            cluster_idx=args.cluster_idx,
            edge_idx=args.edge_idx,
            method=args.method,
        )

        print(
            f"Method '{args.method}' successfully applied to "
            f"cluster {args.cluster_idx}, connection {args.edge_idx}."
        )

    except Exception as e:
        print(f"Error during deduplication: {e}")


if __name__ == "__main__":
    main()