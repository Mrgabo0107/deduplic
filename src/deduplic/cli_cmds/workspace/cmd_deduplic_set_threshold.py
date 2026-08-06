import argparse
import sys

from ..utils import get_cli_settings, set_cli_settings


def _parser():
    parser = argparse.ArgumentParser(
        prog="deduplic_set_threshold",
        description="Sets the global default similarity threshold (float between 0.0 and 1.0).",
    )
    parser.add_argument(
        "value",
        type=float,
        help="Target threshold value (e.g., 0.85).",
    )
    return parser.parse_args()


def main():
    args = _parser()

    try:
        if not (0.0 <= args.value <= 1.0):
            print("Error: Threshold must be a float between 0.0 and 1.0", file=sys.stderr)
            sys.exit(1)

        cfg = get_cli_settings()
        cfg.default_threshold = args.value
        set_cli_settings()

        print(f"Global threshold set to: {cfg.default_threshold}")

    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()