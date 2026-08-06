import sys
from pathlib import Path
import pytest

from deduplic.cli_cmds.workspace.cmd_deduplic_init_from_file import main as init_main
from deduplic.cli_cmds.workspace.cmd_deduplic_purge_workspace import main as purge_main


def test_cli_init_and_purge_flow(tmp_path, monkeypatch, capsys):
    # 1. Create a dummy JSON test file
    json_path = tmp_path / "corpus.json"
    json_path.write_text(
        '[{"id": 1, "title": "CLI Book"}, {"id": 2, "title": "CLI Book"}]',
        encoding="utf-8",
    )

    # 2. Simulate terminal arguments for deduplic_init
    test_args_init = [
        "deduplic_init",
        str(json_path),
        "title",
        "-n",
        "cli_project_test",
    ]
    monkeypatch.setattr(sys, "argv", test_args_init)

    # Run init main
    init_main()

    # Capture stdout/stderr output
    captured_init = capsys.readouterr()
    project_path_str = captured_init.out.strip()

    # Init verification
    assert "cli_project_test" in project_path_str
    assert Path(project_path_str).exists()

    # 3. Simulate purge CANCELLED by the user (answering 'n')
    monkeypatch.setattr(sys, "argv", ["deduplic_purge_workspace"])
    monkeypatch.setattr("builtins.input", lambda _: "n")

    with pytest.raises(SystemExit) as exc_info:
        purge_main()

    # It should exit with code 0 and display the cancellation message on stderr
    assert exc_info.value.code == 0
    captured_cancel = capsys.readouterr()
    assert "Purge aborted by user" in captured_cancel.err
    assert Path(project_path_str).exists()  # The project must NOT have been deleted

    # 4. Simulate forced purge (-f / --force)
    monkeypatch.setattr(sys, "argv", ["deduplic_purge_workspace", "-f"])

    purge_main()

    # Forced purge verification
    captured_force = capsys.readouterr()
    assert "Workspace purged successfully" in captured_force.out
    assert not Path(project_path_str).exists()  # The project should now be deleted
