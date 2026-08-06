import argparse
import sys
from pathlib import Path

from deduplic import (
    DeduplicError,
    DeduplicFileNotFoundError,
    deduplic_init_from_file,
)
from ..utils import get_cli_settings


def _parser():
    def _valid_threshold(value: str) -> float:
        """Validates that the threshold is a float between 0.0 and 1.0."""
        try:
            val = float(value)
        except ValueError:
            raise argparse.ArgumentTypeError(
                f"'{value}' is not a valid floating-point number"
            )

        if not (0.0 <= val <= 1.0):
            raise argparse.ArgumentTypeError(
                f"Threshold must be between 0.0 and 1.0 (got {val})"
            )

        return val

    parser = argparse.ArgumentParser(
        prog="deduplic_init",
        description="""Normalizes a JSON corpus of records into a unified format and generates
a duplicate detection report by comparing specified fields with adjustable similarity thresholds.
""",
    )

    parser.add_argument(
        "path_to_corpus",
        type=str,
        help="Path to the input JSON corpus file.",
    )

    parser.add_argument(
        "keys",
        nargs="+",
        help="Fields/Keys to inspect for duplication (e.g. title author).",
    )

    parser.add_argument(
        "-n",
        "--project_name",
        type=str,
        required=False,
        default=None,
        help="Custom name for the project workspace folder.",
    )

    parser.add_argument(
        "-t",
        "--threshold",
        type=_valid_threshold,
        default=None,
        required=False,
        help="Similarity threshold for deduplication between 0.0 and 1.0 (default: uses stored global setting).",
    )

    return parser.parse_args()


def main():
    args = _parser()

    try:
        get_cli_settings()

        created_folder = deduplic_init_from_file(
            file_path=args.path_to_corpus,
            keys=args.keys,
            name=args.project_name,
            threshold=args.threshold,
        )

        if created_folder is None:
            print(
                "Project creation skipped: No duplicates were found with the given threshold.",
                file=sys.stderr,
            )
            sys.exit(0)

        # Print cleanly to stdout to facilitate piping or capture in bash
        print(f"Deduplic project created: {Path(created_folder).resolve()}")

    except DeduplicFileNotFoundError as e:
        print(f"Error: Target JSON file was not found -> {e}", file=sys.stderr)
        sys.exit(1)

    except DeduplicError as e:
        print(f"Deduplic Error: {e}", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()