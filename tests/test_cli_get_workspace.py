import sys
from pathlib import Path

from deduplic import deduplic_set_workspace_dir
from deduplic.cli_cmds.workspace.cmd_deduplic_get_workspace import main as get_workspace_main


def test_cli_get_workspace(tmp_path, monkeypatch, capsys):
    # 1. Configure a custom test workspace
    custom_ws = tmp_path / "custom_cli_workspace"
    custom_ws.mkdir()
    deduplic_set_workspace_dir(custom_ws)

    expected_target = (custom_ws / "deduplic_projects").resolve()

    # 2. Simulate NORMAL execution (Before creating the folder)
    monkeypatch.setattr(sys, "argv", ["deduplic_get_workspace"])
    get_workspace_main()

    captured = capsys.readouterr()
    assert str(expected_target) in captured.out
    assert "Status: DOES NOT EXIST YET" in captured.out

    # 3. Physically create the folder and query again
    expected_target.mkdir(parents=True, exist_ok=True)
    get_workspace_main()

    captured_after = capsys.readouterr()
    assert str(expected_target) in captured_after.out
    assert "Status: EXISTS" in captured_after.out

    # 4. Test the --quiet (-q) option for scripts
    monkeypatch.setattr(sys, "argv", ["deduplic_get_workspace", "-q"])
    get_workspace_main()

    captured_quiet = capsys.readouterr()
    assert captured_quiet.out.strip() == str(expected_target)