"""
Deduplic Global Configuration Module.
Location: src/deduplic/config.py

This file defines the project's neutral configuration layer and MUST NOT import
any internal project modules.
"""
from pathlib import Path
from dataclasses import dataclass, field
from typing import List

PACKAGE_DIR = Path(__file__).parent.resolve()

@dataclass
class Settings:
    # Workspace & Directory Settings
    projects_dir: Path = field(
        default_factory=lambda: Path(__file__).resolve().parents[2] / "projects"
    )

    # 1. Algorithm Parameters
    default_threshold: float = 0.8
    default_match_keys: List[str] = field(default_factory=lambda: [])

    # 2. Official Resolution Methods
    resolution_methods: List[str] = field(
        default_factory=lambda: [
            "keep_all",
            "keep_first",
            "keep_last",
            "keep_oldest",
            "keep_newest",
            "keep_largest",
            "keep_shortest",
            "merge",
        ]
    )
    default_resolution_method: str = "keep_all"

    # 3. Memory and Batch Limits
    max_recommended_records: int = 10000
    default_batch_size: int = 1000

    # 4. Visual Diff Settings (Merge)
    diff_color_added: str = "#d4edda"      # Light green
    diff_color_removed: str = "#f8d7da"    # Light red


settings = Settings()