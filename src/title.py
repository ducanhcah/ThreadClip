"""Tạo tiêu đề + hashtag để đăng TikTok (Thuật toán tự động thông minh, không cần AI hay API key)."""
from __future__ import annotations

import re
from scraper import Thread

DEFAULT_TAGS = ["#threads", "#topic", "#fyp", "#viral", "#xuhuong"]


def make_title(t: Thread, max_len: int = 90, **kwargs) -> str:
    """Tự động trích xuất câu mở đầu hay nhất từ bài Threads và gắn hashtag thịnh hành.
    
    Chạy 100% offline, nhanh tức thì, không cần kết nối API AI bên ngoài.
    """
    text = re.sub(r"\s+", " ", t.main.text).strip()
    text = re.sub(r"^(topic|chủ đề)\s*:\s*-?\s*", "", text, flags=re.I)

    # Lấy câu đầu tiên hoặc giới hạn độ dài
    first_sentence = re.split(r"[.!?\n]", text)[0].strip()
    if len(first_sentence) < 15 and len(text) > len(first_sentence):
        title_cand = text
    else:
        title_cand = first_sentence

    if len(title_cand) > max_len:
        title_cand = title_cand[: max_len - 1].rsplit(" ", 1)[0] + "…"

    return f"{title_cand}\n" + " ".join(DEFAULT_TAGS)
