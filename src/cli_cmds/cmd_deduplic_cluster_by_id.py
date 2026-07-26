import argparse
from pathlib import Path
from core.deduplic import deduplic_cluster_by_comp_id

# Localizar dinámicamente la carpeta projects/ relativa a la ubicación de este archivo script
PROJECTS_DIR = Path(__file__).resolve().parents[2] / "projects"


def main():
    parser = argparse.ArgumentParser(
        description="Applies a deduplication method to all clusters belonging to a specific component_id."
    )
    parser.add_argument(
        "project_name",
        type=str,
        help="Name of the project directory inside 'projects/'."
    )
    parser.add_argument(
        "component_id",
        type=int,
        help="ID of the component to deduplicate."
    )
    parser.add_argument(
        "-m", "--method",
        type=str,
        default="keep_all",
        help="Deduplication method to apply (default: 'keep_all')."
    )

    args = parser.parse_args()

    project_path = PROJECTS_DIR / args.project_name

    if not project_path.exists():
        print(f"Error: Project directory '{project_path}' does not exist.")
        return

    try:
        deduplic_cluster_by_comp_id(
            project_path=project_path,
            id_to_find=args.component_id,
            method=args.method
        )
    except Exception as e:
        print(f"Error while deduplicating by component_id: {e}")


if __name__ == "__main__":
    main()