"""Hệ thống Tự động Phân tích Lời thoại & Đề xuất Sound Effects (SFX) Thông minh.

Tuân thủ nghiêm ngặt 6 nguyên tắc cốt lõi:
  1. ANALYZE THE SPEECH: Hiểu toàn bộ ngữ cảnh, câu chuyện, mối quan hệ giữa các câu.
  2. DETECT EMOTIONAL CONTEXT: Curiosity, Surprise, Humor, Suspense, Serious, Warning, Excitement, Sadness, Neutral.
  3. IDENTIFY OPPORTUNITIES: Hook, Emphasis, Comedy (Punchline), Transition, Suspense.
  4. SOUND EFFECT SELECTION: Whoosh, Pop, Notification, Cinematic Impact, Error, Cartoon SFX,...
  5. PRECISE TIMING: Canh nhịp chính xác theo Speech-to-Text / Edge TTS Sentence & Word Boundaries.
  6. NATURAL SOUND DESIGN: Giọng nói là số 1, không che khuất, mật độ cân bằng, chống lặp lại.
"""
from __future__ import annotations

import json
import random
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from text_norm import normalize_vietnamese_text

# ─── Bảng phân loại cảm xúc & Từ khóa ngữ cảnh tiếng Việt ───────────────────
_EMOTION_RULES: list[tuple[str, list[str], float]] = [
    # Cảm xúc 1: Warning (Cảnh báo, nguy hiểm, toang)
    ("Warning", [
        "toang", "thôi xong", "tiêu rồi", "chết dở", "hỏng rồi", "nguy hiểm",
        "độc hại", "ung thư", "dị ứng", "nhiễm độc", "cẩn thận", "coi chừng",
        "đừng dại", "né ngay", "né gấp", "chạy ngay", "sợ quá", "hãi", "báo công an",
        "pháp luật", "lừa đảo", "gian thương", "hàng giả",
    ], 1.2),

    # Cảm xúc 2: Surprise (Bất ngờ, kinh ngạc, vỡ lẽ, sốc)
    ("Surprise", [
        "bất ngờ", "sốc", "té ngửa", "xỉu", "ngỡ ngàng", "sự thật", "hóa ra",
        "hoá ra", "thật ra", "ai ngờ", "không ngờ", "trời ơi", "kinh thật",
        "rùng mình", "biến căng", "drama", "ảo thật", "không thể tin", "kinh khủng",
    ], 1.1),

    # Cảm xúc 3: Curiosity (Tò mò, thắc mắc, hỏi ngơ ngác)
    ("Curiosity", [
        "ủa", "hả", "sao lại", "sao vậy", "sao thế", "sao ta", "là sao",
        "thế nào", "làm sao", "ở đâu", "mua ở đâu", "shop nào", "xin địa chỉ",
        "ai biết", "cho em hỏi", "cho mình hỏi", "hỏi thật", "thắc mắc", "ngơ ngác",
        "đâu ra", "cái gì", "gì cơ", "?",
    ], 1.0),

    # Cảm xúc 4: Humor (Hài hước, châm biếm, mỉa mai, cà khịa)
    ("Humor", [
        "haha", "hahaha", "kkk", "cười", "mắc cười", "buồn cười", "cười ỉa",
        "cười bò", "cười chết", "cười té ghế", "hề", "hề hước", "hài", "hài hước",
        "chúa hề", "bựa", "quỳ", "lạy", "nhịn cười", "troll", "vui vãi",
        "não", "khôn thế", "ảo tưởng", "tỉnh lại đi", "ai mượn", "ai bảo",
        "tào lao", "ngáo", "dở hơi", "xàm", "nhảm", "🤣", "😂", "😆",
    ], 1.0),

    # Cảm xúc 5: Suspense (Hồi hộp, nghi ngờ, nín thở, drama)
    ("Suspense", [
        "thật không", "thật á", "thật hả", "có chắc", "chắc chưa", "nghi ngờ",
        "nghi lắm", "điêu", "xạo", "chém gió", "bịp", "lươn", "lấn cấn",
        "cấn cấn", "sượng trân", "chim mồi", "seeding", "liếc", "lườm",
        "im lặng", "nín thở", "...",
    ], 0.9),

    # Cảm xúc 6: Sadness (Buồn bã, bi ai, tiếc tiền, bất lực)
    ("Sadness", [
        "tiếc tiền", "tiếc của", "tiếc", "mất tiền", "uổng", "mất trắng",
        "đen đủi", "xui xẻo", "mất oan", "buồn", "buồn quá", "khóc", "huhu",
        "rơi nước mắt", "xót xa", "đau lòng", "tội nghiệp", "đáng thương",
        "cạn lời", "bó tay", "hết cứu", "bất lực", "😭", "😢", "🥺", "💔",
    ], 0.9),

    # Cảm xúc 7: Excitement (Phấn khích, khen ngợi, hype, đỉnh cao)
    ("Excitement", [
        "wow", "xuất sắc", "đỉnh", "đỉnh cao", "đỉnh nóc", "đỉnh của chóp",
        "tuyệt vời", "quá đẹp", "quá hay", "mê ly", "xịn sò", "siêu phẩm",
        "đẹp quá", "xinh quá", "ưng quá", "quá xịn", "quá chuẩn", "chuẩn luôn",
        "quá đã", "đã cái nư", "🔥", "✨", "🥰", "😍",
    ], 0.9),

    # Cảm xúc 8: Serious (Nghiêm túc, thông tin then chốt, lời khuyên)
    ("Serious", [
        "lưu ý", "quan trọng", "nguyên tắc", "bắt buộc", "kinh nghiệm",
        "mẹo", "bí quyết", "chỉ cho", "lời khuyên", "hướng dẫn", "chính xác",
        "bản chất", "kết luận", "tóm lại",
    ], 0.8),
]

# ─── Bảng ánh xạ Cảm xúc & Loại cơ hội → Bộ SFX tương ứng ──────────────────
_SFX_PALETTE: dict[str, list[tuple[str, float]]] = {
    # (Tên file, Âm lượng đề xuất 0.0 - 1.0)
    "Hook": [
        ("whoosh.mp3", 0.40),
        ("pop.mp3", 0.38),
        ("ting.mp3", 0.35),
        ("vine-boom.mp3", 0.32),
    ],
    "Transition": [
        ("whoosh.mp3", 0.42),
        ("side-eye.mp3", 0.38),
        ("pop.mp3", 0.35),
    ],
    "Emphasis": [
        ("pop.mp3", 0.38),
        ("ting.mp3", 0.36),
        ("nice.mp3", 0.38),
    ],
    "Warning": [
        ("oh-no.mp3", 0.42),
        ("fbi-open-up.mp3", 0.38),
        ("hell-nah.mp3", 0.40),
        ("metal-pipe.mp3", 0.30),
    ],
    "Surprise": [
        ("vine-boom.mp3", 0.35),
        ("metal-pipe.mp3", 0.30),
        ("damn.mp3", 0.38),
        ("what-the-hell.mp3", 0.40),
    ],
    "Curiosity": [
        ("huh.mp3", 0.42),
        ("what-the-hell.mp3", 0.38),
        ("quack.mp3", 0.36),
    ],
    "Humor": [
        ("laugh-tiktok.mp3", 0.40),
        ("bonk.mp3", 0.40),
        ("fart.mp3", 0.36),
        ("bruh.mp3", 0.40),
        ("quack.mp3", 0.36),
        ("emotional-damage.mp3", 0.42),
    ],
    "Suspense": [
        ("side-eye.mp3", 0.42),
        ("cricket.mp3", 0.35),
        ("vine-boom.mp3", 0.30),
    ],
    "Sadness": [
        ("womp-womp.mp3", 0.40),
        ("sad-violin.mp3", 0.38),
        ("oof.mp3", 0.38),
    ],
    "Excitement": [
        ("wow.mp3", 0.40),
        ("airhorn.mp3", 0.32),
        ("nice.mp3", 0.38),
    ],
    "Neutral": [
        ("pop.mp3", 0.28),
        ("ting.mp3", 0.28),
    ],
}


@dataclass
class SoundCue:
    """Đặc tả một điểm chèn Sound Effect chính xác."""
    sfx_file: Path | None
    offset_seconds: float
    duration_seconds: float
    emotion: str
    opportunity_type: str
    keyword_or_phrase: str
    volume: float
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["sfx_file"] = str(self.sfx_file) if self.sfx_file else None
        return d


class SoundDesigner:
    """Bộ não phân tích ngữ cảnh lời thoại và tự động sắp đặt SFX theo chuẩn TikTok / Reels."""

    def __init__(self, sfx_dir: Path):
        self.sfx_dir = sfx_dir
        self.recent_sfx: list[str] = []

    def _match_keyword(self, kw: str, text: str) -> bool:
        if kw in ("?", "!", "...", "..") or any(ord(c) > 0x1F000 for c in kw):
            return kw in text
        if len(kw) <= 4:
            return bool(re.search(rf"(?<!\w){re.escape(kw)}(?!\w)", text, re.IGNORECASE))
        return kw.lower() in text.lower()

    def detect_emotion(self, text: str) -> tuple[str, str, float]:
        """Bước 2: Nhận diện bối cảnh cảm xúc trong câu thoại."""
        t = text.lower()
        scored: list[tuple[float, str, str]] = []

        for emotion, keywords, weight in _EMOTION_RULES:
            for kw in keywords:
                if self._match_keyword(kw, t):
                    scored.append((weight, emotion, kw))
                    break

        if scored:
            scored.sort(key=lambda x: x[0], reverse=True)
            w, emo, matched_kw = scored[0]
            return emo, matched_kw, w

        # Fallback theo dấu câu
        if "?" in text:
            return "Curiosity", "?", 0.7
        if "!" in text:
            return "Surprise", "!", 0.7
        if "..." in text or ".." in text:
            return "Suspense", "...", 0.6

        return "Neutral", "", 0.0

    def identify_opportunity(self, is_hook: bool, text: str, emotion: str,
                             matched_kw: str) -> tuple[str, str]:
        """Bước 3: Xác định thời điểm phù hợp để chèn SFX (Hook, Emphasis, Comedy, Transition, Suspense)."""
        t = text.lower()

        # A. Hook cho bài đăng gốc
        if is_hook:
            if emotion in ("Curiosity", "Warning", "Surprise"):
                return "Hook", matched_kw or "Mở đầu kịch tính"
            return "Hook", "Mở đầu lôi cuốn"

        # B. Transition (Chuyển vế đối lập)
        transition_triggers = ["nhưng mà", "thế mà", "ai ngờ", "hóa ra", "hoá ra", "tuy nhiên", "nhưng"]
        for tr in transition_triggers:
            if self._match_keyword(tr, t):
                return "Transition", tr

        # C. Comedy / Punchline
        if emotion in ("Humor", "Sadness") or any(k in t for k in ["cười", "vl", "vcl", "bó tay", "hết cứu"]):
            return "Comedy", matched_kw or "Punchline hài hước"

        # D. Suspense
        if emotion in ("Suspense", "Warning"):
            return "Suspense", matched_kw or "Tạo hồi hộp / nghi vấn"

        # E. Emphasis (Từ khóa, con số, mẹo)
        if emotion in ("Excitement", "Serious") or re.search(r"\b\d+([.,]\d+)?\s*(k|triệu|tỷ|đ|vnđ|%)?", t):
            return "Emphasis", matched_kw or "Nhấn mạnh thông tin"

        return "Neutral", matched_kw or "Không có điểm nhấn đặc biệt"

    def _pick_sfx_candidate(self, category: str) -> tuple[Path | None, float]:
        """Bước 4 & 6: Chọn SFX theo danh mục, chống lặp lại âm thanh liên tiếp."""
        candidates = _SFX_PALETTE.get(category, _SFX_PALETTE["Neutral"])
        available = [
            (self.sfx_dir / fname, vol)
            for fname, vol in candidates
            if (self.sfx_dir / fname).exists()
        ]
        if not available:
            return None, 0.40

        # Lọc bớt các âm thanh vừa mới xuất hiện ở 2 cảnh gần nhất để không nhàm chán
        filtered = [item for item in available if item[0].name not in self.recent_sfx[-2:]]
        chosen = random.choice(filtered if filtered else available)

        self.recent_sfx.append(chosen[0].name)
        if len(self.recent_sfx) > 10:
            self.recent_sfx.pop(0)

        return chosen

    def plan_sound_cue(
        self,
        text: str,
        is_hook: bool = False,
        sentence_boundaries: list[dict[str, Any]] | None = None,
        total_duration: float = 3.0,
    ) -> SoundCue:
        """Thực hiện toàn diện quy trình 6 bước để tạo 1 SoundCue chính xác từng mili-giây."""
        # 1 & 2. Chuẩn hóa từ viết tắt & Phân tích lời thoại & Nhận diện cảm xúc
        norm_text = normalize_vietnamese_text(text)
        emotion, matched_kw, _ = self.detect_emotion(norm_text)

        # 3. Xác định cơ hội chèn âm thanh
        opp_type, focus_phrase = self.identify_opportunity(is_hook, norm_text, emotion, matched_kw)

        # 4 & 6. Lựa chọn SFX và kiểm soát mật độ (Natural Sound Design)
        # Nếu là Neutral và không phải Hook, giữ cho không gian âm thanh sạch sẽ (Balanced Density)
        if opp_type == "Neutral" and not is_hook:
            # 50% trường hợp để không âm thanh để giữ giọng thoại tự nhiên, 50% gõ nhẹ pop
            if random.random() < 0.5:
                return SoundCue(
                    sfx_file=None,
                    offset_seconds=0.0,
                    duration_seconds=0.0,
                    emotion="Neutral",
                    opportunity_type="None",
                    keyword_or_phrase="Bình thường",
                    volume=0.0,
                    explanation="Nội dung trung tính, không chèn SFX để giọng nói rõ ràng tự nhiên.",
                )

        target_category = opp_type if opp_type in _SFX_PALETTE else emotion
        sfx_path, sfx_vol = self._pick_sfx_candidate(target_category)

        # 5. Precise Timing: Canh thời điểm kích hoạt chính xác theo Boundary
        offset = 0.0
        if sentence_boundaries and len(sentence_boundaries) > 0:
            # Tìm câu chứa từ khóa / điểm nhấn
            target_idx = 0
            if focus_phrase:
                for idx, b in enumerate(sentence_boundaries):
                    if focus_phrase.lower() in b.get("text", "").lower():
                        target_idx = idx
                        break

            target_b = sentence_boundaries[target_idx]
            b_offset = float(target_b.get("offset", 0.0))
            b_dur = float(target_b.get("duration", 1.0))

            if opp_type == "Hook":
                offset = max(0.0, b_offset)
            elif opp_type in ("Transition", "Comedy"):
                # Đặt ngay đầu vế câu chuyển đổi hoặc ngay sau khi nói từ mở đầu
                offset = max(0.0, b_offset + min(0.35, b_dur * 0.2))
            elif opp_type == "Emphasis":
                # Đặt đồng bộ với từ khóa
                offset = max(0.0, b_offset + min(0.25, b_dur * 0.15))
            else:
                offset = max(0.0, b_offset)
        else:
            # Ước lượng hợp lý nếu không có boundary
            offset = 0.0 if is_hook else 0.15

        # Đảm bảo offset không vượt quá độ dài đoạn thoại
        offset = min(offset, max(0.0, total_duration - 0.6))

        explanation = (
            f"Kích hoạt tại t={offset:.2f}s để hỗ trợ nhịp [{opp_type}] với cảm xúc [{emotion}], "
            f"nhấn vào '{focus_phrase or matched_kw or 'câu thoại'}'. Giữ âm lượng {int(sfx_vol*100)}% "
            f"không đè lấp giọng đọc."
        )

        return SoundCue(
            sfx_file=sfx_path,
            offset_seconds=round(offset, 3),
            duration_seconds=round(total_duration, 3),
            emotion=emotion,
            opportunity_type=opp_type,
            keyword_or_phrase=focus_phrase or matched_kw or text[:25],
            volume=sfx_vol,
            explanation=explanation,
        )


def format_cue_report(cues: list[SoundCue]) -> str:
    """Tạo bảng báo cáo chuyên nghiệp theo định dạng Markdown."""
    lines = [
        "| STT | Thời điểm (Timestamp) | Từ khóa / Điểm nhấn | Cảm xúc | Cơ hội SFX | Tên Sound Effect | Âm lượng & Hướng dẫn |",
        "|---|---|---|---|---|---|---|",
    ]
    for i, c in enumerate(cues):
        sfx_name = c.sfx_file.name if c.sfx_file else "*(Không chèn SFX)*"
        time_str = f"`{c.offset_seconds:05.2f}s`"
        vol_str = f"{int(c.volume * 100)}%" if c.volume > 0 else "0%"
        lines.append(
            f"| {i+1} | {time_str} | *\"{c.keyword_or_phrase}\"* | **{c.emotion}** | `{c.opportunity_type}` | `{sfx_name}` | {vol_str} - {c.explanation} |"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Chuyên gia AI Phân tích Lời thoại & Đề xuất Sound Effects (SFX)")
    parser.add_argument("text", nargs="*", help="Câu thoại cần phân tích")
    parser.add_argument("--file", help="File văn bản chứa transcript / kịch bản (mỗi dòng một câu)")
    parser.add_argument("--sfx-dir", default=str(Path(__file__).parent / "assets" / "sfx"),
                        help="Thư mục chứa SFX")
    args = parser.parse_args()

    lines_to_test: list[str] = []
    if args.file and Path(args.file).exists():
        lines_to_test = [line.strip() for line in Path(args.file).read_text(encoding="utf-8").splitlines() if line.strip()]
    elif args.text:
        lines_to_test = [" ".join(args.text)]
    else:
        # Mẫu mặc định minh họa
        lines_to_test = [
            "Đừng bao giờ mua vòng đá phong thủy online nếu bạn chưa biết điều này!",
            "Ủa sao giá gốc 100k mà vô live bán tới 1 triệu vậy trời?",
            "Nhìn là biết gian thương lừa đảo rồi, lươn lẹo dã man...",
            "Cười ỉa luôn á, khôn như thế quê tôi người ta xích đầy rồi!",
            "Nhưng sự thật là kim loại này rất độc hại, có thể gây dị ứng nặng đó.",
            "Shop này uy tín nha mọi người, mua đeo 2 năm rồi siêu phẩm luôn!",
        ]

    designer = SoundDesigner(Path(args.sfx_dir))
    cues: list[SoundCue] = []
    for i, line in enumerate(lines_to_test):
        cue = designer.plan_sound_cue(line, is_hook=(i == 0), total_duration=3.5)
        cues.append(cue)

    print("\n" + "=" * 90)
    print("🎬 KẾT QUẢ PHÂN TÍCH LỜI THOẠI & ĐỀ XUẤT SOUND EFFECTS (SFX)")
    print("=" * 90 + "\n")
    print(format_cue_report(cues))
    print("\n" + "=" * 90 + "\n")
