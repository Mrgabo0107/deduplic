import sys
from pathlib import Path
from deduplic.core.deduplic import deduplic_get_state


def main():
    if len(sys.argv) < 2:
        print("Error: Project name is required.")
        sys.exit(1)

    project_name = sys.argv[1]
    
    # Asume la estructura estándar de proyectos: projects/<project_name>
    projects_dir = Path("projects")
    project_path = projects_dir / project_name

    if not project_path.exists() or not project_path.is_dir():
        print(f"Error: Project directory '{project_path}' does not exist.")
        sys.exit(1)

    try:
        output_file = deduplic_get_state(project_path)
        print(f"Output saved at: {output_file.resolve()}")
    except Exception as e:
        print(f"\nerror: Failed to create snapshot for project '{project_name}': {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()