from __future__ import annotations

"""MCP server for Hermes Agent.

Run with:
    python3 -m mv_brain_hermes.mcp_server
"""

import os
from typing import Any

try:
    from mcp.server.fastmcp import FastMCP
except Exception as exc:  # pragma: no cover - exercised only without optional dep
    raise SystemExit("MCP support requires `python3 -m pip install -e '.[mcp]'`") from exc

from .bridge import export_qdrant_snapshot as _export_qdrant_snapshot
from .core import export_clip_pack as _export_clip_pack
from .core import export_clips as _export_clips
from .core import export_cutlist as _export_cutlist
from .core import export_preview_manifest as _export_preview_manifest
from .core import ensure_within_root as _ensure_within_root
from .core import list_clips as _list_clips
from .core import render_enabled_for_mcp as _render_enabled_for_mcp
from .core import search_clips as _search_clips
from .demo import write_demo as _write_demo

mcp = FastMCP("mvbrain")


def _default_clips(clips_path: str | None = None) -> str | None:
    return clips_path or os.getenv("MV_BRAIN_CLIPS_PATH")


def _export_root() -> str:
    return os.getenv("MV_BRAIN_EXPORT_ROOT", "./exports")


def _safe_write_path(path: str) -> str:
    return str(_ensure_within_root(path, _export_root()))


@mcp.tool()
def write_demo(out_path: str = "data/demo/clips.json") -> dict[str, Any]:
    """Write a no-media demo metadata file."""
    return _write_demo(_safe_write_path(out_path))


@mcp.tool()
def list_clips(clips_path: str | None = None, limit: int = 50, source_type: str | None = None) -> list[dict[str, Any]]:
    """List clips from a metadata file."""
    return _list_clips(_default_clips(clips_path), limit=limit, source_type=source_type)


@mcp.tool()
def search_clips(query: str, clips_path: str | None = None, limit: int = 10, source_type: str | None = None) -> list[dict[str, Any]]:
    """Search local clip metadata by keywords/labels/descriptions."""
    return _search_clips(query=query, clips_path=_default_clips(clips_path), limit=limit, source_type=source_type)


@mcp.tool()
def export_cutlist(query: str, out_dir: str, clips_path: str | None = None, limit: int = 10, source_type: str | None = None) -> dict[str, Any]:
    """Export matching clips as JSON/CSV cut lists."""
    return _export_cutlist(query=query, clips_path=_default_clips(clips_path), out_dir=_safe_write_path(out_dir), limit=limit, source_type=source_type)


@mcp.tool()
def export_clip_pack(query: str, out_dir: str, clips_path: str | None = None, limit: int = 8) -> dict[str, Any]:
    """Export JSON/CSV cut list, preview manifest, and README as an agent/editor handoff pack."""
    return _export_clip_pack(query=query, clips_path=_default_clips(clips_path), out_dir=_safe_write_path(out_dir), limit=limit)


@mcp.tool()
def export_clips(query: str, out_dir: str, clips_path: str | None = None, limit: int = 5, render: bool = False) -> dict[str, Any]:
    """Export matching clips as cut lists and optionally render MP4 clips."""
    if render and not _render_enabled_for_mcp():
        raise ValueError("MCP MP4 rendering requires MV_BRAIN_ENABLE_RENDER=1")
    return _export_clips(query=query, clips_path=_default_clips(clips_path), out_dir=_safe_write_path(out_dir), limit=limit, render=render)


@mcp.tool()
def export_preview_manifest(query: str, out_dir: str, clips_path: str | None = None, limit: int = 8) -> dict[str, Any]:
    """Write a rough-cut preview manifest for matching clips."""
    return _export_preview_manifest(query=query, clips_path=_default_clips(clips_path), out_dir=_safe_write_path(out_dir), limit=limit)


@mcp.tool()
def snapshot_qdrant(out_path: str = "data/mvbrain/clips.json", collection: str = "clip_archive", limit: int = 1000) -> dict[str, Any]:
    """Export the main MV BRAIN Qdrant clip archive to portable clips.json metadata. Requires main mv-brain and Qdrant."""
    return _export_qdrant_snapshot(out_path=_safe_write_path(out_path), collection=collection, limit=limit)


if __name__ == "__main__":
    mcp.run()
