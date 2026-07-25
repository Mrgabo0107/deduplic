from .keep_all import keep_all
from .keep_largest import keep_largest
from .keep_shortest import keep_shortest
from .keep_newest import keep_newest
from .keep_oldest import keep_oldest
from .keep_first import keep_first
from .keep_last import keep_last

METHODS_REGISTRY = {
    "keep_all": keep_all,
    "keep_largest": keep_largest,
    "keep_shortest": keep_shortest,
    "keep_newest": keep_newest,
    "keep_oldest": keep_oldest,
    "keep_first": keep_first,
    "keep_last": keep_last,
}

def apply_method(method_name: str, corpus_draft: dict, report_draft: dict, target_info: dict):
    """
    Función envoltorio principal de la carpeta methods/.
    Valida el método y delega la ejecución al módulo correspondiente.
    """
    if method_name not in METHODS_REGISTRY:
        raise ValueError(f"Unknown deduplication method: '{method_name}'. Available: {list(METHODS_REGISTRY.keys())}")
    
    return METHODS_REGISTRY[method_name](corpus_draft, report_draft, target_info)