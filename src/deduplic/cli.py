import argparse
import json
from pathlib import Path
from deduplic.core import deduplicate
from deduplic.input_adapter import normalize_input

def parser():
    parser = argparse.ArgumentParser(
        description="Deduplic CLI: Remove duplicate records from JSON files."
    )
    
    parser.add_argument(
        "-i", "--input", 
        nargs="+", 
        required=True, 
        help="Path to one or more JSON files to process."
    )
    parser.add_argument(
        "-k", "--keys", 
        nargs="+", 
        required=True, 
        help="Keys to check for duplication (e.g., -k title author)."
    )
    parser.add_argument(
        "-t", "--threshold",
        type=float,
        required=False,
        default=0.8,
        help="Similarity threshold for deduplication (default: 0.8)."
    )

    args = parser.parse_args()
    return args

def main():
    args = parser()
    all_records = normalize_input(args.input)

    print(f"Total records loaded: {len(all_records)}")

    reports = deduplicate(all_records, args.keys, args.threshold)
    print(reports)

if __name__ == "__main__":
    main()