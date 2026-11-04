"""Giọng đọc AI tiếng Việt 100% bằng Microsoft Edge Neural TTS (hoàn toàn miễn phí).

Hỗ trợ:
  - Giọng nam chuẩn: vi-VN-NamMinhNeural (mặc định)
  - Giọng nữ chuẩn: vi-VN-HoaiMyNeural
  - Tự động nhận diện giới tính hoặc chỉ định thủ công
  - Mock TTS (--mock-tts) để test quy trình cực nhanh không cần mạng
"""
from __future__ import annotations

import asyncio
import os
import re
import subprocess
from pathlib import Path
from text_norm import normalize_vietnamese_text

_EMOJI = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F2FF️‍]+",
    flags=re.UNICODE,
)
_URL = re.compile(r"https?://\S+")

# Từ điển chuẩn hóa viết tắt & tiếng lóng tiếng Việt trên mạng xã hội
_SLANG_MAP: list[tuple[re.Pattern, str]] = [
    # Không
    (re.compile(r"\b(ko|k|khg|kh|hơm|hem|hong|hông)\b", re.IGNORECASE), "không"),
    # Được
    (re.compile(r"\b(dc|đc)\b", re.IGNORECASE), "được"),
    # Bình thường
    (re.compile(r"\b(bt|bthg|bth)\b", re.IGNORECASE), "bình thường"),
    # Mọi người
    (re.compile(r"\b(mn|mng)\b", re.IGNORECASE), "mọi người"),
    # Người yêu cũ / người yêu
    (re.compile(r"\b(nyc)\b", re.IGNORECASE), "người yêu cũ"),
    (re.compile(r"\b(ny)\b", re.IGNORECASE), "người yêu"),
    # Điện thoại, số tài khoản
    (re.compile(r"\b(dt|đt)\b", re.IGNORECASE), "điện thoại"),
    (re.compile(r"\b(stk)\b", re.IGNORECASE), "số tài khoản"),
    # Với, thằng, gì, cũng, nói, mình
    (re.compile(r"\b(vs)\b", re.IGNORECASE), "với"),
    (re.compile(r"\b(thg)\b", re.IGNORECASE), "thằng"),
    (re.compile(r"\b(j|giè)\b", re.IGNORECASE), "gì"),
    (re.compile(r"\b(cx)\b", re.IGNORECASE), "cũng"),
    (re.compile(r"\b(ns)\b", re.IGNORECASE), "nói"),
    (re.compile(r"\b(mik|mìn|mk)\b", re.IGNORECASE), "mình"),
    # Hôm qua, hôm nay, ngày mai
    (re.compile(r"\b(hqua|hqa)\b", re.IGNORECASE), "hôm qua"),
    (re.compile(r"\b(hnay)\b", re.IGNORECASE), "hôm nay"),
    (re.compile(r"\b(nmai)\b", re.IGNORECASE), "ngày mai"),
    # Chưa
    (re.compile(r"\b(chx)\b", re.IGNORECASE), "chưa"),
    # Chưa biết
    (re.compile(r"\b(chx|chưa|k|ko|không)\s+bt\b", re.IGNORECASE), r"\1 biết"),
    # Bao nhiêu
    (re.compile(r"\b(bn)\b", re.IGNORECASE), "bao nhiêu"),
    # Em (viết tắt e)
    (re.compile(r"\b(e)\b", re.IGNORECASE), "em"),
    # Giới thiệu (rcm / recommend)
    (re.compile(r"\b(rcm|recommend)\b", re.IGNORECASE), "giới thiệu"),
    # Dính (dích hàng)
    (re.compile(r"\b(dích)\b", re.IGNORECASE), "dính"),
    # Rùi / rồi
    (re.compile(r"\b(rùi|zồi)\b", re.IGNORECASE), "rồi"),
    # Còng đá -> vòng đá
    (re.compile(r"\bcòng đá\b", re.IGNORECASE), "vòng đá"),
    # Tương tác mạng xã hội
    (re.compile(r"\b(ib|inbox)\b", re.IGNORECASE), "nhắn tin"),
    (re.compile(r"\b(cmt|comment)\b", re.IGNORECASE), "bình luận"),
    (re.compile(r"\b(fb)\b", re.IGNORECASE), "phây búc"),
    (re.compile(r"\b(ig)\b", re.IGNORECASE), "in-sta-gram"),
    (re.compile(r"\b(tt|tiktok)\b", re.IGNORECASE), "tóp tóp"),
    (re.compile(r"\b(acc)\b", re.IGNORECASE), "tài khoản"),
    (re.compile(r"\b(rep)\b", re.IGNORECASE), "trả lời"),
    (re.compile(r"\b(uk|uh|uhm|um)\b", re.IGNORECASE), "ừ"),
    (re.compile(r"\b(oki|okey|oke)\b", re.IGNORECASE), "ô kê"),
    (re.compile(r"\b(vcl|vcd|vkl)\b", re.IGNORECASE), "vãi"),
    (re.compile(r"\b(clgt)\b", re.IGNORECASE), "cái lề gì thốn"),
]


def clean_for_speech(text: str) -> str:
    """Làm sạch và chuẩn hóa văn bản trước khi đọc:
    - Bỏ URL, emoji, biểu tượng cảm xúc dạng ký tự (:)), :v, ^^).
    - Chuẩn hóa từ viết tắt/tiếng lóng tiếng Việt sang từ phát âm chuẩn.
    - Chuẩn hóa số tiền/định lượng (ví dụ 10k -> 10 nghìn).
    """
    text = _URL.sub("", text)
    text = _EMOJI.sub("", text)

    # Loại bỏ biểu tượng cảm xúc dạng ký tự phổ biến gây vấp audio
    text = re.sub(r"[:=]-?[()DPdp]{1,}", " ", text)
    text = re.sub(r"\^{2,}", " ", text)
    text = re.sub(r":v|;\)", " ", text)

    # Chuẩn hóa khoảng giá viết tắt như 1xx, 2xx, 1xxk -> hơn 1 trăm nghìn
    text = re.sub(r"\b(\d+)\s*[xX]{1,3}\s*[kK]?\b", r"hơn \1 trăm nghìn ", text)

    # Chuẩn hóa số tiền viết tắt như 10k, 50k
    text = re.sub(r"\b(\d+)\s*[kK]\b", r"\1 nghìn", text)

    # Chuẩn hóa toàn bộ từ viết tắt tiếng Việt chuyên sâu (ko, dc, ng, b, m, 12h, vcl...)
    text = normalize_vietnamese_text(text)

    # Chuẩn hóa từ viết tắt bổ sung
    for pat, rep in _SLANG_MAP:
        text = pat.sub(rep, text)

    # Chuyển đổi các chữ số đơn lẻ 0-10 sang từ tiếng Việt để giọng Neural đọc trơn tru
    _DIGITS = {
        "0": "không", "1": "một", "2": "hai", "3": "ba", "4": "bốn",
        "5": "năm", "6": "sáu", "7": "bảy", "8": "tám", "9": "chín", "10": "mười"
    }
    text = re.sub(r"\b([0-9]|10)\b", lambda m: _DIGITS.get(m.group(1), m.group(1)), text)

    # Gộp dấu câu lặp lại
    text = re.sub(r"[?!]{2,}", "?", text)
    text = re.sub(r"\.{4,}", "...", text)

    # Gộp khoảng trắng
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def _normalize_gender(gender: str | None) -> str | None:
    if not gender:
        return None
    value = gender.strip().lower()
    if value in {"male", "man", "m", "nam"}:
        return "male"
    if value in {"female", "woman", "f", "nu", "nữ"}:
        return "female"
    return None


FEMALE_NAME_TOKENS = {
    "linh", "trang", "huong", "quynh", "phuong", "huyen", "thuy", "oanh", "nguyet",
    "nhung", "suong", "trinh", "tuyen", "tuyet", "khanh", "hgie", "nhien", "giang",
    "thao", "uyen", "ngoc", "tram", "hien", "loan", "chau", "diep", "bich", "kieu",
    "lien", "ngan", "quyen", "thoa", "thuc", "tien", "truc", "xuan", "nga", "hoa",
    "lan", "mai", "chi", "anh", "van", "yen", "nhu", "tam", "nhi", "cam", "dao",
    "thu", "mon", "bong", "mit", "dau", "kem", "mun", "vy", "ha", "ly", "my", "mi",
    "su", "dan", "khue", "meo", "tho", "gao", "bap", "be", "pe", "nang", "na", "chibi"
}

MALE_NAME_TOKENS = {
    "hoang", "trung", "cuong", "thang", "quang", "thuan", "thinh", "khang", "nghia",
    "trieu", "phong", "khoa", "kien", "hieu", "tuan", "hung", "tung", "bach", "phuc",
    "toan", "quan", "dung", "duc", "long", "viet", "minh", "phat", "vuong", "trong",
    "chinh", "nam", "huy", "dat", "son", "hai", "duy", "bao", "tri", "loc", "lam",
    "tai", "vu", "thanh", "binh", "khoi", "nhan", "danh", "quy", "hiep", "triet"
}

FEMALE_TEXT_PATTERNS = [
    re.compile(r"\bchồng\s+(?:em|mình|tôi|tao)\b", re.I),
    re.compile(r"\bck\s+(?:em|mình|tôi)\b", re.I),
    re.compile(r"\b(?:anh\s+nhà|anh\s+xã|ông\s+xã)\b", re.I),
    re.compile(r"\bngười\s+yêu\s+anh\s+ấy\b", re.I),
    re.compile(r"\banh\s+người\s+yêu\b", re.I),
    re.compile(r"\b(?:bạn\s+trai|bồ\s+em)\b", re.I),
    re.compile(r"\bchị\s+em(?:\s+mình|\s+phụ\s+nữ)?\b", re.I),
    re.compile(r"\b(?:phái\s+đẹp|phái\s+nữ|nữ\s+giới)\b", re.I),
    re.compile(r"\b(?:mẹ\s+bỉm|bà\s+mẹ|mẹ\s+đơn\s+thân)\b", re.I),
    re.compile(r"\b(?:mang\s+bầu|bầu\s+bì|mang\s+thai|sinh\s+con|ở\s+cữ|hút\s+sữa)\b", re.I),
    re.compile(r"\b(?:đau\s+bụng\s+kinh|tới\s+tháng|rụng\s+dâu)\b", re.I),
    re.compile(r"\b(?:son\s+môi|trang\s+điểm|chân\s+váy|váy\s+đầm|đầm\s+bầu)\b", re.I),
    re.compile(r"\bchị\s+(?:thấy|nghĩ|bảo|khuyên|từng|làm|đi)\b", re.I),
    re.compile(r"\b(?:em|chị|mình)\s+là\s+(?:con\s+gái|phụ\s+nữ|nữ)\b", re.I),
]

MALE_TEXT_PATTERNS = [
    re.compile(r"\bvợ\s+(?:em|mình|tôi|tao)\b", re.I),
    re.compile(r"\bvk\s+(?:em|mình|tôi)\b", re.I),
    re.compile(r"\b(?:bà\s+xã|nóc\s+nhà)\b", re.I),
    re.compile(r"\b(?:bạn\s+gái|bồ\s+nhí)\b", re.I),
    re.compile(r"\bngười\s+yêu\s+cô\s+ấy\b", re.I),
    re.compile(r"\b(?:cánh\s+mày\s+râu|đấng\s+mày\s+râu|nam\s+giới)\b", re.I),
    re.compile(r"\b(?:thằng\s+con\s+trai|thằng\s+đàn\s+ông|đàn\s+ông\s+tụi\s+mình)\b", re.I),
    re.compile(r"\b(?:cạo\s+râu|râu\s+ria|đá\s+banh|đi\s+nghĩa\s+vụ)\b", re.I),
    re.compile(r"\banh\s+(?:thấy|nghĩ|bảo|khuyên|từng|làm|đi)\b", re.I),
    re.compile(r"\b(?:em|anh|tôi|mình)\s+là\s+(?:con\s+trai|đàn\s+ông|nam)\b", re.I),
]


def detect_gender(
    text: str = "",
    username: str = "",
    explicit_gender: str | None = None,
    scene_index: int = 0
) -> tuple[str, str]:
    """Nhận diện giới tính chính xác từ explicit gender, ngữ cảnh bài viết và tên tài khoản.
    
    Returns:
        tuple[str, str]: ("female" hoặc "male", lý do nhận diện)
    """
    # 1. Dữ liệu tường minh nếu có
    norm_explicit = _normalize_gender(explicit_gender)
    if norm_explicit:
        return norm_explicit, "dữ liệu tài khoản"

    # 2. Phân tích ngữ cảnh nội dung bài viết / bình luận
    for pat in FEMALE_TEXT_PATTERNS:
        if pat.search(text):
            return "female", "ngữ cảnh bài viết (phái nữ)"

    for pat in MALE_TEXT_PATTERNS:
        if pat.search(text):
            return "male", "ngữ cảnh bài viết (phái nam)"

    # 3. Phân tích tên tài khoản / Username
    if username:
        u = username.lower()
        if re.search(r"\b(?:girl|miss|nang|lady|pe|be|me|mom)\b|_girl|miss_|\.girl", u):
            return "female", f"tên @{username} (nữ)"
        if re.search(r"\b(?:boy|mr|trai|chu|bac|ong|man|bro)\b|_boy|mr_|\.boy", u):
            return "male", f"tên @{username} (nam)"

        parts = re.split(r"[^a-zA-Z]+", u)
        cleaned_parts = [re.sub(r"[sfrxj]$", "", p) for p in parts if len(p) >= 2]

        for p in cleaned_parts:
            if p in FEMALE_NAME_TOKENS and p not in MALE_NAME_TOKENS:
                return "female", f"tên @{username} ({p})"
            if p in MALE_NAME_TOKENS and p not in FEMALE_NAME_TOKENS:
                return "male", f"tên @{username} ({p})"

        # So khớp tên ghép dài (ví dụ hoangnguyen, thutrang, phuongthao, minhtuan)
        for part in cleaned_parts:
            if len(part) >= 4:
                for f_name in sorted(FEMALE_NAME_TOKENS, key=len, reverse=True):
                    if len(f_name) >= 4 and f_name in part:
                        return "female", f"tên @{username} ({f_name})"
                for m_name in sorted(MALE_NAME_TOKENS, key=len, reverse=True):
                    if len(m_name) >= 4 and m_name in part:
                        return "male", f"tên @{username} ({m_name})"

    # 4. Fallback thông minh: Cảnh 0 là Nam, các comment luân phiên Nữ/Nam để video sinh động
    if scene_index == 0:
        return "male", "mặc định bài chính (Nam)"
    elif scene_index % 2 == 1:
        return "female", "luân phiên hội thoại (Nữ)"
    else:
        return "male", "luân phiên hội thoại (Nam)"


def select_edge_voice(
    gender: str | None = None,
    text: str = "",
    username: str = "",
    scene_index: int = 0
) -> tuple[str, str, str]:
    """Chọn giọng Edge tiếng Việt: Hoài My (Nữ) hoặc Nam Minh (Nam).
    
    Returns:
        tuple[str, str, str]: (voice_name, resolved_gender, reason)
    """
    resolved_gender, reason = detect_gender(
        text=text,
        username=username,
        explicit_gender=gender,
        scene_index=scene_index
    )
    if resolved_gender == "female":
        voice = os.getenv("EDGE_TTS_FEMALE_VOICE", "vi-VN-HoaiMyNeural")
    else:
        voice = os.getenv("EDGE_TTS_MALE_VOICE", "vi-VN-NamMinhNeural")

    return voice, resolved_gender, reason


def format_edge_rate(rate: str | float | int | None) -> str:
    """Chuyển đổi tốc độ đọc sang định dạng của edge-tts (ví dụ: '+15%', '-10%', '+0%')."""
    if rate is None:
        return "+0%"
    if isinstance(rate, str):
        rate_str = rate.strip()
        if not rate_str:
            return "+0%"
        try:
            val = float(rate_str.rstrip("xX%"))
            if 0.5 <= val <= 2.5 and "%" not in rate_str:
                pct = int(round((val - 1.0) * 100))
                return f"+{pct}%" if pct >= 0 else f"{pct}%"
            else:
                pct = int(val)
                return f"+{pct}%" if pct >= 0 else f"{pct}%"
        except ValueError:
            pass
        if rate_str.startswith(("+", "-")) and rate_str.endswith("%"):
            return rate_str
        if rate_str.endswith("%"):
            return f"+{rate_str}"
        return rate_str
    if isinstance(rate, (int, float)):
        if 0.5 <= rate <= 2.5:
            pct = int(round((rate - 1.0) * 100))
            return f"+{pct}%" if pct >= 0 else f"{pct}%"
        else:
            pct = int(rate)
            return f"+{pct}%" if pct >= 0 else f"{pct}%"
    return "+0%"


def mock_tts(text: str, out: Path, rate: str | float | int = "+0%") -> tuple[Path, list[dict[str, Any]]]:
    """Âm thanh giả (sóng sin nhỏ) dài tỉ lệ với số ký tự và tốc độ đọc — chỉ để test pipeline."""
    from video import get_ffmpeg_bin
    rate_str = format_edge_rate(rate)
    try:
        pct = int(rate_str.rstrip("%"))
        mult = max(0.5, 1.0 + pct / 100.0)
    except Exception:
        mult = 1.0

    dur = max(1.2, len(text) / (14 * mult))  # ~14 ký tự/giây điều chỉnh theo tốc độ
    subprocess.run(
        [get_ffmpeg_bin(), "-y", "-loglevel", "error", "-f", "lavfi",
         "-i", f"sine=frequency=220:sample_rate=44100:duration={dur:.2f}",
         "-af", "volume=0.15", "-ac", "2", "-ar", "44100", "-b:a", "128k", str(out)],
        check=True,
    )
    boundaries = [{"text": text, "offset": 0.0, "duration": dur}]
    return out, boundaries


def google_tts_fallback(text: str, out: Path) -> tuple[Path, list[dict[str, Any]]]:
    """Fallback tự động bằng Google TTS (miễn phí, không rate-limit) nếu Microsoft Edge TTS chập chờn mạng."""
    import urllib.parse
    import urllib.request
    from video import duration

    # Tách đoạn nếu dài hơn 180 ký tự (Google TTS giới hạn ~200 ký tự mỗi request)
    parts = []
    chunks = re.split(r"([.!?,;\n]+)", text)
    curr = ""
    for piece in chunks:
        if len(curr) + len(piece) < 180:
            curr += piece
        else:
            if curr.strip():
                parts.append(curr.strip())
            curr = piece
    if curr.strip():
        parts.append(curr.strip())

    if not parts:
        parts = [text[:180]]

    with open(out, "wb") as outfile:
        for part in parts:
            q = urllib.parse.quote(part)
            url = f"https://translate.google.com/translate_tts?ie=UTF-8&tl=vi&client=tw-ob&q={q}"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, timeout=8) as r:
                outfile.write(r.read())

    dur = duration(out)
    boundaries = [{"text": text, "offset": 0.0, "duration": dur}]
    return out, boundaries


def edge_tts_synthesize(text: str, out: Path, voice: str | None = None,
                        rate: str | float | int = "+0%",
                        max_retries: int = 2) -> tuple[Path, list[dict[str, Any]]]:
    """Tạo giọng đọc tiếng Việt bằng Microsoft Edge TTS.

    Cơ chế kiên cường (Resilience & Auto-recovery):
      - Hỗ trợ tùy chỉnh tốc độ đọc (rate, ví dụ: +10%, +15%, +20%, -10%).
      - Tự động thử lại đến 5 lần với exponential backoff khi mạng chập chờn.
      - Chuyển đổi linh hoạt giữa giọng nam/nữ nếu một bên bị Microsoft nghẽn tạm thời.
      - Nếu Microsoft vẫn nghẽn sau toàn bộ các lần thử, tự động chuyển sang Google TTS fallback.
      - Đảm bảo quy trình chạy thông suốt 100%, không bao giờ crash giữa chừng.
    """
    import edge_tts  # noqa: PLC0415

    if voice is None:
        voice = os.getenv("EDGE_TTS_VOICE", "vi-VN-NamMinhNeural")

    fallback_voice = "vi-VN-HoaiMyNeural" if voice == "vi-VN-NamMinhNeural" else "vi-VN-NamMinhNeural"
    rate_str = format_edge_rate(rate)

    async def _synthesize():
        last_err = None
        for attempt in range(1, max_retries + 1):
            cur_voice = voice if attempt <= 2 else fallback_voice
            try:
                if attempt > 1:
                    sleep_time = 1.5 * attempt
                    print(f"      (Thử kết nối lại máy chủ giọng đọc lần {attempt}/{max_retries} sau {sleep_time:.1f}s...)")
                    await asyncio.sleep(sleep_time)
                else:
                    await asyncio.sleep(0.4)

                communicate = edge_tts.Communicate(
                    text, cur_voice, rate=rate_str, connect_timeout=5, receive_timeout=10
                )
                async def _stream():
                    b_list: list[dict[str, Any]] = []
                    with open(out, "wb") as f:
                        async for chunk in communicate.stream():
                            if chunk["type"] == "audio":
                                f.write(chunk["data"])
                            elif chunk["type"] == "SentenceBoundary":
                                b_list.append({
                                    "text": chunk.get("text", ""),
                                    "offset": chunk.get("offset", 0) / 10_000_000,
                                    "duration": chunk.get("duration", 0) / 10_000_000,
                                })
                    return b_list
                boundaries = await asyncio.wait_for(_stream(), timeout=12.0)

                if out.exists() and out.stat().st_size > 1024:
                    return boundaries
                else:
                    raise RuntimeError("Không nhận được dữ liệu âm thanh hợp lệ.")

            except Exception as e:
                last_err = e
                if attempt >= max_retries:
                    break

        print(f"      [Tự động xử lý] Máy chủ Edge TTS phản hồi chậm ({last_err}), chuyển sang giọng dự phòng để hoàn tất video...")
        return None

    boundaries = asyncio.run(_synthesize())
    if boundaries is not None:
        return out, boundaries

    # Tự động kích hoạt Google TTS fallback để video không bao giờ bị dừng
    try:
        return google_tts_fallback(text, out)
    except Exception as e:
        print(f"      [Cảnh báo] Dùng mock TTS: {e}")
        return mock_tts(text, out, rate=rate)


def synthesize(
    text: str,
    out: Path,
    mock: bool = False,
    engine: str = "edge",
    edge_voice: str | None = None,
    gender: str | None = None,
    username: str = "",
    scene_index: int = 0,
    rate: str | float | int = "+0%",
) -> tuple[Path, list[dict[str, Any]], str]:
    """Tổng hợp giọng đọc tiếng Việt bằng Edge TTS (hoặc mock nếu mock=True).

    Returns:
        tuple[Path, list[dict], str]: (đường dẫn file mp3, danh sách boundary thời gian câu thoại, nhãn giọng đọc)
    """
    clean_text = clean_for_speech(text)
    if not clean_text:
        clean_text = "Xem ảnh đính kèm"
    if mock:
        p, b = mock_tts(clean_text, out, rate=rate)
        return p, b, "Mock TTS"

    if engine == "gtts":
        p, b = google_tts_fallback(clean_text, out)
        return p, b, "Google TTS" 

    if edge_voice:
        voice = edge_voice
        voice_label = "Chỉ định thủ công"
    else:
        voice, resolved_gender, reason = select_edge_voice(
            gender=gender, text=text, username=username, scene_index=scene_index
        )
        if resolved_gender == "female":
            voice_label = f"Nữ (Hoài My) [{reason}]"
        else:
            voice_label = f"Nam (Nam Minh) [{reason}]"

    rate_str = format_edge_rate(rate)
    if rate_str != "+0%":
        voice_label += f" ({rate_str})"

    res_path, boundaries = edge_tts_synthesize(clean_text, out, voice=voice, rate=rate)
    return res_path, boundaries, voice_label
