from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _quoted(value: str) -> str:
    return json.dumps(value)


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def normalize_qdrant_point(point: Any) -> dict[str, Any]:
    """Convert an MV BRAIN Qdrant point payload into mv-brain-hermes clip JSON."""
    payload = dict(getattr(point, "payload", None) or {})
    point_id = str(getattr(point, "id", payload.get("id", payload.get("clip_id", "clip"))))
    source_path = str(payload.get("source_path") or payload.get("source") or "")
    start = _as_float(payload.get("start_time", payload.get("start", 0.0)))
    if "end_time" in payload or "end" in payload:
        end = _as_float(payload.get("end_time", payload.get("end")), start)
    else:
        end = start + _as_float(payload.get("duration", 0.0))
    duration = max(0.0, end - start)
    labels = payload.get("labels", [])
    if isinstance(labels, str):
        labels = [part.strip() for part in labels.split(",") if part.strip()]
    clip = {
        "id": point_id,
        "source": str(payload.get("source") or Path(source_path).name or point_id),
        "source_path": source_path,
        "source_type": str(payload.get("source_type") or "footage"),
        "start_time": start,
        "end_time": max(start, end),
        "duration": duration,
        "labels": list(labels),
        "description": str(payload.get("description") or payload.get("summary") or ""),
        "score": _as_float(payload.get("score", payload.get("grade_score", 0.0))),
    }
    for key in [
        "grade", "bpm", "energy_mean", "energy_relative_bucket", "scene_pacing_bucket",
        "editor_guidance", "keyframes", "global_bpm", "global_duration",
    ]:
        if key in payload:
            clip[key] = payload[key]
    return clip


def export_qdrant_snapshot(out_path: str | Path, collection: str = "clip_archive", limit: int = 1000) -> dict[str, Any]:
    """Read MV BRAIN's Qdrant clip archive and write portable clips.json metadata.

    This imports mv_brain lazily so the adapter still works as a lightweight CLI when
    the full MV BRAIN stack is not installed.
    """
    try:
        from mv_brain.config.settings import Settings
        from mv_brain.core.qdrant_manager import QdrantManager
    except Exception as exc:  # pragma: no cover - depends on optional external repo
        raise RuntimeError(
            "MV BRAIN is not importable. Install/clone the main repo first, e.g. "
            "`python3 -m pip install -e /path/to/mv-brain`, then retry."
        ) from exc

    settings = Settings()
    qdrant = QdrantManager(config=settings.qdrant)
    try:
        points, _ = qdrant.client.scroll(collection, limit=limit, with_payload=True, with_vectors=False)
    except ValueError as exc:
        message = str(exc)
        if "not found" in message.lower():
            raise RuntimeError(
                f"MV BRAIN Qdrant collection `{collection}` was not found. "
                "Run `mv-brain ingest ...` first, or use `mv-brain demo`/`mv-brain-hermes demo` for a no-provider sample."
            ) from exc
        raise
    clips = [normalize_qdrant_point(point) for point in points]
    out = Path(out_path).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "mode": "mv-brain-qdrant-snapshot",
        "collection": collection,
        "clip_count": len(clips),
        "clips": clips,
    }
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"path": str(out), "collection": collection, "clip_count": len(clips)}


def write_mcp_config_snippet(out_path: str | Path, repo_path: str, clips_path: str) -> dict[str, Any]:
    out = Path(out_path).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    text = f"""# Add this to your Hermes profile config.yaml, then restart Hermes.
mcp_servers:
  mvbrain:
    command: "python3"
    args:
      - "-m"
      - "mv_brain_hermes.mcp_server"
    env:
      MV_BRAIN_CLIPS_PATH: {_quoted(clips_path)}
      MV_BRAIN_EXPORT_ROOT: {_quoted(str(Path(repo_path).expanduser() / "exports"))}
      PYTHONPATH: {_quoted(repo_path)}
    timeout: 120
    connect_timeout: 30
"""
    out.write_text(text, encoding="utf-8")
    return {"config": str(out)}


def write_hermes_skill(out_dir: str | Path, repo_path: str, clips_path: str) -> dict[str, Any]:
    out = Path(out_dir).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    skill_path = out / "SKILL.md"
    text = f"""---
name: mv-brain-hermes
description: Use MV BRAIN Hermes Adapter to search local music-video clip metadata and render selected moments as MP4 clips.
---

# MV BRAIN Hermes Adapter

Use this skill when the user asks Hermes to work with MV BRAIN clip memory or export selected moments as MP4 clips.

## Local paths

- Adapter repo: `{repo_path}`
- Default clips metadata: `{clips_path}`

## Safe defaults

- Read local metadata first. Do not run real media rendering unless the user asks for MP4 output.
- MP4 rendering is opt-in with `--render` and only reads `source_path` values from the clip metadata.
- If the footage is not on the same machine as Hermes, ask for or use a synced local folder first. Google Drive/rclone/NAS/server folders are input transport, not embedding providers.
- Provider keys and Qdrant belong to the main `mv-brain` stack; this adapter can consume a portable `clips.json` snapshot.

## Common commands

```bash
cd {repo_path}
python3 -m pip install -e '.[mcp,test]'
mv-brain-hermes list --clips {clips_path} --limit 10
mv-brain-hermes search "chorus dance" --clips {clips_path} --limit 5
mv-brain-hermes export-pack "chorus dance" --clips {clips_path} --out exports/chorus-pack
mv-brain-hermes export-clips "chorus dance" --clips {clips_path} --out exports/chorus-mp4 --limit 3 --render
```

## If the main MV BRAIN repo is installed

Create a portable metadata snapshot from the Qdrant clip archive:

```bash
cd {repo_path}
mv-brain-hermes snapshot-qdrant --out data/mvbrain/clips.json --limit 1000
```

Then use that snapshot as `--clips` or set `MV_BRAIN_CLIPS_PATH` for MCP.
"""
    skill_path.write_text(text, encoding="utf-8")
    return {"skill": str(skill_path)}


def write_quickstart(out_path: str | Path, repo_url: str, repo_path: str, clips_path: str) -> dict[str, Any]:
    out = Path(out_path).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    text = f"""# MV BRAIN Hermes Adapter quickstart

```bash
git clone {repo_url} {repo_path}
cd {repo_path}
python3 -m pip install -e '.[mcp,test]'

# No-media demo: metadata only, no real MP4 files are rendered
mv-brain-hermes demo --out data/demo/clips.json
mv-brain-hermes export-clips "chorus" --clips data/demo/clips.json --out exports/demo-metadata --limit 3

# Remote footage example: sync source MP4 files onto the working machine first
rclone copy gdrive:mv-footage ./videos

# If the main mv-brain stack is installed, ingest the synced MP4 files there,
# then snapshot its Qdrant clip archive for Hermes/MCP search
cd ../mv-brain
mv-brain ingest ./videos/*.mp4

cd {repo_path}
mv-brain-hermes snapshot-qdrant --out {clips_path}

# MP4 output when source_path points to real local media
mv-brain-hermes export-clips "chorus" --clips {clips_path} --out exports/chorus-mp4 --limit 3 --render
```
"""
    out.write_text(text, encoding="utf-8")
    return {"quickstart": str(out)}


def init_hermes_files(out_dir: str | Path, repo_path: str, clips_path: str, repo_url: str = "https://github.com/hyuk-ju/mv-brain-hermes.git") -> dict[str, Any]:
    out = Path(out_dir).expanduser()
    skill = write_hermes_skill(out / "skill", repo_path=repo_path, clips_path=clips_path)
    config = write_mcp_config_snippet(out / "mcp_config.yaml", repo_path=repo_path, clips_path=clips_path)
    quickstart = write_quickstart(out / "QUICKSTART.md", repo_url=repo_url, repo_path=repo_path, clips_path=clips_path)
    return {**skill, "mcp_config": config["config"], **quickstart}
