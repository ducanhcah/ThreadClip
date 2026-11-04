"""Pattern Detector cho Rule-Based Multi-SFX Engine.

Sử dụng Regex, từ điển cấu trúc câu và từ khóa tiếng Việt để nhận diện:
- Humor (Hài hước, cười, punchline)
- Sarcasm (Mỉa mai, tưởng A nhưng B, châm biếm)
- Plot Twist / Transition (Đảo chiều, ai ngờ, hóa ra)
- Failure (Toang, thất bại, sập nguồn, chết máy)
- Surprise (Bất ngờ, sốc, ủa, hả)
- Negation / Exception (Phủ định để tránh chèn SFX sai)
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = ROOT / "config"


@dataclass
class PatternMatchResult:
    """Kết quả khớp một pattern mẫu câu."""
    pattern_id: str
    category: str
    emotion: str
    event_type: str
    anchor_text: str
    char_start: int
    char_end: int
    base_score: float
    priority: int
    reason: str


@dataclass
class ExceptionResult:
    """Kết quả phát hiện phủ định / trường hợp ngoại lệ."""
    is_suppressed: bool
    penalty: float
    reason: str


class PatternDetector:
    """Bộ nhận diện mẫu câu quy tắc (Rule-based Pattern Detector)."""

    def __init__(self, config_dir: Path | None = None):
        self.config_dir = config_dir or CONFIG_DIR
        self.humor_patterns: list[dict[str, Any]] = self._load_json("humor_patterns.json", [])
        self.sarcasm_patterns: list[dict[str, Any]] = self._load_json("sarcasm_patterns.json", [])
        self.exception_patterns: list[dict[str, Any]] = self._load_json("exception_patterns.json", [])
        self.slang_dict: dict[str, Any] = self._load_json("slang_dictionary.json", {})

        # Biên dịch sẵn các Regex để tối ưu hiệu năng
        self._compiled_humor = [
            (p, re.compile(p["regex"], re.IGNORECASE)) for p in self.humor_patterns if "regex" in p
        ]
        self._compiled_sarcasm = [
            (p, re.compile(p["regex"], re.IGNORECASE)) for p in self.sarcasm_patterns if "regex" in p
        ]
        self._compiled_exceptions = [
            (p, re.compile(p["regex"], re.IGNORECASE)) for p in self.exception_patterns if "regex" in p
        ]

    def _load_json(self, filename: str, default_val: Any) -> Any:
        path = self.config_dir / filename
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return default_val

    def check_negations_and_exceptions(self, text: str, category: str) -> ExceptionResult:
        """Kiểm tra xem câu có chứa từ ngữ phủ định triệt tiêu SFX không.

        Ví dụ:
        - "Không buồn cười chút nào" -> suppress Humor/Comedy
        - "Đừng có cười" -> suppress Humor/Comedy
        - "Không phải hết cứu" -> suppress Failure/Comedy
        - "Tưởng hài nhưng chẳng vui" -> suppress Humor/Comedy
        """
        for item, regex in self._compiled_exceptions:
            m = regex.search(text)
            if m:
                suppress_cats = item.get("suppress_categories", [])
                if category in suppress_cats:
                    return ExceptionResult(
                        is_suppressed=True,
                        penalty=float(item.get("penalty", 40.0)),
                        reason=item.get("reason", "Phát hiện phủ định ngữ cảnh"),
                    )

        return ExceptionResult(is_suppressed=False, penalty=0.0, reason="")

    def detect_patterns(self, text: str) -> list[PatternMatchResult]:
        """Quét và nhận diện tất cả pattern có trong câu văn bản."""
        matches: list[PatternMatchResult] = []

        # 1. Quét Sarcasm / Plot Twist
        for item, regex in self._compiled_sarcasm:
            for m in regex.finditer(text):
                anchor = m.group(0)
                matches.append(
                    PatternMatchResult(
                        pattern_id=item["id"],
                        category=item["category"],
                        emotion=item["emotion"],
                        event_type=item["event_type"],
                        anchor_text=anchor,
                        char_start=m.start(),
                        char_end=m.end(),
                        base_score=float(item.get("base_score", 20.0)),
                        priority=int(item.get("priority", 2)),
                        reason=f"Khớp cấu trúc đảo chiều / châm biếm ({item['id']})",
                    )
                )

        # 2. Quét Humor / Comedy
        for item, regex in self._compiled_humor:
            for m in regex.finditer(text):
                anchor = m.group(0)
                # Kiểm tra xem có bị phủ định không
                neg = self.check_negations_and_exceptions(text, item["category"])
                if neg.is_suppressed:
                    continue

                matches.append(
                    PatternMatchResult(
                        pattern_id=item["id"],
                        category=item["category"],
                        emotion=item["emotion"],
                        event_type=item["event_type"],
                        anchor_text=anchor,
                        char_start=m.start(),
                        char_end=m.end(),
                        base_score=float(item.get("base_score", 20.0)),
                        priority=int(item.get("priority", 2)),
                        reason=f"Khớp mẫu câu hài hước / punchline ({item['id']})",
                    )
                )

        # 3. Quét từ khóa trong Slang Dictionary
        emotions_dict = self.slang_dict.get("emotions", {})
        for emo_name, kw_list in emotions_dict.items():
            for kw in kw_list:
                # Kiểm tra từ khóa nguyên vẹn
                pattern_kw = r"\b" + re.escape(kw) + r"\b" if re.match(r"^\w+$", kw) else re.escape(kw)
                for m in re.finditer(pattern_kw, text, re.IGNORECASE):
                    anchor = m.group(0)

                    # Kiểm tra phủ định
                    neg = self.check_negations_and_exceptions(text, emo_name)
                    if neg.is_suppressed:
                        continue

                    # Mapping category
                    cat = emo_name
                    if emo_name == "Warning":
                        cat = "Failure"

                    matches.append(
                        PatternMatchResult(
                            pattern_id=f"slang_{emo_name}_{kw}",
                            category=cat,
                            emotion=emo_name,
                            event_type="KeywordMatch",
                            anchor_text=anchor,
                            char_start=m.start(),
                            char_end=m.end(),
                            base_score=18.0,
                            priority=3,
                            reason=f"Khớp từ khóa cảm xúc '{kw}' [{emo_name}]",
                        )
                    )

        return matches

