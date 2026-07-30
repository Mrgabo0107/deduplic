import json
import logging
import warnings
from pathlib import Path
from typing import Any
from ..exceptions import CorruptDataWarning, DedupAdapterError

logger = logging.getLogger(__name__)


# CONVERSION STRATEGIES
def _handle_path_or_str(raw_input: Any) -> list[dict]:
    """Loads a file and sends its content back through the main normalization pipeline."""
    path = Path(raw_input).resolve()

    if not path.exists():
        raise FileNotFoundError(f"The file '{path}' does not exist.")

    logger.debug(f"Loading input file from path: {path}")

    with open(path, "r", encoding="utf-8") as f:
        try:
            content = json.load(f)
        except json.JSONDecodeError as e:
            raise DedupAdapterError(
                f"File '{path}' is not a valid JSON. Details: {e}"
            ) from e

    return normalize_input(content)


def _handle_indexed_dict(raw_input: dict) -> list[dict]:
    """Extracts nested dictionaries from an indexed structure, skipping corrupt entries."""
    normalized = []

    for k, val in raw_input.items():
        if isinstance(val, dict):
            normalized.append(val)
        else:
            msg = (
                f"Skipping key '{k}' inside indexed dict. "
                f"Expected dict, got {type(val)}."
            )
            logger.warning(msg)
            warnings.warn(msg, CorruptDataWarning)

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
                msg = f"Skipping element because it resolved to non-dictionary data: {item}"
                logger.warning(msg)
                warnings.warn(msg, CorruptDataWarning)

        except Exception as e:
            # If any nested layer fails (e.g. missing file, invalid JSON),
            # catch the exception, log it, and continue processing
            msg = f"Skipping corrupt element. Reason: {e}"
            logger.warning(msg)
            warnings.warn(msg, CorruptDataWarning)

    return normalized


# CONFIGURATION REGISTRY
# (Evaluation order is critical)

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


# MAIN PUBLIC ENTRY POINT

def normalize_input(raw_input: Any) -> list[dict]:
    """
    Library entry point for input normalization.

    Detects the input format, delegates processing to the corresponding
    strategy, and guarantees safe data extraction into a list of dicts.

    Args:
        raw_input (Any): File path, raw JSON string, list of dicts, or indexed dict.

    Returns:
        list[dict]: A clean, normalized list of record dictionaries.

    Raises:
        DedupAdapterError: If the input data format is unsupported or invalid.
        FileNotFoundError: If a provided path does not exist.
    """

    for condition, handler in FORMAT_STRATEGIES:
        if condition(raw_input):
            return handler(raw_input)

    # Primitive values found in an invalid location (int, float, bool, etc.)
    raise DedupAdapterError(
        f"Unsupported data format: {type(raw_input)} -> {raw_input}"
    )