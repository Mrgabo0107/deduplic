import json
import warnings
from pathlib import Path
from typing import Any


class CorruptDataWarning(UserWarning):
    """Custom warning used to report anomalies without interrupting execution."""
    pass


# =====================================================================
# CONVERSION STRATEGIES
# =====================================================================

def _handle_path_or_str(raw_input: Any) -> list[dict]:
    """Loads a file and sends its content back through the main normalization pipeline."""
    path = Path(raw_input).resolve()

    if not path.exists():
        raise FileNotFoundError(f"The file '{path}' does not exist.")

    with open(path, "r", encoding="utf-8") as f:
        try:
            content = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"File '{path}' is not a valid JSON. Details: {e}"
            )

    return normalize_input(content)


def _handle_indexed_dict(raw_input: dict) -> list[dict]:
    """Extracts nested dictionaries from an indexed structure, skipping corrupt entries."""
    normalized = []

    for k, val in raw_input.items():
        if isinstance(val, dict):
            normalized.append(val)
        else:
            warnings.warn(
                f"Skipping key '{k}' inside indexed dict. "
                f"Expected dict, got {type(val)}.",
                CorruptDataWarning
            )

    return normalized


def _handle_pure_dict(raw_input: dict) -> list[dict]:
    """Wraps a single dictionary into a list to preserve the normalized format."""
    return [raw_input]


def _handle_list(raw_input: list) -> list[dict]:
    """Iterates through the list, traverses recursively, and strictly validates the final result."""
    normalized = []

    for item in raw_input:
        try:
            # Traverse recursively until the deepest valid structure is reached
            res = normalize_input(item)

            # Ensure that everything returned from recursion consists only of dictionaries
            if all(isinstance(x, dict) for x in res):
                normalized.extend(res)
            else:
                warnings.warn(
                    f"Skipping element because it resolved to non-dictionary data: {item}",
                    CorruptDataWarning
                )

        except Exception as e:
            # If any nested layer fails (e.g. missing file, invalid JSON),
            # catch the exception and continue processing
            warnings.warn(
                f"Skipping corrupt element. Reason: {e}",
                CorruptDataWarning
            )

    return normalized


# =====================================================================
# CONFIGURATION REGISTRY
# (Evaluation order is critical)
# =====================================================================

FORMAT_STRATEGIES = [
    (lambda x: isinstance(x, (str, Path)), _handle_path_or_str),

    (lambda x: isinstance(x, list), _handle_list),

    (lambda x:
        isinstance(x, dict)
        and x
        and all(str(k).isdigit() for k in x.keys()),
        _handle_indexed_dict
    ),

    (lambda x: isinstance(x, dict), _handle_pure_dict),
]


# =====================================================================
# MAIN PUBLIC ENTRY POINT
# =====================================================================

def normalize_input(raw_input: Any) -> list[dict]:
    """
    Library entry point.

    Detects the input format, delegates processing to the corresponding
    strategy, and guarantees safe data extraction.
    """

    for condition, handler in FORMAT_STRATEGIES:
        if condition(raw_input):
            return handler(raw_input)

    # Primitive values found in an invalid location
    # (int, float, bool, etc.)
    raise ValueError(
        f"Unsupported data format: {type(raw_input)} -> {raw_input}"
    )