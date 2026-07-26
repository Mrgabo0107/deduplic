import random

def get_test_corpus(target_indices: list[int], corpus: dict, noise: int = 0) -> dict:
    """
    Crea un subcorpus bien indexado (0, 1, 2, ...) a partir de una lista de índices.
    
    :param target_indices: Lista de IDs enteros que se desean extraer.
    :param corpus: Diccionario original del corpus { "0": {...}, "1": {...}, ... }.
    :param noise: Cantidad de registros aleatorios adicionales a incluir (opcional).
    :return: Un nuevo diccionario subcorpus con índices secuenciales '0', '1', ...
    """
    # Convertir índices buscados a str para coincidir con las claves del corpus
    target_str_keys = [str(idx) for idx in target_indices]
    
    # 1. Identificar claves válidas que existen en el corpus
    selected_keys = [k for k in target_str_keys if k in corpus]
    
    # 2. Manejar el parámetro noise (registros aleatorios adicionales)
    if noise > 0:
        # Filtrar los registros restantes (los que NO fueron seleccionados inicialmente)
        remaining_keys = [k for k in corpus.keys() if k not in selected_keys]
        
        # Calcular el número real de elementos de ruido a añadir
        num_noise = min(len(remaining_keys), noise)
        
        if num_noise > 0:
            # Seleccionar registros aleatorios sin repetición
            noise_keys = random.sample(remaining_keys, num_noise)
            selected_keys.extend(noise_keys)

    # 3. Re-ordenar y re-indexar secuencialmente en el nuevo subcorpus (0, 1, 2, ...)
    subcorpus = {}
    for new_idx, old_key in enumerate(selected_keys):
        # Copiamos el contenido del registro (puedes usar .copy() si prefieres evitar referencias mutables)
        subcorpus[str(new_idx)] = corpus[old_key].copy() if isinstance(corpus[old_key], dict) else corpus[old_key]

    return subcorpus