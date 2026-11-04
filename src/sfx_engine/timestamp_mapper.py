"""Timestamp Mapper & Audio Alignment cho Rule-Based Multi-SFX Engine.

Nhiệm vụ:
- Phân biệt rõ ràng giữa vị trí ký tự (char position), vị trí từ (word position),
  và mốc thời gian âm thanh thực tế (audio timestamp).
- Ánh xạ giữa: Văn bản gốc <-> Văn bản chuẩn hóa <-> Audio Transcript <-> Timestamp.
- Tự động tính toán Timing Confidence (độ tin cậy):
  * 1.0: Khớp chính xác ranh giới câu/từ (Word/Sentence Boundary từ TTS).
  * 0.85: Nội suy tỷ lệ từ bên trong câu có boundary xác thực.
  * 0.60: Ước lượng dựa trên độ dài âm tiết và thời lượng tổng.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class TimestampResult:
    """Kết quả ánh xạ thời gian cho một từ khóa/cụm từ neo."""
    timestamp: float
    confidence: float
    method: str
    sentence_idx: int


class TimestampMapper:
    """Bộ ánh xạ vị trí từ khóa sang mốc thời gian âm thanh (Timeline Alignment)."""

    def align_anchor_time(
        self,
        full_text: str,
        anchor_text: str,
        sentence_boundaries: list[dict[str, Any]] | None = None,
        total_duration: float = 3.0,
    ) -> TimestampResult:
        """Căn chỉnh thời điểm phát âm thanh của anchor_text."""
        anchor_clean = anchor_text.strip().lower()
        if not anchor_clean:
            return TimestampResult(timestamp=0.15, confidence=0.5, method="default", sentence_idx=0)

        # 1. ƯU TIÊN 1 & 2: Dựa trên Speech-to-Text / Edge TTS Sentence Boundaries
        if sentence_boundaries and len(sentence_boundaries) > 0:
            for s_idx, b in enumerate(sentence_boundaries):
                b_text = b.get("text", "").lower()
                b_offset = float(b.get("offset", 0.0))
                b_dur = float(b.get("duration", 1.0))

                if anchor_clean in b_text:
                    # Nếu từ khóa nằm ở đầu câu
                    char_idx = b_text.find(anchor_clean)
                    if char_idx <= 2:
                        return TimestampResult(
                            timestamp=round(max(0.0, b_offset), 2),
                            confidence=1.0,
                            method="sentence_start_boundary",
                            sentence_idx=s_idx,
                        )

                    # Nội suy vị trí từ bên trong câu thoại
                    words = b_text.split()
                    anchor_words = anchor_clean.split()
                    target_word_idx = 0
                    for w_idx, w in enumerate(words):
                        if anchor_words[0] in w:
                            target_word_idx = w_idx
                            break

                    ratio = target_word_idx / max(1, len(words))
                    # Canh mốc âm thanh: b_offset + ratio * b_dur (có offset nhẹ 0.1s trước khi nói)
                    calc_t = b_offset + (ratio * b_dur)
                    return TimestampResult(
                        timestamp=round(max(0.0, calc_t), 2),
                        confidence=0.85,
                        method="word_interpolated_boundary",
                        sentence_idx=s_idx,
                    )

        # 2. ƯU TIÊN 3: Ước lượng dựa trên âm tiết (Syllable estimation)
        char_idx = full_text.lower().find(anchor_clean)
        if char_idx != -1:
            preceding_text = full_text[:char_idx]
            preceding_syllables = len(re.findall(r"\w+", preceding_text))
            total_syllables = max(1, len(re.findall(r"\w+", full_text)))

            ratio = preceding_syllables / total_syllables
            est_t = ratio * total_duration
            # Đảm bảo không sát nút cuối audio
            est_t = min(est_t, max(0.0, total_duration - 0.5))
            return TimestampResult(
                timestamp=round(max(0.0, est_t), 2),
                confidence=0.60,
                method="syllable_estimation",
                sentence_idx=0,
            )

        # 3. Fallback
        return TimestampResult(
            timestamp=0.15,
            confidence=0.40,
            method="fallback",
            sentence_idx=0,
        )

