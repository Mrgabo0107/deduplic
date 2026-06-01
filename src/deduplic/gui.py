import subprocess
import sys
from pathlib import Path


def launch_gui():
    """Bridge function that starts Streamlit pointing to this same file."""
    current_file = Path(__file__).resolve()

    print(
        "Starting Streamlit server... Press Ctrl+C to stop it.",
        flush=True
    )

    try:
        subprocess.run(["streamlit", "run", str(current_file)], check=True)
    except KeyboardInterrupt:
        print("\nStreamlit server stopped successfully.")
        sys.exit(0)


# This block only runs when Streamlit re-executes the file
if __name__ == "__main__":
    import streamlit as st

    # Page configuration (browser tab settings)
    st.set_page_config(
        page_title="Deduplic GUI",
        page_icon="🤖",
        layout="centered"
    )

    # Inject CSS to force a full black background
    # and neon green terminal-style text
    st.markdown(
        """
        <style>
        /* Set the main application background */
        .stApp {
            background-color: #000000 !important;
        }

        /* Custom container for neon text */
        .neon-container {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 60vh; /* Vertical centering */
        }

        .neon-text {
            color: #00FF66; /* Bright neon green */
            font-family: 'Courier New', Courier, monospace;
            font-size: 3.5rem;
            font-weight: bold;
            text-align: center;
            text-shadow:
                0 0 5px #00FF66,
                0 0 10px #00FF66,
                0 0 20px #00FF66,
                0 0 40px #00FF66;
            animation: blink 1.5s infinite alternate;
        }

        /* Subtle blinking effect like old terminals */
        @keyframes blink {
            0% { opacity: 0.9; }
            100% { opacity: 1; }
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Render HTML component using custom CSS classes
    st.markdown(
        """
        <div class="neon-container">
            <h1 class="neon-text">Building deduplic!!!</h1>
        </div>
        """,
        unsafe_allow_html=True
    )