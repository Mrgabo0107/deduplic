import argparse
import sys

from ..utils import get_cli_settings


def _parser():
    parser = argparse.ArgumentParser(
        prog="deduplic_get_threshold",
        description="Displays the active global similarity threshold.",
    )
    return parser.parse_args()


def main():
    _parser()

    try:
        cfg = get_cli_settings()
        print(cfg.default_threshold)

    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()