from pathlib import Path
import time

from deduplic import (
    deduplic_init_from_file,
    deduplic_purge_workspace,
    deduplic_set_workspace_dir,
)
from deduplic.config import settings

TIME_TO_SEE = 0.0

def test_full_workspace_lifecycle_and_safety(tmp_path):
    # 1. Create a dummy JSON file for testing
    dummy_json = tmp_path / "dummy_corpus.json"
    dummy_json.write_text(
        '[{"id": 1, "title": "Test Book", "author": "John"}, '
        '{"id": 2, "title": "Test Book", "author": "John"}]',
        encoding="utf-8",
    )

    # -------------------------------------------------------------
    # PHASE 1: Default system workspace
    # -------------------------------------------------------------
    deduplic_set_workspace_dir(None)
    default_dir = settings.projects_dir

    project_path = deduplic_init_from_file(
        file_path=dummy_json, keys=["title"], name="test_proj_default"
    )
    assert project_path is not None
    assert Path(project_path).exists()
    assert str(default_dir) in str(project_path)

    # Purge the default directory (requires confirm=True)
    time.sleep(TIME_TO_SEE)
    deduplic_purge_workspace(confirm=True)
    assert not Path(project_path).exists()

    # -------------------------------------------------------------
    # PHASE 2: Custom directory in CWD
    # -------------------------------------------------------------
    custom_cwd_dir = Path.cwd() / "test_deduplic"
    custom_cwd_dir.mkdir(exist_ok=True)

    try:
        deduplic_set_workspace_dir(custom_cwd_dir)

        proj_custom = deduplic_init_from_file(
            file_path=dummy_json, keys=["title"], name="test_proj_custom"
        )
        assert Path(proj_custom).exists()

        time.sleep(TIME_TO_SEE)
        # Purge internal projects
        deduplic_purge_workspace(confirm=True)
        assert not Path(proj_custom).exists()

    finally:
        resolved_custom = custom_cwd_dir / "deduplic_projects"
        if resolved_custom.exists():
            resolved_custom.rmdir()
        if custom_cwd_dir.exists():
            custom_cwd_dir.rmdir()

    # -------------------------------------------------------------
    # PHASE 3: Isolation and protection of adjacent user files
    # -------------------------------------------------------------
    user_custom_dir = Path.cwd() / "my_personal_folder"
    user_custom_dir.mkdir(exist_ok=True)

    # User's personal file next to the deduplic workspace
    user_file = user_custom_dir / "user_file.txt"
    user_file.write_text("Important user work", encoding="utf-8")

    try:
        deduplic_set_workspace_dir(user_custom_dir)

        proj_deduplic = deduplic_init_from_file(
            file_path=dummy_json, keys=["title"], name="proj_in_user_dir"
        )
        assert Path(proj_deduplic).exists()

        # Run deduplic purge
        time.sleep(TIME_TO_SEE)
        deduplic_purge_workspace(confirm=True)

        # Security verification:
        # 1. The internal deduplic project was deleted
        assert not Path(proj_deduplic).exists()

        # 2. The user's file that was NEXT TO the workspace was untouched
        assert user_file.exists()
        assert user_file.read_text(encoding="utf-8") == "Important user work"

    finally:
        # Manually clean up the test environment
        if user_file.exists():
            user_file.unlink()

        deduplic_projects_folder = user_custom_dir / "deduplic_projects"
        if deduplic_projects_folder.exists():
            deduplic_projects_folder.rmdir()

        if user_custom_dir.exists():
            user_custom_dir.rmdir()

        # Restore the workspace to default
        deduplic_set_workspace_dir(None)