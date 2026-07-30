# import argparse
# import json
# import shutil
# from pathlib import Path
# from deduplic.core.input_adapter import normalize_input
# from deduplic.core.do_reports import do_reports


# def deduplic_init(
#     raw_input: any,
#     keys: list,
#     name: str = None,
#     threshold: float = 0.8,
# ) -> Path | None:
#     """
#     Normalizes the input, creates an incremental workspace under projects/,
#     generates the raw report, and returns the absolute path to the project folder.
#     """

#     # 1. Normalize the raw input using the input adapter
#     normalized_records = normalize_input(raw_input)

#     # 2. Generate the pure report directly from in-memory normalized records
#     report_data = do_reports(
#         data=normalized_records,
#         keys_to_check=keys,
#         threshold=threshold,
#     )

#     if not report_data:
#         print(f"No duplications found in the corpus with threshold {threshold}. Project creation aborted.")
#         return None

#     # 3. Create the 'projects' directory if it does not exist
#     projects_root = Path("projects").resolve()
#     projects_root.mkdir(parents=True, exist_ok=True)

#     # 4. Determine the project folder name (auto-increment)
#     if name is None:
#         counter = 1
#         while (projects_root / str(counter)).exists():
#             counter += 1
#         project_name = str(counter)
#     else:
#         if not (projects_root / name).exists():
#             project_name = name
#         else:
#             counter = 2
#             while (projects_root / f"{name}_{counter}").exists():
#                 counter += 1
#             project_name = f"{name}_{counter}"

#     project_path = projects_root / project_name 
#     path_original = project_path / "original"
#     path_original.mkdir(parents=True, exist_ok=True)

#     # 5. Save the normalized corpus as corpus.json ("Boite" format)
#     corpus_boite = {
#         str(i): record
#         for i, record in enumerate(normalized_records)
#     }

#     corpus_file = path_original / "corpus.json"

#     with open(corpus_file, "w", encoding="utf-8") as f:
#         json.dump(
#             corpus_boite,
#             f,
#             indent=4,
#             ensure_ascii=False,
#         )

#     report_file = path_original / "report.json"

#     with open(report_file, "w", encoding="utf-8") as f:
#         json.dump(
#             report_data,
#             f,
#             indent=4,
#             ensure_ascii=False,
#         )

#     metadata = {
#         "threshold": threshold,
#         "keys_checked": keys,
#         "total_records": len(normalized_records),
#         "status": "in progress"
#     }
    
#     metadata_file = project_path / "metadata.json"
#     with open(metadata_file, "w", encoding="utf-8") as f:
#         json.dump(
#             metadata,
#             f,
#             indent=4,
#             ensure_ascii=False,
#         )

#     return project_path


# def init_workspace(project_path: Path) -> None:
#     """
#     Sets the files in original/ as the current active state in the project root
#     and creates an initial .draft/ directory with a working copy.
#     """
#     path_original = project_path / "original"
#     path_draft = project_path / ".draft"

#     # 1. Ensure .draft directory exists
#     path_draft.mkdir(parents=True, exist_ok=True)

#     # 2. Copy original files to root (current state) AND to .draft/
#     for filename in ["corpus.json", "report.json"]:
#         source_file = path_original / filename
        
#         # Copy to Root (Current State)
#         shutil.copy2(source_file, project_path / filename)
        
#         # Copy to .draft/ (Working Draft)
#         shutil.copy2(source_file, path_draft / filename)


# def _parser():
#     def _valid_threshold(value: str) -> float:
#         """Valida que el threshold sea un float entre 0.0 y 1.0."""
#         try:
#             val = float(value)
#         except ValueError:
#             raise argparse.ArgumentTypeError(f"'{value}' is not a valid floating-point number")

#         if not (0.0 <= val <= 1.0):
#             raise argparse.ArgumentTypeError(f"Threshold must be between 0.0 and 1.0 (got {val})")

#         return val

#     parser = argparse.ArgumentParser(
#         description="""Normalizes a JSON corpus of records into a unified format and generates
#         a duplicate detection report by comparing specified fields, with adjustable similarity thresholds.

#         Can also be used as a Python library:
#             from deduplic import deduplic_init
#         allowing direct integration into other applications."""
#     )

#     parser.add_argument(
#         "path_to_corpus",
#         type=str,
#         help="Path to the corpus JSON file.",
#     )

#     parser.add_argument(
#         "keys",
#         nargs="+",
#         help="Fields to check for duplication (e.g. title, author).",
#     )

#     parser.add_argument(
#         "-n",
#         "--project_name",
#         type=str,
#         required=False,
#         help="Name of the project.",
#     )

#     parser.add_argument(
#         "-t",
#         "--threshold",
#         type=_valid_threshold,
#         default=0.8,
#         required=False,
#         help="Similarity threshold for deduplication (default: 0.8).",
#     )

#     args = parser.parse_args()
#     return args


# def main():
#     args = _parser()
#     # Load the JSON corpus passed through the CLI
#     corpus_path = Path(args.path_to_corpus).resolve()

#     with open(corpus_path, "r", encoding="utf-8") as f:
#         raw_json_data = json.load(f)

#     # Run normalization and report generation using the in-memory object
#     created_folder = deduplic_init(
#         raw_input=raw_json_data,
#         keys=args.keys,
#         name=args.project_name,
#         threshold=args.threshold,
#     )

#     if created_folder is None:
#         return

#     # Set original as current state and create draft directory
#     init_workspace(created_folder)

#     # Print the resulting project path
#     print(created_folder)


# if __name__ == "__main__":
#     main()

#     # organizar con init_from_file exponer init e init from file y documentar

import argparse
import logging

from ..core.deduplic import deduplic_init_from_file

logger = logging.getLogger(__name__)


def _parser():
    def _valid_threshold(value: str) -> float:
        """Validate that the threshold its a float between 0.0 y 1.0."""
        try:
            val = float(value)
        except ValueError:
            raise argparse.ArgumentTypeError(f"'{value}' is not a valid floating-point number")

        if not (0.0 <= val <= 1.0):
            raise argparse.ArgumentTypeError(f"Threshold must be between 0.0 and 1.0 (got {val})")

        return val

    parser = argparse.ArgumentParser(
        description="""Normalizes a JSON corpus of records into a unified format and generates
        a duplicate detection report by comparing specified fields, with adjustable similarity thresholds.

        Can also be used as a Python library:
            from deduplic import deduplic_init, deduplic_init_from_file
        allowing direct integration into other applications."""
    )

    parser.add_argument(
        "path_to_corpus",
        type=str,
        help="Path to the corpus JSON file.",
    )

    parser.add_argument(
        "keys",
        nargs="+",
        help="Fields to check for duplication (e.g. title, author).",
    )

    parser.add_argument(
        "-n",
        "--project_name",
        type=str,
        required=False,
        help="Name of the project.",
    )

    parser.add_argument(
        "-t",
        "--threshold",
        type=_valid_threshold,
        default=0.8,
        required=False,
        help="Similarity threshold for deduplication (default: 0.8).",
    )

    parser.add_argument(
        "-p",
        "--projects_dir",
        type=str,
        required=False,
        default=None,
        help="Directory where project folders will be created.",
    )

    args = parser.parse_args()
    return args


def main():
    args = _parser()

    created_folder = deduplic_init_from_file(
        file_path=args.path_to_corpus,
        keys=args.keys,
        name=args.project_name,
        threshold=args.threshold,
        projects_dir=args.projects_dir,
    )

    if created_folder is None:
        logger.info("Project creation skipped (no duplicates found).")
        return

    # init_workspace(created_folder)
    
    # Única salida estándar para scripting en la CLI (mantiene comportamiento anterior)
    print(created_folder)


if __name__ == "__main__":
    main()