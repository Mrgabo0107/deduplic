import sys
from pathlib import Path
import pytest

from deduplic.cli_cmds.workspace.cmd_deduplic_init_from_file import main as init_main
from deduplic.cli_cmds.workspace.cmd_deduplic_delete_project import main as delete_project_main


def test_cli_delete_project_flow(tmp_path, monkeypatch, capsys):
    # 1. Crear corpus ficticio
    json_path = tmp_path / "corpus.json"
    json_path.write_text(
        '[{"id": 1, "title": "Book A"}, {"id": 2, "title": "Book A"}]',
        encoding="utf-8",
    )

    proj_name = "target_project"

    # 2. Inicializar proyecto
    monkeypatch.setattr(
        sys,
        "argv",
        ["deduplic_init", str(json_path), "title", "-n", proj_name],
    )
    init_main()
    captured_init = capsys.readouterr()
    proj_path = Path(captured_init.out.strip())
    assert proj_path.exists()

    # 3. Simular cancelación por el usuario
    monkeypatch.setattr(sys, "argv", ["deduplic_delete_project", proj_name])
    monkeypatch.setattr("builtins.input", lambda _: "n")

    with pytest.raises(SystemExit) as exc_info:
        delete_project_main()

    assert exc_info.value.code == 0
    captured_cancel = capsys.readouterr()
    assert "operation aborted by user" in captured_cancel.err
    assert proj_path.exists()

    # 4. Borrado con bandera --force (-f)
    monkeypatch.setattr(sys, "argv", ["deduplic_delete_project", proj_name, "-f"])
    delete_project_main()

    captured_force = capsys.readouterr()
    assert f"Project '{proj_name}' deleted successfully." in captured_force.out
    assert not proj_path.exists()


def test_cli_delete_project_non_existent(monkeypatch, capsys):
    # Intentar borrado de proyecto inexistente
    monkeypatch.setattr(sys, "argv", ["deduplic_delete_project", "non_existent_proj", "-f"])

    with pytest.raises(SystemExit) as exc_info:
        delete_project_main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Deduplic Error:" in captured.err