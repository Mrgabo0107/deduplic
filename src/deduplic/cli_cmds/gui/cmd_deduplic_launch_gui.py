import sys
import subprocess
from pathlib import Path


def run_gui():
    """Launches the Streamlit graphical interface with optimized server settings."""
    # Locate the absolute path to app.py relative to this file
    gui_dir = Path(__file__).resolve().parent.parent / "streamlit_gui"
    app_path = gui_dir / "app.py"

    if not app_path.exists():
        print(f"Error: GUI entry point not found at: {app_path}")
        sys.exit(1)

    # Build the command with the server flags
    cmd = [
        sys.executable,  # Use the same Python interpreter from the active virtual environment
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.maxMessageSize=500",
        "--browser.gatherUsageStats=false"
    ]

    print(f"Starting Deduplic GUI from: {app_path}")

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nGUI stopped by the user.")
    except subprocess.CalledProcessError as e:
        print(f"Error running Streamlit: {e}")
        sys.exit(e.returncode)


if __name__ == "__main__":
    run_gui()