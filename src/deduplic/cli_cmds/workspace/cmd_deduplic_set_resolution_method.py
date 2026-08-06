import argparse
import sys

from ..utils import get_cli_settings, set_cli_settings


def _parser():
    parser = argparse.ArgumentParser(
        prog="deduplic_set_resolution_method",
        description="Sets the global default resolution method.",
    )
    parser.add_argument(
        "method",
        type=str,
        nargs="?",
        default=None,
        help="Optional method name. If omitted, an interactive menu will be displayed.",
    )
    return parser.parse_args()


def main():
    args = _parser()

    try:
        cfg = get_cli_settings()
        available_methods = getattr(cfg, "resolution_methods", ["keep_first", "keep_newest", "merge"])

        selected_method = args.method

        if not selected_method:
            print("\nAvailable resolution methods:")
            for idx, method in enumerate(available_methods, start=1):
                current_flag = " (active)" if method == cfg.default_resolution_method else ""
                print(f"  [{idx}] {method}{current_flag}")

            try:
                choice = input("\nSelect a method by number or name: ").strip()
                if choice.isdigit():
                    index = int(choice) - 1
                    if 0 <= index < len(available_methods):
                        selected_method = available_methods[index]
                    else:
                        print("Error: Invalid index choice.", file=sys.stderr)
                        sys.exit(1)
                else:
                    selected_method = choice
            except (KeyboardInterrupt, EOFError):
                print("\nOperation cancelled.")
                sys.exit(0)

        if selected_method not in available_methods:
            print(f"Error: '{selected_method}' is not a valid method. Choose from {available_methods}", file=sys.stderr)
            sys.exit(1)

        cfg.default_resolution_method = selected_method
        set_cli_settings()

        print(f"Default resolution method updated to: {cfg.default_resolution_method}")

    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()