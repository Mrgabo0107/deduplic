import argparse
import importlib.resources
from pathlib import Path
import subprocess
import sys
from typing import Sequence

from ..utils import get_cli_settings
from deduplic.config import resolve_workspace_dir

def resolve_gui_workspace(target_path: str | Path | None = None) -> Path:
    """Resolves active workspace for GUI.

    - If target_path is provided: must exist and be a directory.
    - Otherwise: falls back directly to get_cli_settings().projects_dir.
    """
    cli_settings = get_cli_settings()
    if target_path:
        candidate = Path(target_path).resolve()
        if not candidate.exists():
            print(
                f"Error: Provided workspace path '{candidate}' does not exist.",
                file=sys.stderr,
            )
            return Path(cli_settings.projects_dir).resolve()
        if not candidate.is_dir():
            print(
                f"Error: Provided path '{candidate}' is a file, not a directory.",
                file=sys.stderr,
            )
            return Path(cli_settings.projects_dir).resolve()
        return candidate

    # Fallback to persistent CLI settings workspace
    return Path(cli_settings.projects_dir).resolve()


def run_gui(argv: Sequence[str] | None = None) -> None:
    """CLI Entry point to parse arguments and launch the Streamlit GUI."""
    parser = argparse.ArgumentParser(
        prog="deduplic-gui",
        description="Launch the Deduplic Streamlit Graphical User Interface.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=None,
        help="Optional relative or absolute path to target workspace directory.",
    )

    args = parser.parse_args(argv)

    try:
        import streamlit  # noqa: F401
    except ImportError:
        print(
            "Error: Optional GUI dependencies are not installed.\n"
            "Please install them using: pip install deduplic[gui]",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        gui_package = importlib.resources.files("deduplic.streamlit_gui")
        app_path = gui_package / "app.py"
    except (ImportError, TypeError, AttributeError):
        print(
            "Error: Could not locate 'deduplic.streamlit_gui' package resources.",
            file=sys.stderr,
        )
        sys.exit(1)

    if not app_path.exists():
        print(
            f"Error: GUI entry point not found at expected location: {app_path}",
            file=sys.stderr,
        )
        sys.exit(1)

    active_workspace = resolve_workspace_dir(resolve_gui_workspace(args.path))

    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.maxMessageSize=500",
        "--browser.gatherUsageStats=false",
        "--",
        "--workspace",
        str(active_workspace),
    ]

    print(f"Starting Deduplic GUI bound to workspace: {active_workspace}")

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nStreamlit GUI session closed.")
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        print(f"Error launching Streamlit application: {e}", file=sys.stderr)
        sys.exit(e.returncode)


if __name__ == "__main__":
    run_gui()