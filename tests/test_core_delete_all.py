from pathlib import Path
import pytest

from deduplic import (
    DeduplicError,
    DeduplicFileNotFoundError,
    deduplic_delete_all,
    deduplic_init_from_file,
    deduplic_set_workspace_dir,
)


def test_core_delete_all_safety_and_execution(tmp_path):
    # Setup: Create a custom test workspace and a project inside it
    custom_ws = tmp_path / "custom_workspace"
    custom_ws.mkdir()
    deduplic_set_workspace_dir(custom_ws)

    # Create a JSON with 2 duplicate elements to force project creation
    dummy_json = tmp_path / "corpus.json"
    dummy_json.write_text(
        '[{"id": 1, "title": "Test Book"}, {"id": 2, "title": "Test Book"}]',
        encoding="utf-8",
    )

    proj_path = deduplic_init_from_file(
        file_path=dummy_json, keys=["title"], name="proj_to_delete"
    )

    # Now proj_path should not be None
    assert proj_path is not None
    assert Path(proj_path).exists()

    # 1. SECURITY TEST: Must fail if confirm=False
    with pytest.raises(DeduplicError) as exc_info:
        deduplic_delete_all(confirm=False)
    assert "confirm=True" in str(exc_info.value)
    assert Path(proj_path).exists()  # The project must NOT have been deleted

    # 2. EXECUTION TEST: Delete with confirm=True
    deduplic_delete_all(confirm=True)

    # The project no longer exists
    assert not Path(proj_path).exists()

    # The workspace root folder still exists but is empty
    resolved_workspace = custom_ws / "deduplic_projects"
    assert resolved_workspace.exists()
    assert len(list(resolved_workspace.iterdir())) == 0


def test_core_delete_all_non_existent_workspace(tmp_path):
    # Set a workspace to a path that DOES NOT exist
    non_existent = tmp_path / "ghost_path"
    deduplic_set_workspace_dir(non_existent)

    # Must raise DeduplicFileNotFoundError
    with pytest.raises(DeduplicFileNotFoundError):
        deduplic_delete_all(confirm=True)