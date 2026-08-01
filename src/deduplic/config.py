"""
Deduplic Global Configuration Module.
Location: src/deduplic/config.py

This file defines the project's neutral configuration layer and MUST NOT import
any internal project modules.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List
from platformdirs import user_data_dir
import logging

logger = logging.getLogger(__name__)


def resolve_workspace_dir(custom_path: Path | str | None = None) -> Path:
    """Resolves the target workspace directory Path without side-effects."""
    if custom_path:
        try:
            base_target = Path(custom_path).resolve()
            return (
                base_target
                if base_target.name == "deduplic_projects"
                else base_target / "deduplic_projects"
            )
        except Exception as e:
            logger.warning(
                f"Failed to resolve custom workspace path '{custom_path}': {e}. "
                "Falling back to OS default directory."
            )

    return Path(user_data_dir("deduplic")) / "deduplic_projects"


@dataclass
class Settings:
    """Global configuration settings for the deduplic library."""

    # Workspace & Directory Settings initialized via helper resolver
    projects_dir: Path = field(default_factory=resolve_workspace_dir)

    # 1. Algorithm Parameters
    default_threshold: float = 0.8
    default_match_keys: List[str] = field(default_factory=list)

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
            "merge",  # Special case: handled via create_pending_merge
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