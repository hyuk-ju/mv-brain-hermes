from __future__ import annotations

from pathlib import Path

import pytest

from mv_brain_hermes.bridge import write_mcp_config_snippet, write_quickstart
from mv_brain_hermes.core import ensure_within_root, render_enabled_for_mcp


def test_ensure_within_root_rejects_paths_outside_export_root(tmp_path: Path) -> None:
    root = tmp_path / "exports"
    outside = tmp_path / "outside"

    with pytest.raises(ValueError, match="outside allowed root"):
        ensure_within_root(outside, root)


def test_ensure_within_root_allows_paths_inside_export_root(tmp_path: Path) -> None:
    root = tmp_path / "exports"
    allowed = ensure_within_root(root / "pack", root)

    assert allowed == (root / "pack").resolve()


def test_mcp_render_requires_explicit_environment_opt_in(monkeypatch) -> None:
    monkeypatch.delenv("MV_BRAIN_ENABLE_RENDER", raising=False)
    assert render_enabled_for_mcp() is False

    monkeypatch.setenv("MV_BRAIN_ENABLE_RENDER", "1")
    assert render_enabled_for_mcp() is True


def test_mcp_config_yaml_escapes_generated_path_values(tmp_path: Path) -> None:
    snippet = write_mcp_config_snippet(
        tmp_path / "mcp.yaml",
        repo_path='/repo/with"quote',
        clips_path='/repo/data/clips"bad.json',
    )

    text = Path(snippet["config"]).read_text(encoding="utf-8")
    assert '/repo/with\\"quote' in text
    assert '/repo/data/clips\\"bad.json' in text
    assert '/repo/with"quote' not in text
    assert '/repo/data/clips"bad.json' not in text


def test_generated_quickstart_keeps_no_media_demo_metadata_only(tmp_path: Path) -> None:
    quickstart = write_quickstart(
        tmp_path / "QUICKSTART.md",
        repo_url="https://example.invalid/repo.git",
        repo_path="/repo",
        clips_path="/repo/data/mvbrain/clips.json",
    )

    text = Path(quickstart["quickstart"]).read_text(encoding="utf-8")
    demo_block = text.split("# Remote footage example", maxsplit=1)[0]
    assert "--render" not in demo_block
    assert "metadata only" in demo_block
