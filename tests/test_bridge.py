from __future__ import annotations

import json
from pathlib import Path

from mv_brain_hermes.bridge import normalize_qdrant_point, write_hermes_skill, write_mcp_config_snippet
from mv_brain_hermes.cli import main


class FakePoint:
    def __init__(self, point_id: str, payload: dict):
        self.id = point_id
        self.payload = payload


def test_normalize_qdrant_point_keeps_mv_brain_payload_fields() -> None:
    clip = normalize_qdrant_point(FakePoint("abc123", {
        "source_path": "/video/A001.mp4",
        "start_time": 10.5,
        "end_time": 14.0,
        "labels": ["chorus", "dance"],
        "description": "high energy chorus",
        "grade_score": 0.91,
        "source_type": "footage",
        "bpm": 128,
    }))

    assert clip["id"] == "abc123"
    assert clip["source"] == "A001.mp4"
    assert clip["source_path"] == "/video/A001.mp4"
    assert clip["start_time"] == 10.5
    assert clip["end_time"] == 14.0
    assert clip["duration"] == 3.5
    assert clip["score"] == 0.91
    assert clip["labels"] == ["chorus", "dance"]
    assert clip["bpm"] == 128


def test_write_hermes_skill_and_mcp_snippet(tmp_path: Path) -> None:
    skill = write_hermes_skill(tmp_path / "skill", repo_path="/repo", clips_path="/repo/data/demo/clips.json")
    snippet = write_mcp_config_snippet(tmp_path / "mcp.yaml", repo_path="/repo", clips_path="/repo/data/demo/clips.json")

    skill_text = Path(skill["skill"]).read_text(encoding="utf-8")
    assert "mv-brain-hermes" in skill_text
    assert "export-clips" in skill_text
    assert "Google Drive/rclone/NAS/server folders" in skill_text
    assert "--render" in skill_text

    snippet_text = Path(snippet["config"]).read_text(encoding="utf-8")
    assert "mcp_servers:" in snippet_text
    assert "MV_BRAIN_CLIPS_PATH" in snippet_text


def test_snapshot_qdrant_missing_mvbrain_dependency_reports_install_hint(monkeypatch, tmp_path: Path) -> None:
    import builtins
    from mv_brain_hermes.bridge import export_qdrant_snapshot

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name.startswith("mv_brain"):
            raise ModuleNotFoundError("no mv_brain")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    try:
        export_qdrant_snapshot(tmp_path / "clips.json")
    except RuntimeError as exc:
        assert "Install/clone the main repo" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected RuntimeError")


def test_cli_init_hermes_writes_onboarding_files(tmp_path: Path, capsys) -> None:
    out = tmp_path / "onboarding"
    assert main(["init-hermes", "--out", str(out), "--repo-path", "/repo", "--clips", "/repo/clips.json"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert Path(payload["skill"]).exists()
    assert Path(payload["mcp_config"]).exists()
    assert Path(payload["quickstart"]).exists()
