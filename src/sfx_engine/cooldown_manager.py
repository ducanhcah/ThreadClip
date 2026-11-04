"""Cooldown Manager cho Rule-Based Multi-SFX Engine.

Quản lý khoảng cách thời gian giữa các SFX, kiểm soát mật độ âm thanh,
ngăn ngừa lặp lại âm thanh liên tiếp và lọc các sự kiện không đủ điểm.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import SoundEvent


class CooldownManager:
    """Bộ quản lý Cooldown & Mật độ SFX."""

    def __init__(
        self,
        min_gap_seconds: float = 0.60,
        max_sfx_per_sentence: int = 3,
        max_sfx_per_comment: int = 6,
        min_score: float = 65.0,
        history_size: int = 5,
    ):
        self.min_gap_seconds = min_gap_seconds
        self.max_sfx_per_sentence = max_sfx_per_sentence
        self.max_sfx_per_comment = max_sfx_per_comment
        self.min_score = min_score
        self.history_size = history_size
        self.recent_sfx: list[str] = []

    def is_repeated(self, sfx_name: str) -> bool:
        """Kiểm tra xem âm thanh này có vừa được phát gần đây không."""
        return sfx_name in self.recent_sfx

    def record_sfx(self, sfx_name: str):
        """Ghi nhận âm thanh vừa phát vào bộ nhớ đệm chống lặp."""
        self.recent_sfx.append(sfx_name)
        if len(self.recent_sfx) > self.history_size:
            self.recent_sfx.pop(0)

    def filter_and_schedule(self, candidates: list[SoundEvent]) -> list[SoundEvent]:
        """Lọc và sắp xếp danh sách candidates theo cooldown và giới hạn mật độ."""
        if not candidates:
            return []

        # 1. Lọc theo điểm tối thiểu (min_score)
        valid = [c for c in candidates if c.score >= self.min_score and c.start_time is not None]
        if not valid:
            return []

        # 2. Sắp xếp theo thứ tự thời gian xuất hiện (start_time)
        valid.sort(key=lambda x: (x.start_time or 0.0))

        # 3. Áp dụng Cooldown giữa các âm thanh (tối thiểu min_gap_seconds)
        scheduled: list[SoundEvent] = []
        last_time = -1.0

        for cand in valid:
            t = cand.start_time or 0.0
            if last_time >= 0 and (t - last_time) < self.min_gap_seconds:
                # Nếu quá sát nhau, chỉ giữ lại sự kiện có điểm score cao hơn
                if scheduled and cand.score > scheduled[-1].score:
                    scheduled[-1] = cand
                    last_time = t
                continue

            scheduled.append(cand)
            last_time = t

            if cand.sfx_path:
                self.record_sfx(cand.sfx_path.name)

            if len(scheduled) >= self.max_sfx_per_comment:
                break

        return scheduled

