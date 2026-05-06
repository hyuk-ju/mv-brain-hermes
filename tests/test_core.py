from __future__ import annotations

import csv
import json
from pathlib import Path

from mv_brain_hermes.core import export_clip_pack, export_clips, export_cutlist, export_preview_manifest, search_clips, write_cutlist
from mv_brain_hermes.demo import write_demo


def test_demo_search_and_cutlist(tmp_path: Path) -> None:
    clips_path = tmp_path / "clips.json"
    result = write_demo(clips_path)
    assert result["clip_count"] == 8

    matches = search_clips("neon chorus dance", clips_path, limit=3)
    assert matches
    assert matches[0]["id"] == "demo_clip_01"

    out = export_cutlist("chorus", clips_path, tmp_path / "exports", limit=4)
    assert Path(out["json"]).exists()
    assert Path(out["csv"]).exists()
    payload = json.loads(Path(out["json"]).read_text(encoding="utf-8"))
    assert payload["clip_count"] >= 1


def test_export_clips_without_render_is_manifest_only(tmp_path: Path) -> None:
    clips_path = tmp_path / "clips.json"
    write_demo(clips_path)
    out = export_clips("dance", clips_path, tmp_path / "exports", limit=2, render=False)
    assert out["render"] is False
    assert out["rendered"] == []
    assert Path(tmp_path / "exports" / "render_manifest.json").exists()


def test_preview_manifest(tmp_path: Path) -> None:
    clips_path = tmp_path / "clips.json"
    write_demo(clips_path)
    out = export_preview_manifest("high energy", clips_path, tmp_path / "preview", limit=2)
    assert out["clip_count"] >= 1
    assert out["duration"] > 0


def test_export_clip_pack_writes_agent_and_editor_handoff(tmp_path: Path) -> None:
    clips_path = tmp_path / "clips.json"
    write_demo(clips_path)

    out = export_clip_pack("chorus", clips_path, tmp_path / "pack", limit=3)

    assert out["clip_count"] >= 1
    assert Path(out["cutlist_json"]).exists()
    assert Path(out["cutlist_csv"]).exists()
    assert Path(out["preview_manifest"]).exists()
    assert Path(out["readme"]).exists()

    readme = Path(out["readme"]).read_text(encoding="utf-8")
    assert "Agent-readable clip pack" in readme
    assert "For editors" in readme
    assert "For agents" in readme
    assert "MP4 rendering is opt-in" in readme

    preview = json.loads(Path(out["preview_manifest"]).read_text(encoding="utf-8"))
    assert preview["query"] == "chorus"
    assert preview["clips"]


def test_cutlist_csv_neutralizes_spreadsheet_formulas(tmp_path: Path) -> None:
    clips = [{
        "id": "=cmd",
        "source": "+source.mp4",
        "source_path": "@/tmp/source.mp4",
        "start_time": " \t=1+1",
        "end_time": "\r+2+2",
        "duration": "\n-3+3",
        "labels": ["-danger"],
        "description": "=HYPERLINK(\"https://example.invalid\")",
        "score": "@SUM(1,1)",
    }]

    out = write_cutlist(clips, tmp_path / "exports", "danger")
    with Path(out["csv"]).open(encoding="utf-8", newline="") as handle:
        row = next(csv.DictReader(handle))

    assert row["id"] == "'=cmd"
    assert row["source"] == "'+source.mp4"
    assert row["source_path"] == "'@/tmp/source.mp4"
    assert row["start_time"] == "' \t=1+1"
    assert row["end_time"] == "'\r+2+2"
    assert row["duration"] == "'\n-3+3"
    assert row["labels"] == "'-danger"
    assert row["description"].startswith("'=HYPERLINK")
    assert row["score"] == "'@SUM(1,1)"
