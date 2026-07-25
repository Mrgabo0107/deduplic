import sys
from pathlib import Path
from core.deduplic import get_state


def main():
    if len(sys.argv) < 2:
        print("Error: Project name is required.")
        print("Usage: python cmd_deduplic_screenshot.py <project_name>")
        sys.exit(1)

    project_name = sys.argv[1]
    
    # Asume la estructura estándar de proyectos: projects/<project_name>
    projects_dir = Path("projects")
    project_path = projects_dir / project_name

    if not project_path.exists() or not project_path.is_dir():
        print(f"Error: Project directory '{project_path}' does not exist.")
        sys.exit(1)

    try:
        output_file = get_state(project_path)
        print(f"\n[SUCCESS] Snapshot created successfully for project '{project_name}'.")
        print(f"Output saved at: {output_file.resolve()}")
    except Exception as e:
        print(f"\n[ERROR] Failed to create screenshot for project '{project_name}': {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()