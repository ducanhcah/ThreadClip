"""Text Preprocessor cho Rule-Based Multi-SFX Engine.

Nhiệm vụ:
- Chuẩn hóa văn bản tiếng Việt phục vụ phân tích ngữ cảnh.
- Tách câu và phân đoạn mệnh đề (clause segmentation).
- Bảo toàn dấu câu, emoji, tiếng lóng phục vụ nhận diện cảm xúc.
- Ánh xạ vị trí ký tự (char offset) giữa văn bản gốc và văn bản chuẩn hóa.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from text_norm import normalize_vietnamese_text


@dataclass
class ClauseSegment:
    """Đặc tả một mệnh đề hoặc câu độc lập trong văn bản."""
    index: int
    raw_text: str
    norm_text: str
    char_start: int
    char_end: int
    delimiters: str
    has_emoji: bool
    has_question: bool
    has_exclamation: bool


class TextPreprocessor:
    """Bộ tiền xử lý ngôn ngữ tiếng Việt rule-based."""

    # Tách theo các ranh giới câu hoặc mệnh đề chính
    CLAUSE_SPLIT_REGEX = re.compile(r"([.!?,;\n]+)")
    EMOJI_REGEX = re.compile(
        r"[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F2FF️‍]+",
        flags=re.UNICODE,
    )

    def __init__(self):
        pass

    def extract_emojis(self, text: str) -> list[str]:
        """Trích xuất danh sách emoji có trong văn bản."""
        return self.EMOJI_REGEX.findall(text)

    def segment_clauses(self, text: str) -> list[ClauseSegment]:
        """Tách văn bản thành danh sách các ClauseSegment có bảo toàn vị trí ký tự."""
        if not text:
            return []

        tokens = self.CLAUSE_SPLIT_REGEX.split(text)
        segments: list[ClauseSegment] = []
        cur_pos = 0
        seg_idx = 0

        # tokens chứa xen kẽ: [text_0, delim_0, text_1, delim_1, ...]
        i = 0
        while i < len(tokens):
            chunk = tokens[i]
            delim = tokens[i + 1] if i + 1 < len(tokens) else ""
            i += 2

            raw_seg = chunk.strip()
            if not raw_seg:
                cur_pos += len(chunk) + len(delim)
                continue

            # Tìm vị trí chính xác trong text gốc
            seg_start = text.find(raw_seg, cur_pos)
            if seg_start == -1:
                seg_start = cur_pos
            seg_end = seg_start + len(raw_seg)
            cur_pos = seg_end + len(delim)

            norm_seg = normalize_vietnamese_text(raw_seg)
            has_emoji = bool(self.EMOJI_REGEX.search(raw_seg))
            has_q = "?" in delim or "?" in raw_seg
            has_ex = "!" in delim or "!" in raw_seg

            segments.append(
                ClauseSegment(
                    index=seg_idx,
                    raw_text=raw_seg,
                    norm_text=norm_seg,
                    char_start=seg_start,
                    char_end=seg_end,
                    delimiters=delim,
                    has_emoji=has_emoji,
                    has_question=has_q,
                    has_exclamation=has_ex,
                )
            )
            seg_idx += 1

        return segments

    def map_anchor_position(self, full_text: str, anchor: str) -> tuple[int, int, float]:
        """Tính toán char_start, char_end và tỉ lệ vị trí tương đối (0.0 - 1.0) của anchor."""
        if not full_text or not anchor:
            return 0, 0, 0.0

        idx = full_text.lower().find(anchor.lower())
        if idx == -1:
            return 0, 0, 0.0

        end_idx = idx + len(anchor)
        rel_pos = idx / max(1, len(full_text))
        return idx, end_idx, round(rel_pos, 3)

