"""Chọn âm thanh meme phù hợp với nội dung bình luận bằng keyword matching.

Không dùng AI — sử dụng quy tắc ngữ cảnh từ khóa tiếng Việt cực kỳ đa dạng
để nhận diện mọi tình huống: hài hước, kịch tính, buồn bã, náo nhiệt, nghi ngờ,
hỏi ngơ ngác, cảnh báo,... Đảm bảo mọi bình luận đều có sound effect phù hợp.
"""
from __future__ import annotations

import random
import re
from pathlib import Path

# ─── Bảng ngữ cảnh từ khóa → File SFX TikTok viral ───────────────────────────
_RULES: list[tuple[str, list[str], int]] = [
    # 1. Hài hước, cười cợt, nhảm nhí, chúa hề (Laugh TikTok / Fart / Bruh)
    ("laugh-tiktok.mp3", [
        "haha", "hahaha", "kkk", "cười", "mắc cười", "buồn cười", "cười ỉa",
        "cười bò", "cười chết", "cười té ghế", "hề", "hề hước", "hài", "hài hước",
        "hài vl", "hài vcl", "hài quá", "chúa hề", "té ghế", "vl", "vcl", "vãi",
        "bựa", "quỳ", "lạy", "nhịn cười", "troll", "hài cốt", "vui vãi",
        "🤣", "😂", "😆", "😅", "😹",
    ], 5),

    # 2. Cảnh báo độc hại, nguy hiểm, toang rồi, chết dở (Oh No TikTok)
    ("oh-no.mp3", [
        "toang", "toang rồi", "thôi xong", "tiêu rồi", "chết dở", "hỏng rồi",
        "nguy hiểm", "nguy", "độc hại", "độc", "hại", "hại lắm", "hại sức khỏe",
        "ung thư", "kim loại nặng", "dị ứng", "nhiễm độc", "ngộ độc", "chết",
        "chết tiệt", "cẩn thận", "coi chừng", "đừng dại", "né ngay", "né gấp",
        "chạy ngay", "sợ quá", "hãi", "kinh hoàng", "khiếp", "rợn người",
    ], 5),

    # 3. Kịch tính, drama, giật mình, sự thật ngã ngửa (Vine Boom)
    ("vine-boom.mp3", [
        "bất ngờ", "sốc", "té ngửa", "xỉu", "ngỡ ngàng", "sự thật", "hóa ra",
        "hoá ra", "thật ra", "ai ngờ", "không ngờ", "trời ơi", "chết tiệt",
        "kinh thật", "rùng mình", "biến căng", "drama", "căng đét", "căng thẳng",
        "nín thở", "gay cấn", "bóc phốt", "kinh khủng", "rúng động",
    ], 5),

    # 4. Nghi ngờ, lườm nguýt, lươn lẹo, bán hàng gian thương (Side Eye)
    ("side-eye.mp3", [
        "thật không", "thật á", "thật hả", "có chắc", "chắc chưa", "nghi ngờ",
        "nghi lắm", "lừa đảo", "bị lừa", "điêu", "xạo", "chém gió", "bịp",
        "lươn", "gian thương", "không uy tín", "k uy tín", "hàng fake", "hàng giả",
        "nhái", "lấn cấn", "cấn", "cấn cấn", "sượng", "sượng trân", "chim mồi",
        "seeding", "treo đầu dê", "liếc", "lườm", "inbox mình", "shop tui",
        "bên tui", "bên shop",
    ], 5),

    # 5. Cà khịa, hỏi xoáy, đâm chọt, vặn vẹo (Emotional Damage)
    ("emotional-damage.mp3", [
        "suy nghĩ thử", "suy nghĩ lại", "nhập giá", "bán cho bạn", "tự hiểu",
        "nghĩ sao vậy", "nghĩ kĩ", "khôn", "khôn lỏi", "ngây thơ", "thông minh",
        "não", "nghĩ xem", "tính tiền", "khôn thế", "ảo tưởng", "thức tỉnh",
        "tỉnh táo", "tỉnh lại đi", "chê", "đáng đời", "ai mượn", "ai bảo",
    ], 5),

    # 6. Hỏi ngơ ngác, tò mò, chưa hiểu gì (Huh Cat / What the hell)
    ("huh.mp3", [
        "?", "ủa", "hả", "sao lại", "sao vậy", "sao thế", "sao ta", "là sao",
        "thế nào", "làm sao", "ở đâu", "mua ở đâu", "shop nào", "xin địa chỉ",
        "chưa biết", "chx bt", "ai biết", "cho em hỏi", "cho mình hỏi", "hỏi thật",
        "thắc mắc", "ngơ ngác", "cứu", "cứu với", "cứu em", "được không", "được k",
        "k ạ", "không ạ", "nhỉ", "hử", "đâu ra", "cái gì", "gì cơ", "ngơ",
    ], 4),

    # 7. Rơi vỡ, đánh rơi, đứt dây, đổ nát (Metal Pipe)
    ("metal-pipe.mp3", [
        "bị đứt", "đứt", "rớt mất", "rơi mất", "rớt", "rơi", "vỡ",
        "bể", "tan tành", "va đập", "rơi vỡ", "tuột", "đứt dây", "văng",
    ], 4),

    # 8. Tiếc tiền, tiếc của, xui xẻo, công cốc (Womp Womp)
    ("womp-womp.mp3", [
        "tiếc tiền", "tiếc của", "tiếc", "bỏ thì tiếc", "mất tiền", "uổng",
        "uổng tiền", "mất trắng", "đen đủi", "xui xẻo", "mất oan", "lãng phí",
        "vứt đi", "bỏ đi thì", "đen thật", "xui thế",
    ], 4),

    # 9. Bi ai, đau lòng, khóc lóc, buồn bã (Sad Violin)
    ("sad-violin.mp3", [
        "buồn", "buồn quá", "khóc", "huhu", "huhuhu", "rơi nước mắt", "xót xa",
        "đau lòng", "tội nghiệp", "đáng thương", "thương em", "tủi thân",
        "khổ thân", "chia buồn", "đau đớn", "trầm cảm", "thất vọng",
        "😭", "😢", "🥺", "💔", "😞", "😔",
    ], 4),

    # 10. Náo nhiệt, phấn khích, khen ngợi, đỉnh cao (Wow / Airhorn)
    ("wow.mp3", [
        "wow", "xuất sắc", "đỉnh", "đỉnh cao", "đỉnh nóc", "đỉnh của chóp",
        "tuyệt vời", "quá đẹp", "quá hay", "mê ly", "xịn sò", "siêu phẩm",
        "đẹp quá", "xinh quá", "ưng quá", "quá xịn", "quá đỉnh", "cháy quá",
        "🔥", "✨", "🥰", "❤️", "😍",
    ], 4),

    # 11. Hype, quá chuẩn, vỗ tay (Airhorn)
    ("airhorn.mp3", [
        "đúng rồi", "quá chuẩn", "chuẩn không cần chỉnh", "chính xác",
        "chuẩn luôn", "số 1", "chất lừ", "chuẩn đét", "vỗ tay", "chúc mừng",
        "quá đã", "đã cái nư", "cháy",
    ], 3),

    # 12. Phát hiện mẹo hay, mách nước, kinh nghiệm (Ting)
    ("ting.mp3", [
        "tham khảo", "mẹo", "chỉ cho", "gợi ý", "kinh nghiệm", "mách bạn",
        "bảo quản", "bí quyết", "cách phân biệt", "phân biệt", "nhận biết",
        "lời khuyên", "rcm", "recommend",
    ], 3),

    # 13. Gõ đầu thức tỉnh, nói ngáo (Bonk)
    ("bonk.mp3", [
        "ngáo", "ngáo ngơ", "ngáo thật", "ngu ngốc", "tào lao", "vớ vẩn",
        "thức tỉnh", "tỉnh ngủ", "gõ đầu", "bố khỉ", "dở hơi",
    ], 3),

    # 14. Tát tỉnh người, chấn chỉnh thái độ (Slap)
    ("slap.mp3", [
        "tát cho", "vả cho", "nói thẳng", "tỉnh mộng", "tỉnh chưa",
        "chấn chỉnh", "bốp", "mơ tưởng", "vả vào mặt",
    ], 3),

    # 15. Công an bắt, vi phạm, báo công an (FBI Open Up)
    ("fbi-open-up.mp3", [
        "báo công an", "công an", "bắt ngay", "bắt khẩn cấp", "pháp luật",
        "đi tù", "tội phạm", "hàng cấm", "vào tù",
    ], 3),

    # 16. Cạn lời, bất lực, facepalm (Bruh)
    ("bruh.mp3", [
        "rõ ràng", "hiển nhiên", "vậy mà", "cạn lời", "bó tay", "bó chiếu",
        "bất lực", "chịu luôn", "hết cứu", "hết nước chấm", "thật sự à",
        "dĩ nhiên", "tất nhiên", "chán chả buồn nói",
    ], 3),

    # 17. Xàm xí, nhảm nhí (Fart)
    ("fart.mp3", [
        "xàm", "nhảm", "xàm xí", "nói nhảm", "tào lao bí đao", "vô nghĩa",
        "nhảm nhí", "chém gió",
    ], 3),

    # 18. Cái quái gì vậy, vô lý (What The Hell)
    ("what-the-hell.mp3", [
        "vô lý", "vô lí", "quái lạ", "cái quái gì", "wtf", "lạ đời",
        "trời đất", "chuyện lạ", "ngược đời", "ảo thật",
    ], 3),

    # 19. Hợp lý, duyệt, vừa ý (Nice)
    ("nice.mp3", [
        "hợp lý", "ổn áp", "ngon lành", "được nè", "duyệt", "tốt đó",
        "chuẩn đấy", "hợp tình", "ok nè", "ưng bụng", "tốt nè",
    ], 2),

    # 20. Ngơ ngác như vịt (Quack)
    ("quack.mp3", [
        "ngây thơ", "ngơ ngác", "lơ ngơ", "vịt", "lù đù", "ngơ",
    ], 2),
]

# Danh sách SFX nhẹ nhàng dùng làm fallback để bình luận nào cũng có âm thanh
_FALLBACK_SFX = [
    "ting.mp3",
    "nice.mp3",
    "huh.mp3",
    "bonk.mp3",
    "quack.mp3",
    "oof.mp3",
]


def _match_keyword(kw: str, text: str) -> bool:
    """Khớp từ khóa thông minh: dùng ranh giới từ (word boundary) cho từ ngắn để tránh bắt nhầm (vd 'ủa' trong 'của')."""
    if kw in ("?", "!", "...", "..") or any(ord(c) > 0x1F000 for c in kw):
        return kw in text
    if len(kw) <= 4:
        return bool(re.search(rf"(?<!\w){re.escape(kw)}(?!\w)", text, re.IGNORECASE))
    return kw in text


def pick_meme_sfx(text: str, sfx_dir: Path) -> Path | None:
    """Chọn file SFX meme phù hợp nhất với nội dung bình luận.

    Quy tắc:
      1. Khớp từ khóa ngữ cảnh tiếng Việt (hài hước, kịch tính, buồn bã, hỏi,...).
      2. Nếu khớp nhiều nhóm, ưu tiên nhóm có trọng số cao nhất.
      3. Nếu không khớp từ khóa cụ thể, tự động nhận diện theo dấu câu (?/!/...) hoặc emoji.
      4. Fallback chọn âm thanh vui nhộn nhẹ nhàng để mọi bình luận đều có SFX sinh động.
    """
    if not sfx_dir.exists():
        return None

    t = text.lower()
    matches: list[tuple[int, str]] = []

    # 1. Quét từ khóa
    for filename, keywords, weight in _RULES:
        sfx_path = sfx_dir / filename
        if not sfx_path.exists():
            continue
        if any(_match_keyword(kw, t) for kw in keywords):
            matches.append((weight, filename))

    if matches:
        max_weight = max(w for w, _ in matches)
        top_candidates = [f for w, f in matches if w == max_weight]
        chosen = random.choice(top_candidates)
        return sfx_dir / chosen

    # 2. Nhận diện theo dấu câu & biểu cảm nếu chưa khớp từ khóa chính xác
    if "?" in text:
        candidate = sfx_dir / "huh.mp3"
        if candidate.exists():
            return candidate

    if "!" in text:
        candidate = sfx_dir / "vine-boom.mp3"
        if candidate.exists():
            return candidate

    if "..." in text or ".." in text:
        candidate = sfx_dir / "side-eye.mp3"
        if candidate.exists():
            return candidate

    # 3. Fallback nhẹ nhàng: bình luận nào cũng có SFX vui tươi, không để bị im lặng
    for fname in _FALLBACK_SFX:
        p = sfx_dir / fname
        if p.exists():
            return p

    return None
