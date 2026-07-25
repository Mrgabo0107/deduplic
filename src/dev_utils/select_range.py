import argparse
import json
import os
import sys

def extract_json_range(source_file, output_file, start_index, end_index):
    """
    Reads the giant JSON file (dictionary of articles) and extracts a specific
    range of elements based on their numeric string keys.
    """
    if not os.path.exists(source_file):
        print(f"Error: The source file '{source_file}' does not exist.")
        sys.exit(1)
        
    print(f" Loading original file ({os.path.getsize(source_file) / (1024*1024):.2f} MB)...")
    
    with open(source_file, 'r', encoding='utf-8') as f:
        full_data = json.load(f)
    
    print(f" Total articles detected in the original file: {len(full_data)}")
    
    sample_data = {}
    counter = 0
    
    # Iterate through the requested index range matching the keys ("0", "1", "2"...)
    for i in range(start_index, end_index):
        key_str = str(i)
        if key_str in full_data:
            sample_data[key_str] = full_data[key_str]
            counter += 1
            
    print(f" Extracting {counter} articles (from index {start_index} to {end_index - 1})...")
    
    # Save the sliced sample into a new formatted JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sample_data, f, ensure_ascii=False, indent=4)
        
    print(f" Done! Sample successfully saved to '{output_file}'")


def main():
    parser = argparse.ArgumentParser(
        description="Corpus Slicer: Extract a specific range of records from the dataset for testing."
    )
    
    parser.add_argument(
        "-i", "--input", 
        required=True, 
        help="Path to the large source JSON file."
    )
    parser.add_argument(
        "-o", "--output", 
        required=True, 
        help="Path where the sliced sample JSON file will be saved."
    )
    parser.add_argument(
        "-s", "--start", 
        type=int, 
        required=True, 
        help="The starting index of the range (inclusive)."
    )
    parser.add_argument(
        "-e", "--end", 
        type=int, 
        required=True, 
        help="The ending index of the range (exclusive)."
    )
    
    args = parser.parse_args()
    
    # Validation to ensure start index is lower than end index
    if args.start >= args.end:
        print("Error: --start index must be strictly less than --end index.")
        sys.exit(1)
        
    extract_json_range(args.input, args.output, args.start, args.end)


if __name__ == "__main__":
    main()