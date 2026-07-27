import argparse
import json
from pathlib import Path


def create_indexed_dictionary(n: int) -> dict:
    """Creates a dictionary with n elements indexed by numeric strings ('0', '1', etc.),
    where each value is another dictionary containing the key 'texte' with the index itself as a string."""
    return {str(i): {"texte": str(i)} for i in range(n)}


def duplicate_dictionary(original_dictionary: dict) -> dict:
    """Duplicates the records of an indexed dictionary, reindexing the keys
    sequentially starting from '0', while preserving the internal text."""
    new_dictionary = {}
    new_index = 0

    # Iterate over the original dictionary twice to simulate duplication
    for _ in range(2):
        for _, value in original_dictionary.items():
            # Create a copy of the inner value to avoid mutating the original
            # (note: we use "texte" to remain consistent with the original schema)
            new_dictionary[str(new_index)] = {"texte": f"{value["texte"]}as"}
            new_index += 1

    return new_dictionary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Creates an indexed dictionary and duplicates its elements."
    )
    parser.add_argument(
        "n",
        type=int,
        help="Number of initial elements in the dictionary."
    )

    args = parser.parse_args()

    # 1. Create the original dictionary with 'n' elements
    original = create_indexed_dictionary(args.n)

    # 2. Duplicate the dictionary and reindex it
    duplicated = duplicate_dictionary(original)

    # 3. Save as duplic.json right beside the script using pathlib
    output_path = Path(__file__).resolve().parent / "duplic.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(duplicated, f, indent=4, ensure_ascii=False)

    print(f"Duplicated dictionary successfully saved to {output_path}")