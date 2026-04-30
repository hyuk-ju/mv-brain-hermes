from __future__ import annotations

import json
from pathlib import Path

from mv_brain_hermes.cli import main


def test_cli_demo_search_export(tmp_path: Path, capsys) -> None:
    clips = tmp_path / "clips.json"
    assert main(["demo", "--out", str(clips)]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["clip_count"] == 8

    assert main(["search", "chorus", "--clips", str(clips), "--limit", "2"]) == 0
    search = json.loads(capsys.readouterr().out)
    assert len(search) >= 1

    out = tmp_path / "exports"
    assert main(["export-cutlist", "chorus", "--clips", str(clips), "--out", str(out)]) == 0
    export = json.loads(capsys.readouterr().out)
    assert Path(export["json"]).exists()
