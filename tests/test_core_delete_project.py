from pathlib import Path
import pytest

from deduplic import (
    DeduplicError,
    DeduplicFileNotFoundError,
    deduplic_delete_project,
    deduplic_init_from_file,
    deduplic_set_workspace_dir,
)


def test_core_delete_project_safety_and_execution(tmp_path):
    # Setup
    custom_ws = tmp_path / "custom_ws"
    custom_ws.mkdir()
    deduplic_set_workspace_dir(custom_ws)

    dummy_json = tmp_path / "corpus.json"
    dummy_json.write_text(
        '[{"id": 1, "title": "Book A"}, {"id": 2, "title": "Book A"}]',
        encoding="utf-8",
    )

    proj_path = deduplic_init_from_file(
        file_path=dummy_json, keys=["title"], name="proj_to_remove"
    )
    assert proj_path is not None
    proj_path = Path(proj_path)

    # 1. PRUEBA DE SEGURIDAD: Sin confirmación debe lanzar error
    with pytest.raises(DeduplicError) as exc_info:
        deduplic_delete_project(proj_path, confirm=False)

    assert "confirm=True" in str(exc_info.value)
    assert proj_path.exists()

    # 2. PRUEBA DE EJECUCIÓN: Con confirm=True debe eliminarlo
    deduplic_delete_project(proj_path, confirm=True)
    assert not proj_path.exists()


def test_core_delete_project_not_found(tmp_path):
    non_existent = tmp_path / "fake_project"

    with pytest.raises(DeduplicFileNotFoundError):
        deduplic_delete_project(non_existent, confirm=True)