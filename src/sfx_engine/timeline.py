"""Timeline Management cho Rule-Based Multi-SFX Engine.

Quản lý dòng thời gian của phân cảnh và toàn bộ video:
- Kiểm tra tính hợp lệ của timestamp.
- Ngăn ngừa xung đột thời gian giữa các track.
- Xác định thời lượng cảnh tối ưu.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import SoundEvent


class SceneTimeline:
    """Quản lý trục thời gian cho một phân cảnh."""

    def __init__(self, scene_id: int, total_duration: float):
        self.scene_id = scene_id
        self.total_duration = total_duration
        self.events: list[SoundEvent] = []

    def add_event(self, event: SoundEvent) -> bool:
        """Thêm một SoundEvent vào timeline sau khi kiểm tra hợp lệ."""
        if event.start_time is None or event.start_time < 0.0:
            return False
        if event.start_time >= self.total_duration:
            return False

        self.events.append(event)
        return True

    def validate_and_sort(self) -> list[SoundEvent]:
        """Sắp xếp sự kiện theo trình tự thời gian."""
        self.events.sort(key=lambda e: (e.start_time or 0.0))
        return self.events

