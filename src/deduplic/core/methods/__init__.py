from ...exceptions import DeduplicError
from .keep_all import keep_all
from .keep_first import keep_first
from .keep_largest import keep_largest
from .keep_last import keep_last
from .keep_shortest import keep_shortest
from .keep_by_time import keep_newest, keep_oldest
from .utils import clean_record

METHODS_REGISTRY = {
    "keep_all": keep_all,
    "keep_largest": keep_largest,
    "keep_shortest": keep_shortest,
    "keep_newest": keep_newest,
    "keep_oldest": keep_oldest,
    "keep_first": keep_first,
    "keep_last": keep_last,
}


def apply_method(
    method_name: str,
    corpus_draft: dict,
    report_draft: list,
    target_info: dict,
) -> tuple[dict, list]:
    """
    Main wrapper for deduplication methods.
    Validates method availability and delegates execution.

    Raises:
        DeduplicError: If the specified method_name is unsupported.
    """
    if method_name not in METHODS_REGISTRY:
        raise DeduplicError(
            f"Unknown deduplication method: '{method_name}'. "
            f"Available methods: {list(METHODS_REGISTRY.keys())}"
        )

    return METHODS_REGISTRY[method_name](corpus_draft, report_draft, target_info)