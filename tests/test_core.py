from __future__ import annotations

import json
from pathlib import Path

from mv_brain_hermes.core import export_clips, export_cutlist, export_preview_manifest, search_clips
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
