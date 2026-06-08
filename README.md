# Deduplic

A lightweight, robust, and framework-agnostic Python library and CLI tool designed to identify and remove duplicate records from JSON data based on user-defined keys. 

It features an intelligent, fault-tolerant input adapter that handles multiple data formats seamlessly and includes a built-in Streamlit GUI for interactive data inspection.

---

## ✨ Features

- **Agnostic & Reusable:** Works with any JSON data structure, completely independent of specific backend pipelines.
- **Smart Input Adapter:** Accepts a mix of file paths (`str` or `Path`), pure Python dictionaries, numerical indexed dictionaries (`{"0": {...}, "1": {...}}`), or lists of these formats.
- **Fault-Tolerant Ingestion:** Gracefully skips corrupt records or invalid formats using non-blocking system warnings instead of crashing.
- **Dynamic Key Selection:** Choose one or multiple keys (e.g., `title`, `author`) to define the exact deduplication criteria.
- **Dual-Interface:** Use it as a Python module inside larger software architectures or as a native terminal command (CLI).
- **Streamlit Web UI:** Includes a beautiful dashboard to upload, analyze, and download deduplicated results visually.

---

el algoritmo de similaridad trabaja con un porcentaje llamado tolerance que servira para definir que tanto se parece un texto a otro en diferentes filtros. 

 - Si el ratio de la longitud entre los dos textos es menor que la tolerancia se dira que los textos son diferentes, esto quiere decir que si a un texto se le anade informacion se considerara que es diferetne del original en cuanto ka informacion anadida sobrepase (1 - t) donde t es la tolerancia. Por ejemplo con una tolerancia de 

el algoritmo usa TI IDF y similaridad por coseno, este metodo sirve para encontrar y comparar conjuntos de palabras claves lo cual sirve como prueba de contexto sobre el ratio de palabras claves encontradas en el contexto

Se espera que diferencias entre contenidos impliquen 



## 🚀 Installation

You can install the library directly into your project's virtual environment using any of the following private/local methods:

### 1. From a local folder (Development Mode)
```bash
pip install -e .