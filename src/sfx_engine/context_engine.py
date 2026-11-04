"""Context Engine cho Rule-Based Multi-SFX Engine.

Phân tích 3 phạm vi ngữ cảnh:
1. Local context: Từ ngữ xung quanh điểm nhấn.
2. Sentence context: Ý nghĩa toàn bộ câu (dấu câu, thái độ).
3. Comment context: Lịch sử các bình luận trước đó trong bài viết.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ContextState:
    """Trạng thái ngữ cảnh tích lũy qua các bình luận."""
    has_prior_failure: bool = False
    has_prior_warning: bool = False
    prior_emotions: list[str] = field(default_factory=list)
    recent_events: list[str] = field(default_factory=list)


class ContextEngine:
    """Bộ máy phân tích ngữ cảnh liên kết bình luận (Cross-comment Context Engine)."""

    def __init__(self):
        self.state = ContextState()

    def reset(self):
        """Khởi tạo lại trạng thái ngữ cảnh (ví dụ khi sang bài viết mới)."""
        self.state = ContextState()

    def update_history(self, emotion: str, event_type: str):
        """Ghi nhận sự kiện vừa xảy ra vào lịch sử ngữ cảnh."""
        self.state.prior_emotions.append(emotion)
        self.state.recent_events.append(event_type)
        if emotion in ("Failure", "Warning") or event_type in ("Failure", "Warning"):
            self.state.has_prior_failure = True

    def evaluate_context(
        self,
        current_text: str,
        detected_emotion: str,
        detected_type: str,
    ) -> tuple[float, str]:
        """Đánh giá điểm cộng/trừ ngữ cảnh (Context Match Score: 0.0 - 20.0).

        Phát hiện tương phản trào phúng (Sarcasm contrast):
        Nếu các câu trước có thất bại/hỏng hóc ("sập nguồn", "toang", "mất tiền"),
        mà câu hiện tại dùng từ tích cực ("tuyệt vời", "quá đã", "thông minh", "đỉnh cao"),
        thì ngữ cảnh xác nhận đây là MỈA MAI / CHÂM BIẾM (Sarcasm) với điểm cộng tối đa!
        """
        score = 10.0
        reason = "Ngữ cảnh câu bình thường"

        # Tương phản mỉa mai qua lịch sử bình luận
        if self.state.has_prior_failure:
            positive_words = ["tuyệt vời", "quá đã", "xuất sắc", "thông minh", "đỉnh cao", "giỏi", "uy tín"]
            if any(w in current_text.lower() for w in positive_words):
                score = 20.0
                reason = "Phát hiện châm biếm tương phản với sự cố ở bình luận trước đó"
                return score, reason

        # Khớp ngữ cảnh liên hoàn (chuỗi drama / hài hước)
        if self.state.prior_emotions and self.state.prior_emotions[-1] == detected_emotion:
            score += 5.0
            reason = f"Cộng hưởng cảm xúc [{detected_emotion}] tiếp nối câu trước"

        return min(20.0, score), reason

