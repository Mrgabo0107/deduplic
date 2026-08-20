import argparse
import sys

from ..utils import get_cli_settings, set_cli_settings


def _parser():
    parser = argparse.ArgumentParser(
        prog="deduplic_batchsize",
        description="Displays or updates the global batch size setting for deduplication tasks.",
    )
    parser.add_argument(
        "value",
        type=int,
        nargs="?",
        default=None,
        help="Optional target batch size (positive integer, e.g., 64). If omitted, displays current batch size.",
    )
    return parser.parse_args()


def main():
    args = _parser()

    try:
        cfg = get_cli_settings()

        if args.value is None:
            print(f"Current batch size: {cfg.default_batch_size}")
            sys.exit(0)

        if args.value <= 0:
            print("Error: Batch size must be a positive integer greater than 0.", file=sys.stderr)
            sys.exit(1)

        cfg.default_batch_size = args.value
        set_cli_settings()

        print(f"Global batch size set to: {cfg.default_batch_size}")

    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()