from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .models import Clip, clip_from_dict


def load_clips(path: str | Path | None = None) -> list[Clip]:
    selected = Path(path or os.getenv("MV_BRAIN_CLIPS_PATH", "./data/demo/clips.json")).expanduser()
    payload = json.loads(selected.read_text(encoding="utf-8"))
    raw_clips = payload.get("clips", payload) if isinstance(payload, dict) else payload
    if not isinstance(raw_clips, list):
        raise ValueError("clips file must be a list or an object with a clips array")
    return [clip_from_dict(item) for item in raw_clips if isinstance(item, dict)]


def search_clips(query: str, clips_path: str | Path | None = None, limit: int = 10, source_type: str | None = None) -> list[dict[str, Any]]:
    terms = [term.lower() for term in query.split() if term.strip()]
    clips = load_clips(clips_path)
    ranked: list[tuple[float, Clip]] = []
    for clip in clips:
        if source_type and clip.source_type != source_type:
            continue
        text = clip.searchable_text()
        term_hits = sum(1 for term in terms if term in text)
        label_hits = sum(2 for term in terms for label in clip.labels if term in label.lower())
        if terms and term_hits == 0 and label_hits == 0:
            continue
        rank = term_hits + label_hits + clip.score
        ranked.append((rank, clip))
    ranked.sort(key=lambda item: item[0], reverse=True)
    return [{"rank_score": round(rank, 3), **clip.to_dict()} for rank, clip in ranked[:limit]]


def list_clips(clips_path: str | Path | None = None, limit: int = 50, source_type: str | None = None) -> list[dict[str, Any]]:
    clips = load_clips(clips_path)
    if source_type:
        clips = [clip for clip in clips if clip.source_type == source_type]
    return [clip.to_dict() for clip in clips[:limit]]


def _slug(value: str) -> str:
    allowed = []
    for ch in value.lower():
        if ch.isalnum():
            allowed.append(ch)
        elif ch in {" ", "-", "_", "."}:
            allowed.append("-")
    return "".join(allowed).strip("-") or "clip"


def write_cutlist(clips: list[dict[str, Any]], out_dir: str | Path, query: str) -> dict[str, Any]:
    out = Path(out_dir).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "cutlist.json"
    csv_path = out / "cutlist.csv"
    readme_path = out / "README.md"
    payload = {"query": query, "clip_count": len(clips), "clips": clips}
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "source", "source_path", "start_time", "end_time", "duration", "labels", "description", "score"])
        writer.writeheader()
        for clip in clips:
            writer.writerow({
                "id": clip.get("id", ""),
                "source": clip.get("source", ""),
                "source_path": clip.get("source_path", ""),
                "start_time": clip.get("start_time", ""),
                "end_time": clip.get("end_time", ""),
                "duration": clip.get("duration", ""),
                "labels": ",".join(clip.get("labels", [])),
                "description": clip.get("description", ""),
                "score": clip.get("score", ""),
            })
    readme_path.write_text("\n".join([
        f"# Cut list: {query}",
        "",
        f"Selected clips: {len(clips)}",
        "",
        "Import the CSV into a spreadsheet or use the JSON as agent-readable context.",
        "Use `export-clips --render` only when `source_path` points at real local video files.",
        "",
    ]), encoding="utf-8")
    return {"out_dir": str(out), "json": str(json_path), "csv": str(csv_path), "readme": str(readme_path), "clip_count": len(clips)}


def export_cutlist(query: str, clips_path: str | Path | None, out_dir: str | Path, limit: int = 10, source_type: str | None = None) -> dict[str, Any]:
    matches = search_clips(query=query, clips_path=clips_path, limit=limit, source_type=source_type)
    return write_cutlist(matches, out_dir, query)


def ffmpeg_cut_command(clip: dict[str, Any], output_path: str | Path, reencode: bool = True) -> list[str]:
    ffmpeg = os.getenv("MV_BRAIN_FFMPEG", "ffmpeg")
    cmd = [ffmpeg, "-y", "-ss", str(clip["start_time"]), "-to", str(clip["end_time"]), "-i", str(clip["source_path"])]
    if reencode:
        cmd += ["-c:v", "libx264", "-c:a", "aac", "-movflags", "+faststart"]
    else:
        cmd += ["-c", "copy"]
    cmd.append(str(output_path))
    return cmd


def export_clips(query: str, clips_path: str | Path | None, out_dir: str | Path, limit: int = 5, render: bool = False, reencode: bool = True) -> dict[str, Any]:
    matches = search_clips(query=query, clips_path=clips_path, limit=limit)
    manifest = write_cutlist(matches, out_dir, query)
    out = Path(out_dir).expanduser()
    rendered: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    if render:
        if not shutil.which(os.getenv("MV_BRAIN_FFMPEG", "ffmpeg")):
            raise RuntimeError("ffmpeg not found; install ffmpeg or omit render=true")
        for index, clip in enumerate(matches, start=1):
            source_path = Path(str(clip.get("source_path", ""))).expanduser()
            if not source_path.exists():
                skipped.append({"id": clip.get("id"), "reason": "source_path does not exist", "source_path": str(source_path)})
                continue
            output_path = out / f"{index:03d}_{_slug(str(clip.get('id', 'clip')))}.mp4"
            cmd = ffmpeg_cut_command({**clip, "source_path": str(source_path)}, output_path, reencode=reencode)
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            rendered.append({"id": clip.get("id"), "path": str(output_path)})
    manifest.update({"rendered": rendered, "skipped": skipped, "render": render})
    (out / "render_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest


def _write_clip_pack_readme(out: Path, query: str, clip_count: int, duration: float) -> Path:
    readme_path = out / "README.md"
    readme_path.write_text("\n".join([
        f"# Agent-readable clip pack: {query}",
        "",
        "This folder is a universal handoff package for MV BRAIN search results.",
        "It is designed to be useful even when Final Cut Pro is not available.",
        "",
        "## Contents",
        "",
        "- `cutlist.csv` — spreadsheet-friendly edit list for editors.",
        "- `cutlist.json` — structured context for agents, scripts, and MCP clients.",
        "- `preview_manifest.json` — rough-cut timeline order before any render step.",
        "- `render_manifest.json` — created by `export-clips`; records render/skipped results.",
        "",
        "## For editors",
        "",
        f"- Query: `{query}`",
        f"- Selected clips: {clip_count}",
        f"- Preview timeline duration: {duration:.3f}s",
        "- Open `cutlist.csv` in a spreadsheet or hand it to Premiere, DaVinci, CapCut, or a manual edit workflow.",
        "",
        "## For agents",
        "",
        "- Read `cutlist.json` for ranked clip metadata and source timecodes.",
        "- Read `preview_manifest.json` for timeline offsets and sequence order.",
        "- Use `source_path`, `start_time`, and `end_time` only as explicit local-media instructions.",
        "",
        "## Rendering",
        "",
        "MP4 rendering is opt-in. Run `mv-brain-hermes export-clips ... --render` only when `source_path` points at allowed local video files.",
        "Without `--render`, this pack is metadata-only and does not touch media.",
        "",
    ]), encoding="utf-8")
    return readme_path


def export_preview_manifest(query: str, clips_path: str | Path | None, out_dir: str | Path, limit: int = 8) -> dict[str, Any]:
    matches = search_clips(query=query, clips_path=clips_path, limit=limit)
    out = Path(out_dir).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    total = 0.0
    timeline = []
    for clip in matches:
        item = {"timeline_start": round(total, 3), "timeline_end": round(total + float(clip.get("duration", 0.0)), 3), **clip}
        timeline.append(item)
        total += float(clip.get("duration", 0.0))
    path = out / "preview_manifest.json"
    path.write_text(json.dumps({"query": query, "duration": round(total, 3), "clips": timeline}, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"manifest": str(path), "clip_count": len(timeline), "duration": round(total, 3)}


def export_clip_pack(query: str, clips_path: str | Path | None, out_dir: str | Path, limit: int = 8) -> dict[str, Any]:
    """Write the universal editor/agent handoff pack for a search query."""
    out = Path(out_dir).expanduser()
    cutlist = export_cutlist(query=query, clips_path=clips_path, out_dir=out, limit=limit)
    preview = export_preview_manifest(query=query, clips_path=clips_path, out_dir=out, limit=limit)
    readme = _write_clip_pack_readme(out, query=query, clip_count=cutlist["clip_count"], duration=float(preview["duration"]))
    return {
        "out_dir": str(out),
        "query": query,
        "clip_count": cutlist["clip_count"],
        "cutlist_json": cutlist["json"],
        "cutlist_csv": cutlist["csv"],
        "preview_manifest": preview["manifest"],
        "readme": str(readme),
        "duration": preview["duration"],
        "render": False,
    }
