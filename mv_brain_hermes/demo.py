from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def sample_clips() -> list[dict[str, Any]]:
    return [
        {"id": "demo_clip_01", "source": "demo_take_01_chorus.mp4", "source_path": "demo://demo_take_01_chorus.mp4", "source_type": "footage", "start_time": 42.1, "end_time": 47.8, "labels": ["dance", "close-up", "chorus", "high-energy", "neon"], "description": "High-energy neon close-up dance shot for the chorus hook.", "score": 0.94},
        {"id": "demo_clip_02", "source": "demo_take_02_wide.mp4", "source_path": "demo://demo_take_02_wide.mp4", "source_type": "footage", "start_time": 15.0, "end_time": 21.2, "labels": ["wide", "group", "formation", "clean"], "description": "Clean wide shot showing the full choreography formation.", "score": 0.89},
        {"id": "demo_clip_03", "source": "demo_take_03_broll.mp4", "source_path": "demo://demo_take_03_broll.mp4", "source_type": "footage", "start_time": 4.5, "end_time": 8.5, "labels": ["b-roll", "neon", "intro", "slow"], "description": "Neon detail shot that works as an intro or transition pad.", "score": 0.72},
        {"id": "demo_clip_04", "source": "demo_take_04_bridge.mp4", "source_path": "demo://demo_take_04_bridge.mp4", "source_type": "footage", "start_time": 68.0, "end_time": 75.5, "labels": ["bridge", "profile", "moody", "handheld"], "description": "Moody bridge profile shot with slower handheld movement.", "score": 0.87},
        {"id": "demo_clip_05", "source": "demo_take_05_cutaway.mp4", "source_path": "demo://demo_take_05_cutaway.mp4", "source_type": "footage", "start_time": 23.4, "end_time": 27.2, "labels": ["cutaway", "hands", "detail", "beat-hit"], "description": "Short hand-detail cutaway useful for beat accents.", "score": 0.66},
        {"id": "demo_clip_06", "source": "demo_take_06_finale.mp4", "source_path": "demo://demo_take_06_finale.mp4", "source_type": "footage", "start_time": 91.2, "end_time": 99.3, "labels": ["finale", "dance", "wide", "high-energy"], "description": "Final chorus wide shot with the strongest group energy.", "score": 0.96},
        {"id": "demo_ref_01", "source": "demo_ref_mv_01.mp4", "source_path": "demo://demo_ref_mv_01.mp4", "source_type": "reference", "start_time": 12.0, "end_time": 17.0, "labels": ["reference", "glitch", "fast-cuts", "kpop"], "description": "Reference MV segment showing fast glitch-cut pacing.", "score": 0.78},
        {"id": "demo_edit_01", "source": "demo_edit_v1.mp4", "source_path": "demo://demo_edit_v1.mp4", "source_type": "edit", "start_time": 30.0, "end_time": 36.0, "labels": ["edit", "selected", "chorus", "proven"], "description": "Previous edit segment marked as a proven chorus pattern.", "score": 0.86},
    ]


def write_demo(path: str | Path) -> dict[str, Any]:
    out = Path(path).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "mode": "mv-brain-hermes-demo",
        "description": "No-media demo clips for Hermes/MCP clip search and cut-list export.",
        "example_queries": ["neon chorus dance", "moody bridge profile", "fast reference cuts"],
        "clips": sample_clips(),
    }
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"path": str(out), "clip_count": len(payload["clips"]), "example_queries": payload["example_queries"]}
