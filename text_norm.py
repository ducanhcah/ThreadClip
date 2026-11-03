"""Bộ chuẩn hóa và nhận diện từ viết tắt tiếng Việt chuyên sâu (Vietnamese Slang & Text Normalizer).

Hỗ trợ toàn diện các từ viết tắt, tiếng lóng, teencode thịnh hành của Gen Z và giới trẻ
trên TikTok, Threads, Facebook, Instagram,... Chuyển đổi thành tiếng Việt chuẩn,
giúp giọng đọc AI (TTS) phát âm tự nhiên 100%, không bị vấp hoặc đánh vần từng chữ cái.
"""
from __future__ import annotations

import re
from typing import Any

# ─── 1. BẢNG CỤM TỪ GHÉP & CÂU CỬA MIỆNG GEN Z (XỬ LÝ TRƯỚC ĐỂ TRÁNH TRÙNG LẶP) ───
PHRASE_RULES: list[tuple[re.Pattern, str]] = [
    # Cảm thán Gen Z & TikTok
    (re.compile(r"\b(j\s*z\s*tr|j\s*z\s*trùi|j\s*z\s*trui|j\s*z\s*troi|j\s*z)\b", re.IGNORECASE), "gì vậy trời"),
    (re.compile(r"\b(u\s*là\s*tr|u\s*là\s*trời|u\s*la\s*troi|u\s*la\s*tr)\b", re.IGNORECASE), "úi là trời"),
    (re.compile(r"\b(chầm\s*kẽm|cham\s*kem)\b", re.IGNORECASE), "trầm cảm"),
    (re.compile(r"\b(ét\s*o\s*ét|ét\s*ô\s*ét|s\.o\.s)\b", re.IGNORECASE), "ét o ét"),
    (re.compile(r"\b(gòi\s*xong|roi\s*xong)\b", re.IGNORECASE), "rồi xong"),
    (re.compile(r"\b(thặc\s*sự|thặc\s*su)\b", re.IGNORECASE), "thật sự"),
    (re.compile(r"\b(chếc\s*tiệc|chếc\s*tiệt)\b", re.IGNORECASE), "chết tiệt"),
    (re.compile(r"\b(xu\s*cà\s*na)\b", re.IGNORECASE), "xu cà na"),
    (re.compile(r"\b(hết\s*nước\s*chấm)\b", re.IGNORECASE), "hết nước chấm"),
    (re.compile(r"\b(đỉnh\s*chóp|dinh\s*chop)\b", re.IGNORECASE), "đỉnh cao"),
    (re.compile(r"\b(check\s*var)\b", re.IGNORECASE), "kiểm tra lại"),
    (re.compile(r"\b(out\s*trình)\b", re.IGNORECASE), "vượt trình độ"),
    (re.compile(r"\b(red\s*flag)\b", re.IGNORECASE), "cờ đỏ"),
    (re.compile(r"\b(green\s*flag)\b", re.IGNORECASE), "cờ xanh"),
    (re.compile(r"\b(hổng\s*có|hẻm\s*có|hem\s*có|khum\s*có)\b", re.IGNORECASE), "không có"),
    (re.compile(r"\b(sao\s*[vz]|s\s*[vz]|thế\s*[vz]|sao\s*dị)\b", re.IGNORECASE), "sao vậy"),
    (re.compile(r"\b(người\s*iu|ngừi\s*iu|ngiu)\b", re.IGNORECASE), "người yêu"),
    (re.compile(r"\b(bạn\s*thân|bthan)\b", re.IGNORECASE), "bạn thân"),
    (re.compile(r"\b(đúng\s*r|đr\s*đó|đr|đúng\s*òi|đrùi)\b", re.IGNORECASE), "đúng rồi"),
    (re.compile(r"\b(rớt\s*nc\s*mắt|rớt\s*nước\s*mắt)\b", re.IGNORECASE), "rớt nước mắt"),
    (re.compile(r"\b(nc\s*mắt)\b", re.IGNORECASE), "nước mắt"),
    (re.compile(r"\b(snvv|hpbd)\b", re.IGNORECASE), "sinh nhật vui vẻ"),
]

# ─── 2. BIỂU THỨC QUY LUẬT (SỐ ĐO, THỜI GIAN, TIỀN TỆ, TIẾNG CƯỜI, KÉO DÀI TỪ) ─
REGEX_RULES: list[tuple[re.Pattern, Any]] = [
    # Số + h / h30 -> giờ (ví dụ: 12h -> 12 giờ, 1h30 -> 1 giờ 30)
    (re.compile(r"\b(\d+)\s*h(\d+)?\b", re.IGNORECASE),
     lambda m: f"{m.group(1)} giờ" + (f" {m.group(2)}" if m.group(2) else "")),
    # Số + p -> phút (ví dụ: 15p -> 15 phút, 30p -> 30 phút)
    (re.compile(r"\b(\d+)\s*p\b", re.IGNORECASE), r"\1 phút"),
    # Số + s -> giây (ví dụ: 30s -> 30 giây)
    (re.compile(r"\b(\d+)\s*s\b", re.IGNORECASE), r"\1 giây"),
    # Số + k -> nghìn (ví dụ: 50k -> 50 nghìn, 100k -> 100 nghìn)
    (re.compile(r"\b(\d+)\s*k\b", re.IGNORECASE), r"\1 nghìn"),
    # Số + tr / củ -> triệu (ví dụ: 2tr -> 2 triệu, 5 củ -> 5 triệu)
    (re.compile(r"\b(\d+)\s*(tr|củ)\b", re.IGNORECASE), r"\1 triệu"),
    # Số + lít -> trăm nghìn (ví dụ: 2 lít -> 2 trăm nghìn, 5 lít -> 5 trăm nghìn)
    (re.compile(r"\b(\d+)\s*lít\b", re.IGNORECASE), r"\1 trăm nghìn"),
    # Kéo dài chữ cái teen chat (ví dụ: chánnn -> chán, đẹppp -> đẹp, iuuu -> yêu, xỉuuu -> xỉu)
    (re.compile(r"\biu{2,}\b", re.IGNORECASE), "yêu"),
    (re.compile(r"\bx[iỉĩ]u{2,}\b", re.IGNORECASE), "xỉu"),
    (re.compile(r"\bchán{2,}\b", re.IGNORECASE), "chán"),
    (re.compile(r"\bđẹp{2,}\b", re.IGNORECASE), "đẹp"),
    (re.compile(r"\b(buồn|bùn){2,}\b", re.IGNORECASE), "buồn"),
    (re.compile(r"\b(vui|zui){2,}\b", re.IGNORECASE), "vui"),
    # Kaka, hihi, haha, he he, kkk, haizz -> chuẩn hóa phát âm êm tai
    (re.compile(r"\b(ha){2,}\b", re.IGNORECASE), "ha ha"),
    (re.compile(r"\b(hi){2,}\b", re.IGNORECASE), "hi hi"),
    (re.compile(r"\b(he){2,}\b", re.IGNORECASE), "he he"),
    (re.compile(r"\bk{3,}\b", re.IGNORECASE), "kha kha"),
    (re.compile(r"\bhaiz+\b", re.IGNORECASE), "than ôi"),
    (re.compile(r"\bhic+\b", re.IGNORECASE), "hu hu"),
    (re.compile(r"\bhuhu+\b", re.IGNORECASE), "hu hu"),
]

# ─── 3. TỪ ĐIỂN TỪ VIẾT TẮT ĐƠN LẺ (GEN Z, MXH, TEENCODE & CẢM XÚC GIAO TIẾP) ───
ABBREVIATIONS: dict[str, str] = {
    # ── A. Thứ trong tuần & Dịp lễ ──
    "t2": "thứ hai",
    "t3": "thứ ba",
    "t4": "thứ tư",
    "t5": "thứ năm",
    "t6": "thứ sáu",
    "t7": "thứ bảy",
    "cn": "chủ nhật",
    "sn": "sinh nhật",

    # ── B. Cảm xúc, Giao tiếp & Tình cảm (chuẩn theo bộ SLANG_MAP) ──
    "iu": "yêu",
    "iuu": "yêu",
    "iuuu": "yêu",
    "ye": "yêu",
    "thik": "thích",
    "thw": "thương",
    "mún": "muốn",
    "bít": "biết",
    "hỉu": "hiểu",
    "hieu": "hiểu",
    "bt": "biết",
    "uk": "ừ",
    "uh": "ừ",
    "ừa": "ừ",
    "um": "ừ",
    "ok": "đồng ý",
    "oki": "đồng ý",
    "oke": "đồng ý",
    "okei": "đồng ý",
    "okey": "đồng ý",
    "okela": "đồng ý",
    "dcmm": "được mà",
    "vl": "rất",
    "vcl": "rất",
    "vler": "rất",
    "vkl": "rất",
    "vle": "rất",
    "vcc": "rất",
    "vchuong": "vãi chưởng",
    "vcoi": "rất",
    "vloz": "rất",
    "vlon": "rất",
    "xỉu": "xỉu",
    "xĩu": "xỉu",
    "géc": "ghét",
    "gécc": "ghét",
    "bùn": "buồn",
    "pùn": "buồn",
    "zui": "vui",
    "quó": "quá",
    "wa": "quá",
    "qá": "quá",
    "wá": "quá",

    # ── C. Xưng hô & Nhân xưng ──
    "t": "tao",
    "m": "mình",
    "mk": "mình",
    "mik": "mình",
    "mềnh": "mình",
    "b": "bạn",
    "ng": "người",
    "ngừi": "người",
    "ngta": "người ta",
    "mn": "mọi người",
    "mng": "mọi người",
    "ad": "admin",
    "ck": "chồng",
    "vk": "vợ",
    "ox": "ông xã",
    "bx": "bà xã",
    "thg": "thằng",
    "thk": "thằng",
    "ny": "người yêu",
    "nyc": "người yêu cũ",
    "ex": "người yêu cũ",
    "cr": "crush",
    "crush": "crush",
    "hs": "học sinh",
    "sv": "sinh viên",
    "gv": "giáo viên",
    "bme": "bố mẹ",
    "bm": "bố mẹ",
    "ph": "phụ huynh",
    "ac": "anh chị",
    "ace": "anh chị em",
    "th": "thằng",

    # ── D. Phủ định & Khẳng định ──
    "ko": "không",
    "k": "không",
    "kh": "không",
    "khg": "không",
    "kô": "không",
    "hok": "không",
    "hong": "không",
    "hẻm": "không",
    "hem": "không",
    "hổng": "không",
    "khum": "không",
    "khong": "không",
    "hăm": "không",
    "đc": "được",
    "dc": "được",
    "dk": "được không",
    "đk": "được không",
    "chx": "chưa",
    "chwa": "chưa",
    "xog": "xong",
    "r": "rồi",
    "gòi": "rồi",
    "rùi": "rồi",
    "zồi": "rồi",
    "vch": "vãi chưởng",
    "đhs": "đéo hiểu sao",
    "dhs": "đéo hiểu sao",
    "lsao": "làm sao",
    "nnao": "như nào",
    "vcl": "vãi cả lờ",
    "nhm": "nhưng mà",   
    "nma": "nhưng mà",
    "nm": "nhưng mà",
    "bgio": "bao giờ",
    "tbay": "tụi bây",
    "ch": "chưa",
    "kgi": "kiểu gì",
    "v1": "vòng 1",
    "trc": "trước",
    "ông": "ông",


    # ── E. Từ nghi vấn, Liên từ & Trạng từ ──
    "j": "gì",
    "giè": "gì",
    "s": "sao",
    "ntn": "như thế nào",
    "bth": "bình thường",
    "bthg": "bình thường",
    "bik": "biết",
    "pít": "biết",
    "trùi": "trời",
    "chời": "trời",
    "chòi": "trời",
    "mụt": "một",
    "dị": "vậy",
    "cx": "cũng",
    "vs": "với",
    "lm": "làm",
    "lèm": "làm",
    "nhg": "nhưng",
    "nma": "nhưng mà",
    "thui": "thôi",
    "thoy": "thôi",
    "chg": "chẳng",
    "or": "hoặc",
    "v": "vậy",
    "z": "vậy",
    "zậy": "vậy",
    "thía": "thế",
    "bn": "bao nhiêu",
    "bnn": "bao nhiêu",
    "bnhiu": "bao nhiêu",
    "bnhieu": "bao nhiêu",
    "nhiu": "nhiều",
    "nhìu": "nhiều",
    "thặc": "thật",
    "đún": "đúng",
    "đúm": "đúng",
    "khéc": "khác",
    "cừi": "cười",
    "đou": "đâu",

    # ── F. Khen ngợi, Vẻ ngoài & Dễ thương ──
    "xink": "xinh",
    "xik": "xinh",
    "xưn": "xinh",
    "dthw": "dễ thương",
    "dth": "dễ thương",
    "kute": "đáng yêu",
    "cute": "đáng yêu",

    # ── G. Mạng xã hội, Công nghệ & Mua sắm ──
    "đt": "điện thoại",
    "dt": "điện thoại",
    "đth": "điện thoại",
    "tl": "trả lời",
    "rep": "trả lời",
    "cmt": "bình luận",
    "bl": "bình luận",
    "fb": "Facebook",
    "ig": "Instagram",
    "tt": "TikTok",
    "acc": "tài khoản",
    "stt": "bài đăng",
    "avt": "ảnh đại diện",
    "ib": "nhắn tin",
    "nt": "nhắn tin",
    "tn": "tin nhắn",
    "nch": "nói chuyện",
    "fl": "theo dõi",
    "unf": "hủy theo dõi",
    "unfl": "hủy theo dõi",
    "sp": "sản phẩm",
    "pass": "nhượng lại",
    "ord": "đặt hàng",
    "ship": "giao hàng",
    "freeship": "miễn phí giao hàng",
    "vid": "video",
    "pic": "hình ảnh",
    "tg": "thời gian",
    "cs": "cuộc sống",
    "sd": "sử dụng",
    "kb": "không biết",
    "bh": "bây giờ",
    "bjo": "bây giờ",
    "sđt": "số điện thoại",
    "sdt": "số điện thoại",
    "qđ": "quyết định",
    "nv": "nhân viên",
    "gt": "giới thiệu",
    "pt": "phát triển",
    "ktra": "kiểm tra",
    "xđ": "xác định",
    "xd": "xác định",
    "qtam": "quan tâm",
    "tcam": "tình cảm",
    "hp": "hạnh phúc",
    "hnay": "hôm nay",
    "hqua": "hôm qua",
    "hqa": "hôm qua",
    "nmai": "ngày mai",

    # ── H. Lóng Gen Z & Hot Trend TikTok ──
    "simp": "mê muội",
    "cook": "cút",
    "cringe": "ngượng chín mặt",
    "overthinking": "suy nghĩ quá nhiều",
    "healing": "chữa lành",
    "toxic": "độc hại",
    "ghost": "bặt vô âm tín",
    "lowkey": "kín tiếng",
    "highkey": "công khai",
    "delulu": "ảo tưởng",
    "gke": "ghê",
    "mlem": "ngon lành",
    "keo": "keo lỳ",

    # ── I. Cảm thán & Giảm nhẹ từ ngữ mạng (đọc êm tai) ──
    "vđ": "rất",
    "clgt": "cái quái gì thế",
    "cđg": "cái quái gì thế",
    "đm": "đậu má",
    "dm": "đậu má",
    "đmm": "đậu má",
    "đcm": "đậu má",
    "dcm": "đậu má",
    "đkm": "đậu má",
    "dkm": "đậu má",
    "đù": "đù má",
    "hmu": "hu hu",
    "tr oi": "trời ơi",
    "trời ui": "trời ơi",
    "trùi ui": "trời ơi",
    "tr má": "trời má",
    "trời má": "trời má",
    "chời má": "trời má",
    "tks": "cảm ơn",
    "thanks": "cảm ơn",
    "thx": "cảm ơn",
    "plz": "làm ơn",
    "pls": "làm ơn",
}

# Sắp xếp các từ khóa đơn lẻ theo độ dài giảm dần để ưu tiên từ dài trước
_SORTED_KEYS = sorted(ABBREVIATIONS.keys(), key=len, reverse=True)
_WORD_REGEX = re.compile(
    r"(?<!\w)(" + "|".join(re.escape(k) for k in _SORTED_KEYS) + r")(?!\w)",
    re.IGNORECASE
)


def normalize_vietnamese_text(text: str) -> str:
    """Chuẩn hóa văn bản tiếng Việt: giải mã từ viết tắt và lóng Gen Z thành từ đầy đủ.
    
    Args:
        text: Văn bản bài viết hoặc bình luận gốc từ Threads/TikTok/Facebook.
        
    Returns:
        Văn bản đã được chuẩn hóa để giọng AI (TTS) đọc trôi chảy, tự nhiên 100%.
    """
    if not text:
        return ""

    result = text

    # Bước 1. Khớp các cụm từ ghép Gen Z / MXH (j z tr, u là tr, chầm kẽm, check var...)
    for pattern, repl in PHRASE_RULES:
        result = pattern.sub(repl, result)

    # Bước 2. Áp dụng quy tắc regex (số đo: 12h, 15p, 50k, 2tr, 3 củ, 2 lít, haizz, haha...)
    for pattern, repl in REGEX_RULES:
        result = pattern.sub(repl, result)

    # Bước 3. Áp dụng từ điển từ viết tắt đơn lẻ (giữ nguyên chữ hoa/thường hợp lý)
    def _replace_word(match: re.Match) -> str:
        w = match.group(0).lower()
        full = ABBREVIATIONS.get(w, match.group(0))
        # Nếu từ gốc viết hoa chữ cái đầu -> viết hoa kết quả
        if match.group(0).istitle():
            return full.capitalize()
        if match.group(0).isupper() and len(w) <= 3:
            return full.capitalize()
        return full

    result = _WORD_REGEX.sub(_replace_word, result)

    # Bước 4. Làm sạch khoảng trắng thừa
    result = re.sub(r"[ \t]+", " ", result).strip()
    return result
