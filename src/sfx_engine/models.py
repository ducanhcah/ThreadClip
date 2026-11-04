"""Data models cho Rule-Based Multi-SFX Engine.

Định nghĩa SoundEvent và SceneEvents đại diện cho các sự kiện âm thanh
được gắn timestamp chính xác trong từng phân cảnh video.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SoundEvent:
    """Đặc tả chi tiết một sự kiện âm thanh (SFX) trong phân cảnh."""
    event_id: str
    scene_id: int
    anchor_text: str
    char_start: int
    char_end: int
    event_type: str
    emotion: str
    sfx_file: str | Path | None
    score: float
    priority: int
    start_time: float | None
    end_time: float | None
    volume: float
    reason: str
    timing_confidence: float = 1.0

    @property
    def sfx_path(self) -> Path | None:
        if self.sfx_file is None:
            return None
        return Path(self.sfx_file)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["sfx_file"] = str(self.sfx_file) if self.sfx_file else None
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SoundEvent":
        return cls(**data)


@dataclass
class SceneEvents:
    """Tập hợp tất cả SoundEvent diễn ra trong một phân cảnh (Scene)."""
    scene_id: int
    text: str
    events: list[SoundEvent] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scene_id": self.scene_id,
            "text": self.text,
            "events": [e.to_dict() for e in self.events],
        }

