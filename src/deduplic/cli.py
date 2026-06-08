import argparse
import json
from pathlib import Path
from deduplic.core import deduplicate
from deduplic.input_adapter import normalize_input


def main():
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
        "-o", "--output", 
        required=True, 
        help="Path where the cleaned JSON file will be saved."
    )

    args = parser.parse_args()

    all_records = normalize_input(args.input)

    print(f"Total records loaded: {len(all_records)}")

    cleaned_records = deduplicate(all_records, args.keys)
    print(cleaned_records)
    
    # removed_count = len(all_records) - len(cleaned_records)
    # print(f"Deduplication complete. Removed {removed_count} duplicates.")
    # print(f"Remaining unique records: {len(cleaned_records)}")

    # output_path = Path(args.output)
    # with open(output_path, 'w', encoding='utf-8') as f:
    #     json.dump(cleaned_records, f, indent=4, ensure_ascii=False)
    # print(f"Cleaned data successfully saved to: {args.output}")

if __name__ == "__main__":
    main()