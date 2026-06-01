def deduplicate(data: list[dict], keys_to_check: list[str] | tuple[str, ...]) -> list[dict]:
    """
    Removes absolute duplicate dictionaries from a list based on specific keys.
    
    Performance: O(n) using a set of tuples for lookups.
    """
    seen = set()
    unique_data = []

    for item in data:
        # Extraemos los valores de las llaves seleccionadas en orden.
        # Si la llave no existe en el diccionario, usamos None para evitar que explote.
        features = tuple(item.get(key) for key in keys_to_check)
        
        # Si este conjunto de valores no ha sido visto, guardamos el item original
        if features not in seen:
            seen.add(features)
            unique_data.append(item)
            
    return unique_data