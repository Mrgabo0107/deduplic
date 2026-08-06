import sys
from pathlib import Path
import pytest

from deduplic.cli_cmds.workspace.cmd_deduplic_init_from_file import main as init_main
from deduplic.cli_cmds.workspace.cmd_deduplic_delete_all import main as delete_all_main


def test_cli_delete_all_flow(tmp_path, monkeypatch, capsys):
    # 1. Create test JSON
    json_path = tmp_path / "corpus.json"
    json_path.write_text(
        '[{"id": 1, "title": "Book A"}, {"id": 2, "title": "Book A"}]',
        encoding="utf-8",
    )

    # 2. Initialize two projects in the active workspace
    for proj_name in ["proj_one", "proj_two"]:
        monkeypatch.setattr(
            sys,
            "argv",
            ["deduplic_init", str(json_path), "title", "-n", proj_name],
        )
        init_main()
        captured = capsys.readouterr()
        assert Path(captured.out.strip()).exists()

    # 3. Test User Cancellation (answering 'n')
    monkeypatch.setattr(sys, "argv", ["deduplic_delete_all"])
    monkeypatch.setattr("builtins.input", lambda _: "n")

    with pytest.raises(SystemExit) as exc_info:
        delete_all_main()

    assert exc_info.value.code == 0
    captured_cancel = capsys.readouterr()
    assert "Delete all operation aborted by user" in captured_cancel.err

    # 4. Test Forced Deletion (-f / --force)
    monkeypatch.setattr(sys, "argv", ["deduplic_delete_all", "-f"])

    delete_all_main()

    captured_force = capsys.readouterr()
    assert "All projects deleted successfully" in captured_force.out