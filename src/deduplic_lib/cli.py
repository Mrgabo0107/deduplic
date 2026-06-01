import argparse
import json
import sys
from pathlib import Path
from core import deduplicate

def validate_and_load_json(file_path: str) -> list[dict]:
    """Checks if the file exists and normalizes it into a list of dictionaries."""
    path = Path(file_path)
    if not path.exists():
        print(f"Error: The file '{file_path}' does not exist.", file=sys.stderr)
        sys.exit(1)
        
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # if it's a list pass
            if isinstance(data, list):
                return data
                
            # if it's a dictionary set into a list
            elif isinstance(data, dict):
                return [data]
                
            else:
                print(f"Error: '{file_path}' has an invalid format.", file=sys.stderr)
                sys.exit(1)
                
    except json.JSONDecodeError as e:
        print(f"Error: '{file_path}' is not a valid JSON file. Details: {e}", file=sys.stderr)
        sys.exit(1)

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

    all_records = []
    for file_path in args.input:
        records = validate_and_load_json(file_path)
        all_records.extend(records)
        
    print(f"Total records loaded: {len(all_records)}")

    cleaned_records = deduplicate(all_records, args.keys)
    
    removed_count = len(all_records) - len(cleaned_records)
    print(f"Deduplication complete. Removed {removed_count} duplicates.")
    print(f"Remaining unique records: {len(cleaned_records)}")

    output_path = Path(args.output)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(cleaned_records, f, indent=4, ensure_ascii=False)
    print(f"Cleaned data successfully saved to: {args.output}")

if __name__ == "__main__":
    main()