import argparse
import sys
from pathlib import Path
import streamlit as st

from deduplic.config import settings

from deduplic.streamlit_gui.components import render_sidebar, render_workspace
# from .components import render_sidebar, render_workspace


def parse_gui_args() -> Path:
    """Parses custom command-line arguments passed after the '--' separator."""
    parser = argparse.ArgumentParser(
        description="Deduplic Streamlit Application Entrypoint"
    )
    parser.add_argument(
        "--workspace",
        type=str,
        required=True,
        help="Absolute path to active deduplic_projects directory.",
    )

    cli_args = (
        sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else sys.argv[1:]
    )
    args, _ = parser.parse_known_args(cli_args)

    return Path(args.workspace).resolve()


settings.projects_dir = parse_gui_args()

st.set_page_config(
    page_title="Deduplic",
    page_icon="",
    layout="wide",
)

selected_project = render_sidebar()

render_workspace(selected_project)

