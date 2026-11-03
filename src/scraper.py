"""Mở bài Threads bằng Playwright, đọc bài viết + bình luận.

Cách làm: bắt các response JSON (GraphQL) mà trang tự gọi và quét thêm các thẻ
<script type="application/json"> nhúng sẵn trong HTML. Sau đó tìm đệ quy mọi
object trông giống một bài đăng (có user, caption, like_count). Cách này không
phụ thuộc vào class CSS nên ít vỡ hơn khi Threads đổi giao diện.
"""
from __future__ import annotations

import base64
import json
import os
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path

import requests

_runtime_browsers = Path(__file__).resolve().parent.parent / "runtime" / "browsers"
if _runtime_browsers.exists():
    os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(_runtime_browsers))


@dataclass
class Post:
    code: str
    username: str
    text: str
    likes: int = 0
    replies: int = 0
    reposts: int = 0
    shares: int = 0
    views: int | None = None
    taken_at: int | None = None
    avatar_b64: str | None = None  # data URI của ảnh đại diện
    image_b64: str | None = None   # data URI của ảnh đính kèm (nếu bài hoặc bình luận có ảnh)
    gender: str | None = None

    @property
    def date_str(self) -> str:
        if not self.taken_at:
            return ""
        return datetime.fromtimestamp(self.taken_at).strftime("%d/%m/%y")


@dataclass
class Thread:
    url: str
    main: Post
    comments: list[Post] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)

    @staticmethod
    def from_json(s: str) -> "Thread":
        d = json.loads(s)
        return Thread(
            url=d["url"],
            main=Post(**d["main"]),
            comments=[Post(**c) for c in d["comments"]],
        )


def shortcode_from_url(url: str) -> str:
    """Trích xuất mã bài viết từ URL Threads (hỗ trợ /post/, /t/, và /share/)."""
    m = re.search(r"/(?:post|t|share)/([A-Za-z0-9_-]+)", url)
    if not m:
        raise ValueError(f"Không tìm thấy mã bài trong link: {url}")
    return m.group(1)


def _normalize_gender(value) -> str | None:
    """Chuẩn hóa trường giới tính tường minh nếu Threads có cung cấp."""
    if not isinstance(value, str):
        return None
    value = value.strip().lower()
    if value in {"male", "man", "m", "nam"}:
        return "male"
    if value in {"female", "woman", "f", "nu", "nữ"}:
        return "female"
    return None


# ---------------------------------------------------------------- parsing ---

def _extract_image_url(node: dict) -> str | None:
    """Trích xuất URL ảnh nếu bài viết hoặc bình luận có đính kèm hình ảnh/media."""
    if not isinstance(node, dict):
        return None

    # Bỏ qua nếu là bài thuần văn bản (media_type=19 trên Threads)
    if node.get("media_type") == 19:
        return None

    # 1. Album / Carousel nhiều ảnh
    carousel = node.get("carousel_media")
    if isinstance(carousel, list) and carousel:
        first = carousel[0]
        if isinstance(first, dict):
            cands = first.get("image_versions2", {}).get("candidates", [])
            if isinstance(cands, list) and cands and isinstance(cands[0], dict):
                url = cands[0].get("url")
                if url:
                    return url

    # 2. Đơn ảnh hoặc video thumbnail
    img_versions = node.get("image_versions2")
    if isinstance(img_versions, dict):
        cands = img_versions.get("candidates", [])
        if isinstance(cands, list) and cands and isinstance(cands[0], dict):
            url = cands[0].get("url")
            if url:
                return url

    # 3. Ảnh động GIF
    gif_media = node.get("gif_media")
    if isinstance(gif_media, dict):
        images = gif_media.get("images", {})
        if isinstance(images, dict):
            for k in ("original", "fixed_height", "downsized_large"):
                item = images.get(k)
                if isinstance(item, dict) and item.get("url"):
                    return item["url"]

    return None


def _walk(node, out: dict):
    """Duyệt đệ quy, gom mọi dict giống một bài đăng Threads."""
    if isinstance(node, dict):
        user = node.get("user")
        caption = node.get("caption")
        if (
            isinstance(user, dict)
            and user.get("username")
            and "like_count" in node
            and (node.get("code") or node.get("pk"))
        ):
            text = ""
            if isinstance(caption, dict):
                text = caption.get("text") or ""
            key = node.get("code") or str(node.get("pk"))
            info = node.get("text_post_app_info") or {}
            post = {
                "code": node.get("code") or key,
                "username": user["username"],
                "text": text.strip(),
                "likes": int(node.get("like_count") or 0),
                "replies": int(info.get("direct_reply_count") or 0),
                "reposts": int(info.get("repost_count") or 0),
                "shares": int(info.get("reshare_count") or 0),
                "views": node.get("view_count") or info.get("view_count"),
                "taken_at": node.get("taken_at"),
                "avatar_url": user.get("profile_pic_url"),
                "image_url": _extract_image_url(node),
                "gender": _normalize_gender(user.get("gender")),
            }
            # Giữ bản có nhiều thông tin hơn nếu gặp trùng lặp qua GraphQL fragments
            old = out.get(key)
            if old is not None:
                if not post.get("image_url") and old.get("image_url"):
                    post["image_url"] = old["image_url"]
                if len(old.get("text", "")) > len(post["text"]):
                    post["text"] = old["text"]
            out[key] = post
        for v in node.values():
            _walk(v, out)
    elif isinstance(node, list):
        for v in node:
            _walk(v, out)


# ─── BỘ LỌC QUẢNG CÁO, SPAM & LINK LIÊN KẾT NGOÀI ─────────────────────────────
_EXTERNAL_LINK_REGEX = re.compile(
    r"(?:https?://\S+)|"
    r"(?:www\.[a-zA-Z0-9-]+\.[a-zA-Z0-9-.\/]+)|"
    r"\b(?:bit\.ly|tinyurl\.com|t\.me|zalo\.me|shopee\.vn|shope\.ee|lazada\.vn|"
    r"s\.lazada\.vn|linktr\.ee|bio\.link|beacons\.ai|taplink\.cc)\b/\S*|"
    r"\b[a-zA-Z0-9-]+\.(?:com|vn|ly|ee|me|link|ai|io|top|xyz|site)\b/\S+",
    re.IGNORECASE,
)

_SPAM_AD_PATTERNS = [
    # 1. Kéo link bio, link trang cá nhân
    re.compile(r"\b(?:link\s+(?:ở|trên|tại|trong)\s+bio|check\s+bio|xem\s+bio|link\s+bio|ở\s+bio\s+ạ|vào\s+bio)\b", re.I),
    re.compile(r"\b(?:link\s+mua(?:\s+hàng)?|mua\s+ở\s+link|bấm\s+vào\s+link|nhấp\s+link|link\s+dưới\s+cmt)\b", re.I),

    # 2. Zalo / Telegram / Kéo nhóm kín
    re.compile(r"\b(?:vào\s+nhóm\s+zalo|kết\s+bạn\s+zalo|liên\s+hệ\s+zalo|ib\s+zalo|nhóm\s+zalo|zalo\s*:?\s*0\d{8,10})\b", re.I),
    re.compile(r"\b(?:link\s+tele(?:gram)?|nhóm\s+tele|kênh\s+tele|vào\s+tele)\b", re.I),

    # 3. Tuyển dụng CTV, lừa đảo việc nhẹ lương cao, kéo vốn
    re.compile(r"\b(?:tuyển\s+ctv|tuyển\s+dụng\s+ctv|việc\s+nhẹ\s+lương\s+cao|kiếm\s+tiền\s+online)\b", re.I),
    re.compile(r"\b(?:hoa\s+hồng\s+cao|vốn\s+ít|lãi\s+ngày|kéo\s+vốn|vào\s+bờ|thu\s+nhập\s+thụ\s+động)\b", re.I),
    re.compile(r"\b(?:cho\s+vay|hỗ\s+trợ\s+nợ\s+xấu|giải\s+ngân\s+nhanh|vay\s+tiền\s+nóng)\b", re.I),

    # 4. Tài xỉu, cá độ, cờ bạc mạng
    re.compile(r"\b(?:tài\s+xỉu|game\s+bài|nạp\s+rút\s+1\s*:\s*1|nhận\s+code\s+trải\s+nghiệm|nhà\s+cái|kèo\s+bóng)\b", re.I),

    # 5. Mời chào mua bán, spam shop
    re.compile(r"\b(?:inbox\s+shop|ib\s+shop|ghé\s+shop|bán\s+acc|bán\s+nick|mua\s+bán\s+acc)\b", re.I),
    re.compile(r"\b(?:clip\s+full\s+ở|xem\s+full\s+clip|ảnh\s+full\s+ở|full\s+video\s+ở)\b", re.I),
]


def is_spam_or_ad(text: str) -> bool:
    """Kiểm tra xem bình luận có phải là quảng cáo, spam hoặc gắn link ngoài không."""
    if not text:
        return False
    if _EXTERNAL_LINK_REGEX.search(text):
        return True
    for pat in _SPAM_AD_PATTERNS:
        if pat.search(text):
            return True
    return False


def parse_payloads(payloads: list, main_code: str, top: int = 5,
                   max_chars: int = 300, min_chars: int = 8,
                   include_author_replies: bool = False):
    """Trả về (main_dict, [comment_dict...]) đã lọc sạch quảng cáo, link ngoài và sắp theo lượt thích."""
    found: dict = {}
    for p in payloads:
        _walk(p, found)

    main = found.get(main_code)
    if main is None and found:
        main = max(found.values(), key=lambda p: (p.get("replies", 0), p.get("likes", 0)))

    if main is None:
        raise RuntimeError(
            "Không đọc được nội dung bài viết. Có thể Threads yêu cầu đăng nhập, "
            "IP bị hạn chế hoặc Threads đã đổi cấu trúc dữ liệu (xem README, mục Đăng nhập)."
        )

    main_id = main["code"]
    raw_comments = [
        p for k, p in found.items()
        if k != main_id and p.get("code") != main_id
        and (include_author_replies or p["username"] != main["username"])
        and (min_chars <= len(p["text"]) <= max_chars or (p.get("image_url") and len(p["text"]) <= max_chars))
    ]

    # Loại bỏ bình luận quảng cáo, spam, gắn link ngoài
    clean_comments = [p for p in raw_comments if not is_spam_or_ad(p.get("text", ""))]
    clean_comments.sort(key=lambda p: p["likes"], reverse=True)
    return main, clean_comments[:top]


# --------------------------------------------------------------- fetching ---

def _avatar_data_uri(url: str | None) -> str | None:
    if not url:
        return None
    if url.startswith("data:"):
        return url
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        mime = r.headers.get("content-type", "image/jpeg").split(";")[0]
        return f"data:{mime};base64,{base64.b64encode(r.content).decode()}"
    except Exception:
        return None


def _image_data_uri(url: str | None, max_dim: int = 1080) -> str | None:
    """Tải và nén ảnh đính kèm thành base64 data URI (giới hạn max_dim để card nhẹ và render nhanh)."""
    if not url:
        return None
    if url.startswith("data:"):
        return url
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        from PIL import Image
        import io
        im = Image.open(io.BytesIO(r.content))
        if im.mode not in ("RGB", "RGBA"):
            im = im.convert("RGB")
        w, h = im.size
        if max(w, h) > max_dim:
            scale = max_dim / max(w, h)
            im = im.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        buf = io.BytesIO()
        im.convert("RGB").save(buf, format="JPEG", quality=85)
        b64 = base64.b64encode(buf.getvalue()).decode()
        return f"data:image/jpeg;base64,{b64}"
    except Exception:
        # Fallback raw data URI nếu Pillow không mở được
        try:
            mime = r.headers.get("content-type", "image/jpeg").split(";")[0]
            return f"data:{mime};base64,{base64.b64encode(r.content).decode()}"
        except Exception:
            return None


def fetch_thread(url: str, top: int = 5, max_chars: int = 300,
                 storage_state: str | None = None, headless: bool = True,
                 scrolls: int = 8, include_author_replies: bool = False) -> Thread:
    from playwright.sync_api import sync_playwright

    code = shortcode_from_url(url)
    payloads: list = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless, args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"])
        try:
            ctx = browser.new_context(
                locale="vi-VN",
                viewport={"width": 1280, "height": 1800},
                storage_state=storage_state or None,
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
                ),
            )
            page = ctx.new_page()

            def on_response(resp):
                try:
                    if "graphql" in resp.url and "json" in (resp.headers.get("content-type") or ""):
                        payloads.append(resp.json())
                except Exception:
                    pass

            page.on("response", on_response)
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(3000)

            # Cập nhật lại code và url nếu trang chuyển hướng (như link /share/ hoặc /t/)
            final_url = page.url
            if final_url and final_url != url:
                try:
                    new_code = shortcode_from_url(final_url)
                    if new_code:
                        code = new_code
                        url = final_url
                except Exception:
                    pass

            # cuộn để Threads tải thêm bình luận
            for _ in range(scrolls):
                page.mouse.wheel(0, 2500)
                page.wait_for_timeout(1200)

            # dữ liệu nhúng sẵn trong HTML
            for raw in page.eval_on_selector_all(
                'script[type="application/json"]', "els => els.map(e => e.textContent)"
            ):
                try:
                    payloads.append(json.loads(raw))
                except Exception:
                    pass
        finally:
            browser.close()

    main_d, comments_d = parse_payloads(
        payloads, code, top=top, max_chars=max_chars,
        include_author_replies=include_author_replies
    )

    def build(d) -> Post:
        d = dict(d)
        avatar = _avatar_data_uri(d.pop("avatar_url", None) or d.pop("avatar_b64", None))
        image = _image_data_uri(d.pop("image_url", None) or d.pop("image_b64", None))
        return Post(avatar_b64=avatar, image_b64=image, **d)

    return Thread(url=url, main=build(main_d), comments=[build(c) for c in comments_d])
