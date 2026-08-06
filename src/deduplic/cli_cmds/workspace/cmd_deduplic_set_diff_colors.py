import argparse
import sys

from ..utils import get_cli_settings, set_cli_settings

PRESET_COLORS = {
    "red": "#FF4D4D",
    "green": "#4CAF50",
    "blue": "#2196F3",
    "yellow": "#FFEB3B",
    "magenta": "#E91E63",
    "cyan": "#00BCD4",
}


def _parser():
    parser = argparse.ArgumentParser(
        prog="deduplic_set_diff_colors",
        description="Sets the UI visual diff colors (added/removed items).",
    )
    parser.add_argument(
        "--added",
        type=str,
        help="Color for added items (e.g. 'green', 'blue', or hex code '#2196F3').",
    )
    parser.add_argument(
        "--removed",
        type=str,
        help="Color for removed items (e.g. 'red', 'yellow', or hex code '#FF4D4D').",
    )
    return parser.parse_args()


def _normalize_color(color_input: str) -> str:
    color_clean = color_input.strip().lower()
    if color_clean in PRESET_COLORS:
        return PRESET_COLORS[color_clean]
    
    if not color_clean.startswith("#") and len(color_clean) in (3, 6):
        color_clean = f"#{color_clean}"
        
    return color_clean


def main():
    args = _parser()

    if not args.added and not args.removed:
        print("Please specify at least one color: --added or --removed.", file=sys.stderr)
        sys.exit(1)

    try:
        cfg = get_cli_settings()

        if args.added:
            color_val = _normalize_color(args.added)
            cfg.diff_color_added = color_val
            print(f"Color for 'added' set to: {color_val}")

        if args.removed:
            color_val = _normalize_color(args.removed)
            cfg.diff_color_removed = color_val
            print(f"Color for 'removed' set to: {color_val}")

        set_cli_settings()

    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()