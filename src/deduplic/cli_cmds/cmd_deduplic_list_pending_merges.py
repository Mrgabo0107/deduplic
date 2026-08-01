import argparse
import json
from pathlib import Path
from deduplic.core.methods.merge import deduplic_list_pending_merges

PROJECTS_DIR = Path(__file__).resolve().parents[2] / "projects"


def main():
    parser = argparse.ArgumentParser(
        description="Lists all pending merge drafts with their dynamically recomputed status."
    )
    parser.add_argument(
        "project_name",
        type=str,
        help="Name of the project located inside the 'projects/' directory."
    )

    args = parser.parse_args()

    project_path = PROJECTS_DIR / args.project_name

    if not project_path.exists():
        print(f"Error: Project directory '{project_path}' does not exist.")
        return

    try:
        pending = deduplic_list_pending_merges(project_path)
        print(json.dumps(pending, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error listing merge drafts: {e}")


if __name__ == "__main__":
    main()