import json
from pathlib import Path


def load_draft(project_path: Path) -> tuple[dict, list]:
    draft_dir = project_path / ".draft"
    if not draft_dir.exists():
        raise FileNotFoundError(f"No active .draft/ session found in '{project_path}'. Did you run deduplic_init?")
    with open(draft_dir / "corpus.json", "r", encoding="utf-8") as f:
        corpus = json.load(f)
    with open(draft_dir / "report.json", "r", encoding="utf-8") as f:
        report = json.load(f)
    return corpus, report


def save_draft(project_path: Path, corpus: dict, report: list) -> None:
    draft_dir = project_path / ".draft"
    with open(draft_dir / "corpus.json", "w", encoding="utf-8") as f:
        json.dump(corpus, f, indent=4, ensure_ascii=False)
    with open(draft_dir / "report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4, ensure_ascii=False)