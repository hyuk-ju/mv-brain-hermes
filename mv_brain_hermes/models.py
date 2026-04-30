from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class Clip:
    id: str
    source: str
    source_path: str
    start_time: float
    end_time: float
    labels: list[str] = field(default_factory=list)
    description: str = ""
    score: float = 0.0
    source_type: str = "footage"
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def duration(self) -> float:
        return max(0.0, self.end_time - self.start_time)

    @property
    def is_renderable(self) -> bool:
        return self.source_path and Path(self.source_path).expanduser().exists()

    def searchable_text(self) -> str:
        return " ".join([
            self.id,
            self.source,
            self.source_type,
            self.description,
            " ".join(self.labels),
        ]).lower()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "source_path": self.source_path,
            "source_type": self.source_type,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "labels": self.labels,
            "description": self.description,
            "score": self.score,
            "renderable": self.is_renderable,
            **self.extra,
        }


def clip_from_dict(raw: dict[str, Any]) -> Clip:
    start = float(raw.get("start_time", raw.get("start", 0.0)) or 0.0)
    if "end_time" in raw:
        end = float(raw["end_time"])
    elif "end" in raw:
        end = float(raw["end"])
    else:
        end = start + float(raw.get("duration", 0.0) or 0.0)
    labels = raw.get("labels", [])
    if isinstance(labels, str):
        labels = [part.strip() for part in labels.split(",") if part.strip()]
    known = {"id", "source", "source_path", "start_time", "start", "end_time", "end", "duration", "labels", "description", "score", "grade_score", "source_type"}
    extra = {k: v for k, v in raw.items() if k not in known}
    return Clip(
        id=str(raw.get("id") or raw.get("clip_id") or "clip"),
        source=str(raw.get("source") or Path(str(raw.get("source_path", "unknown"))).name),
        source_path=str(raw.get("source_path") or raw.get("path") or raw.get("source") or ""),
        start_time=start,
        end_time=max(start, end),
        labels=list(labels),
        description=str(raw.get("description") or raw.get("summary") or ""),
        score=float(raw.get("score", raw.get("grade_score", 0.0)) or 0.0),
        source_type=str(raw.get("source_type") or "footage"),
        extra=extra,
    )
