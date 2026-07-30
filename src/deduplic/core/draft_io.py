import json
import logging
from pathlib import Path
from typing import Any

from ..exceptions import DeduplicError

logger = logging.getLogger(__name__)


def load_draft(project_path: Path | str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """
    Loads the current state of corpus.json and report.json from the project's .draft/ directory.

    Args:
        project_path: Path or src/deduplic/cli_cmds/cmd_deduplic_delete_project.pystring pointing to the project root directory.

    Returns:
        A tuple containing (corpus_dict, report_list).
    """
    project_path = Path(project_path).resolve()
    draft_dir = project_path / ".draft"

    if not draft_dir.exists():
        raise FileNotFoundError(
            f"No active .draft/ session found in '{project_path}'. Did you run 'deduplic_init'?"
        )

    corpus_file = draft_dir / "corpus.json"
    report_file = draft_dir / "report.json"

    if not corpus_file.exists() or not report_file.exists():
        raise FileNotFoundError(
            f"Draft files missing in '{draft_dir}'. Required: 'corpus.json' and 'report.json'."
        )

    try:
        with open(corpus_file, "r", encoding="utf-8") as f:
            corpus = json.load(f)
        with open(report_file, "r", encoding="utf-8") as f:
            report = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        logger.error(f"Failed to load draft from '{draft_dir}': {e}")
        raise DeduplicError(f"Could not load draft session for '{project_path.name}': {e}") from e

    return corpus, report


def save_draft(
    project_path: Path | str,
    corpus: dict[str, Any],
    report: list[dict[str, Any]],
) -> None:
    """
    Persists the updated corpus and report in RAM back into the project's .draft/ directory.

    Args:
        project_path: Path or string pointing to the project root directory.
        corpus: Dictionary containing the updated corpus records.
        report: List containing the updated cluster reports.
    """
    project_path = Path(project_path).resolve()
    draft_dir = project_path / ".draft"
    draft_dir.mkdir(parents=True, exist_ok=True)

    try:
        with open(draft_dir / "corpus.json", "w", encoding="utf-8") as f:
            json.dump(corpus, f, indent=4, ensure_ascii=False)
        with open(draft_dir / "report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=4, ensure_ascii=False)
    except OSError as e:
        logger.error(f"Failed to save draft to '{draft_dir}': {e}")
        raise DeduplicError(f"Could not save draft session for '{project_path.name}': {e}") from e