import argparse
from pathlib import Path
from deduplic.core.merge_manager import deduplic_execute_merge

PROJECTS_DIR = Path(__file__).resolve().parents[2] / "projects"


def main():
    parser = argparse.ArgumentParser(
        description="Executes the consolidation of a merge draft between two nodes."
    )
    parser.add_argument(
        "project_name",
        type=str,
        help="Name of the project located inside the 'projects/' directory."
    )
    parser.add_argument(
        "node_a_id",
        type=int,
        help="ID of the first node involved in the merge."
    )
    parser.add_argument(
        "node_b_id",
        type=int,
        help="ID of the second node involved in the merge."
    )

    args = parser.parse_args()

    project_path = PROJECTS_DIR / args.project_name

    if not project_path.exists():
        print(f"Error: Project directory '{project_path}' does not exist.")
        return

    try:
        status = deduplic_execute_merge(project_path, args.node_a_id, args.node_b_id)
        print(f"Operation result: {status}")
    except Exception as e:
        print(f"Error executing the merge: {e}")


if __name__ == "__main__":
    main()