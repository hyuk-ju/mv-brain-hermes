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

from .core import export_clips as _export_clips
from .core import export_cutlist as _export_cutlist
from .core import export_preview_manifest as _export_preview_manifest
from .core import list_clips as _list_clips
from .core import search_clips as _search_clips
from .demo import write_demo as _write_demo

mcp = FastMCP("mvbrain")


def _default_clips(clips_path: str | None = None) -> str | None:
    return clips_path or os.getenv("MV_BRAIN_CLIPS_PATH")


@mcp.tool()
def write_demo(out_path: str = "data/demo/clips.json") -> dict[str, Any]:
    """Write a no-media demo metadata file."""
    return _write_demo(out_path)


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
    return _export_cutlist(query=query, clips_path=_default_clips(clips_path), out_dir=out_dir, limit=limit, source_type=source_type)


@mcp.tool()
def export_clips(query: str, out_dir: str, clips_path: str | None = None, limit: int = 5, render: bool = False) -> dict[str, Any]:
    """Export matching clips as cut lists and optionally render MP4 clips."""
    return _export_clips(query=query, clips_path=_default_clips(clips_path), out_dir=out_dir, limit=limit, render=render)


@mcp.tool()
def export_preview_manifest(query: str, out_dir: str, clips_path: str | None = None, limit: int = 8) -> dict[str, Any]:
    """Write a rough-cut preview manifest for matching clips."""
    return _export_preview_manifest(query=query, clips_path=_default_clips(clips_path), out_dir=out_dir, limit=limit)


if __name__ == "__main__":
    mcp.run()
