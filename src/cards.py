"""Vẽ ảnh "chụp màn hình" của bài viết và bình luận theo kiểu giao diện Threads.

Thẻ được dựng bằng HTML rồi chụp bằng Chromium, hỗ trợ tiếng Việt, emoji và
chế độ sáng/tối (Dark Mode). Ảnh nền (lưới + gradient) vẽ bằng Pillow.
"""
from __future__ import annotations

import html
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from scraper import Post

_runtime_browsers = Path(__file__).resolve().parent.parent / "runtime" / "browsers"
if _runtime_browsers.exists():
    os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(_runtime_browsers))

W, H = 1080, 1920
CARD_W = 920


def get_icons(dark: bool = False) -> dict[str, str]:
    c_main = "#f3f5f7" if dark else "#111111"
    c_sub = "#8e8e93" if dark else "#333333"
    return {
        "back": f'<svg viewBox="0 0 24 24" width="40" height="40" fill="none" stroke="{c_main}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 5l-7 7 7 7"/></svg>',
        "bell": f'<svg viewBox="0 0 24 24" width="44" height="44" fill="none" stroke="{c_main}" stroke-width="2" stroke-linejoin="round"><path d="M6 17V11a6 6 0 1 1 12 0v6l1.5 2h-15z"/><path d="M10 21h4"/></svg>',
        "dots": f'<svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="{c_main}" stroke-width="2"><circle cx="12" cy="12" r="10"/><circle cx="7.5" cy="12" r="1" fill="{c_main}"/><circle cx="12" cy="12" r="1" fill="{c_main}"/><circle cx="16.5" cy="12" r="1" fill="{c_main}"/></svg>',
        "heart": '<svg viewBox="0 0 24 24" width="42" height="42" fill="#ff2d55"><path d="M12 21s-8-5.2-8-11a4.6 4.6 0 0 1 8-3 4.6 4.6 0 0 1 8 3c0 5.800-8 11-8 11z"/></svg>',
        "comment": f'<svg viewBox="0 0 24 24" width="42" height="42" fill="none" stroke="{c_sub}" stroke-width="2"><path d="M12 3a9 9 0 1 0 4 17l4 1-1-4A9 9 0 0 0 12 3z"/></svg>',
        "repost": f'<svg viewBox="0 0 24 24" width="42" height="42" fill="none" stroke="{c_sub}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3l3 3-3 3"/><path d="M4 11V9a3 3 0 0 1 3-3h13"/><path d="M7 21l-3-3 3-3"/><path d="M20 13v2a3 3 0 0 1-3 3H4"/></svg>',
        "send": f'<svg viewBox="0 0 24 24" width="42" height="42" fill="none" stroke="{c_sub}" stroke-width="2" stroke-linejoin="round"><path d="M21 3L3 10l7 3 3 7z"/></svg>',
        "threads": f'<svg viewBox="0 0 24 24" width="40" height="40" fill="none" stroke="{c_main}" stroke-width="2" stroke-linecap="round"><path d="M17.500 8.500C16.800 6 14.700 4.500 12 4.500 8 4.500 5.500 7.500 5.500 12s2.500 7.500 6.500 7.500c3.400 0 5.500-1.800 5.500-4 0-2.600-2.500-3.800-5-3.800-2 0-3 .9-3 2 0 1 1 1.800 2.500 1.800 2 0 3-1.500 3-4.500"/></svg>',
    }


def fmt_num(n: int | None) -> str:
    """13100 -> '13,1K' (kiểu hiển thị số quen thuộc)."""
    if n is None:
        return ""
    if n < 1000:
        return str(n)
    for div, suf in ((1_000_000, "M"), (1_000, "K")):
        if n >= div:
            v = f"{n / div:.1f}".replace(".", ",")
            if v.endswith(",0"):
                v = v[:-2]
            return v + suf
    return str(n)


def _avatar_html(post: Post, size: int) -> str:
    if post.avatar_b64:
        return f'<img class="av" style="width:{size}px;height:{size}px" src="{post.avatar_b64}">'
    letter = html.escape((post.username[:1] or "?").upper())
    return (f'<div class="av ph" style="width:{size}px;height:{size}px;'
            f'line-height:{size}px">{letter}</div>')


def _build_css(dark: bool = False, font_size: int = 36) -> str:
    bg_card = "#181818" if dark else "#ffffff"
    text_main = "#f3f5f7" if dark else "#111111"
    text_sub = "#8e8e93" if dark else "#777777"
    line_h = 1.45 if font_size < 35 else 1.5

    return f"""
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:transparent;font-family:"Helvetica Neue",Helvetica,Arial,"Noto Sans","Segoe UI",
  "Noto Color Emoji","Apple Color Emoji",sans-serif;color:{text_main}}}
.card{{width:{CARD_W}px;background:{bg_card};padding:30px 36px 32px}}
.hdr{{display:flex;align-items:center;justify-content:space-between;margin-bottom:34px}}
.hdr .l{{display:flex;align-items:center;gap:10px;font-size:38px;width:30%}}
.hdr .c{{text-align:center}}.hdr .c b{{font-size:40px;display:block}}
.hdr .c span{{font-size:27px;color:{text_sub}}}
.hdr .r{{display:flex;gap:30px;width:30%;justify-content:flex-end}}
.who{{display:flex;align-items:center;gap:22px;margin-bottom:22px}}
.av{{border-radius:50%;object-fit:cover;background:#ddd}}
.av.ph{{text-align:center;color:#fff;background:#8e8e93;font-size:36px;font-weight:600}}
.name{{font-size:36px;font-weight:700}}.date{{font-size:34px;color:{text_sub};font-weight:400;margin-left:10px}}
.who .tl{{margin-left:auto;display:flex;align-items:center;gap:8px;font-size:34px;font-weight:500}}
.txt{{font-size:{font_size}px;line-height:{line_h};white-space:pre-wrap;word-break:break-word}}
.post-img-box{{margin-top:22px;width:100%;border-radius:20px;overflow:hidden;max-height:500px;display:flex;justify-content:center;align-items:center;background:rgba(128,128,128,0.1);border:1px solid rgba(128,128,128,0.18)}}
.post-img{{width:100%;max-height:500px;object-fit:cover;display:block;border-radius:20px}}
.stats{{display:flex;gap:44px;margin-top:26px;font-size:32px;color:{text_sub};align-items:center}}
.stats div{{display:flex;align-items:center;gap:12px}}
.stats .h{{color:#ff2d55}}
"""


def _image_html(post: Post) -> str:
    if not post.image_b64:
        return ""
    return f'<div class="post-img-box"><img class="post-img" src="{post.image_b64}"></div>'


def _post_html(post: Post, icons: dict[str, str]) -> str:
    sub = f"<span>{fmt_num(post.views)} lượt xem</span>" if post.views else ""
    return f"""
<div class="card" id="c">
  <div class="hdr">
    <div class="l">{icons['back']}<span>Quay lại</span></div>
    <div class="c"><b>Thread</b>{sub}</div>
    <div class="r">{icons['bell']}{icons['dots']}</div>
  </div>
  <div class="who">{_avatar_html(post, 110)}
    <div class="name">{html.escape(post.username)}<span class="date">{post.date_str}</span></div>
    <div class="tl">{icons['threads']}<span>Threads</span></div>
  </div>
  <div class="txt">{html.escape(post.text)}</div>
  {_image_html(post)}
  <div class="stats">
    <div class="h">{icons['heart']}{fmt_num(post.likes)}</div>
    <div>{icons['comment']}{fmt_num(post.replies)}</div>
    <div>{icons['repost']}{fmt_num(post.reposts)}</div>
    <div>{icons['send']}{fmt_num(post.shares)}</div>
  </div>
</div>"""


def _comment_html(post: Post, icons: dict[str, str]) -> str:
    return f"""
<div class="card" id="c">
  <div class="who">{_avatar_html(post, 96)}
    <div class="name">{html.escape(post.username)}<span class="date">{post.date_str}</span></div>
  </div>
  <div class="txt">{html.escape(post.text)}</div>
  {_image_html(post)}
  <div class="stats">
    <div class="h">{icons['heart']}{fmt_num(post.likes)}</div>
    <div>{icons['comment']}{fmt_num(post.replies)}</div>
    <div>{icons['repost']}{fmt_num(post.reposts)}</div>
    <div>{icons['send']}{fmt_num(post.shares)}</div>
  </div>
</div>"""


def _outro_html(icons: dict[str, str], dark: bool = False, channel_name: str = "") -> str:
    bg_card = "#181818" if dark else "#ffffff"
    text_main = "#f3f5f7" if dark else "#111111"
    text_sub = "#8e8e93" if dark else "#666666"
    pill_bg = "rgba(255,255,255,0.06)" if dark else "rgba(0,0,0,0.04)"
    pill_border = "rgba(255,255,255,0.12)" if dark else "rgba(0,0,0,0.08)"
    channel_info = ""
    if channel_name:
        clean_name = channel_name.strip()
        if not clean_name.startswith("@") and " " not in clean_name:
            clean_name = f"@{clean_name}"
        channel_info = f'<div style="margin-top:22px;font-size:32px;font-weight:700;color:#38bdf8;">{html.escape(clean_name)}</div>'

    return f"""
<div class="card" id="c" style="text-align:center;padding:46px 36px 42px;">
  <div style="font-size:62px;margin-bottom:18px;letter-spacing:12px;">❤️ 💬 🔔</div>
  <div style="font-size:40px;font-weight:800;margin-bottom:16px;color:#38bdf8;">CẢM ƠN BẠN ĐÃ THEO DÕI!</div>
  <div style="font-size:35px;line-height:1.55;margin-bottom:28px;color:{text_main};">
    Hãy bấm <b>Follow kênh</b>, thả <b>Tim</b> và để lại <b>Bình luận</b> để đón xem những video mới nhất nhé! ✨
  </div>
  <div style="display:flex;justify-content:center;gap:36px;padding:20px 24px;background:{pill_bg};border-radius:40px;border:1px solid {pill_border};font-size:32px;font-weight:700;">
    <span style="color:#ff2d55;">❤️ Thả Tim</span>
    <span style="color:{text_sub};">💬 Bình luận</span>
    <span style="color:#38bdf8;">🔔 Follow</span>
  </div>
  {channel_info}
</div>"""


def _calc_font_size(text: str) -> int:
    """Tự động điều chỉnh cỡ chữ theo độ dài để nội dung hiển thị đầy đủ, không bị cắt cụt."""
    length = len(text)
    if length < 140:
        return 38
    elif length < 260:
        return 34
    else:
        return 30


def render_cards(main: Post, comments: list[Post], out_dir: Path,
                 dark: bool = False, render_outro: bool = True,
                 channel_name: str = "") -> tuple[Path, list[Path], Path | None]:
    """Chụp thẻ bài viết, từng thẻ bình luận và thẻ outro ra PNG trong suốt ở viền bo góc."""
    from playwright.sync_api import sync_playwright

    out_dir.mkdir(parents=True, exist_ok=True)
    main_png = out_dir / "post.png"
    comment_pngs: list[Path] = []
    outro_png: Path | None = None
    icons = get_icons(dark=dark)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"])
        try:
            page = browser.new_page(viewport={"width": CARD_W + 40, "height": 2600},
                                    device_scale_factor=1)

            def shoot(body: str, path: Path, font_size: int):
                css = _build_css(dark=dark, font_size=font_size)
                page.set_content(
                    f"<html><head><meta charset='utf-8'><style>{css}</style></head>"
                    f"<body>{body}</body></html>"
                )
                page.wait_for_timeout(150)
                page.locator("#c").screenshot(path=str(path), omit_background=True)

            shoot(_post_html(main, icons), main_png, _calc_font_size(main.text))
            for i, c in enumerate(comments, 1):
                p = out_dir / f"comment_{i}.png"
                shoot(_comment_html(c, icons), p, _calc_font_size(c.text))
                comment_pngs.append(p)

            if render_outro:
                outro_png = out_dir / "outro.png"
                shoot(_outro_html(icons, dark=dark, channel_name=channel_name), outro_png, 35)
        finally:
            browser.close()

    return main_png, comment_pngs, outro_png


# --------------------------------------------------------------- background ---

def make_background(path: Path, custom: Path | None = None, dark: bool = False) -> Path:
    """Nền dọc 1080x1920: có lưới và gradient (hỗ trợ Light / Dark mode hoặc ảnh riêng)."""
    if custom and custom.exists():
        im = Image.open(custom).convert("RGB")
        s = max(W / im.width, H / im.height)
        im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
        l, t = (im.width - W) // 2, (im.height - H) // 2
        im.crop((l, t, l + W, t + H)).save(path)
        return path

    im = Image.new("RGB", (W, H), (0, 0, 0))
    px = im.load()
    start = int(H * 0.55)

    if dark:
        # Dark mode gradient: xám đen đến xanh xám huyền bí
        for y in range(H):
            t = y / H
            r = int(12 + 8 * t)
            g = int(14 + 12 * t)
            b = int(18 + 24 * t)
            for x in range(W):
                px[x, y] = (r, g, b)
        grid_color = (38, 44, 54)
    else:
        # Light/Default mode gradient: đen sang xanh dương
        for y in range(start, H):
            t = (y - start) / (H - start)
            b = int(20 + 130 * t)
            r = int(5 + 12 * t)
            for x in range(W):
                px[x, y] = (r, int(10 + 25 * t), b)
        grid_color = (235, 235, 235)

    d = ImageDraw.Draw(im)
    step = 112
    for x in range(0, W, step):
        d.line([(x, 0), (x, H)], fill=grid_color, width=2)
    for y in range(0, H, step):
        d.line([(0, y), (W, y)], fill=grid_color, width=2)
    im.save(path)
    return path


def _rounded(im: Image.Image, radius: int = 28) -> Image.Image:
    im = im.convert("RGBA")
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius, fill=255)
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.paste(im, (0, 0), mask)
    return out


def draw_watermark(
    image: Image.Image,
    text: str,
    pos: str = "above-card-left",
    card_top: int | None = None,
    card_left: int | None = None,
    card_width: int | None = None,
) -> None:
    """Vẽ tên bản quyền kênh (Watermark badge) với nền mờ bo góc bán trong suốt và chữ sắc nét.

    Args:
        image: PIL Image (RGBA hoặc RGB).
        text: Tên bản quyền kênh (ví dụ: "@GocThreads" hoặc "Kênh Giải Trí").
        pos: Vị trí hiển thị:
             - 'above-card-left' / 'top-left': Phía trên thẻ bài viết, góc trái (chuẩn TikTok như hình).
             - 'above-card-right': Phía trên thẻ bài viết, góc phải.
             - 'above-card-center': Phía trên thẻ bài viết, ở giữa.
             - 'top-right': Góc trên cùng bên phải màn hình.
             - 'screen-top-left': Góc trên cùng bên trái màn hình.
             - 'bottom-left': Góc dưới cùng bên trái màn hình.
             - 'bottom-right': Góc dưới cùng bên phải màn hình.
    """
    if not text or not text.strip():
        return
    text = text.strip()
    if not text.startswith("@") and " " not in text:
        text = f"@{text}"

    try:
        font = ImageFont.truetype("segoeuib.ttf", 30)
    except Exception:
        try:
            font = ImageFont.truetype("arialbd.ttf", 30)
        except Exception:
            font = ImageFont.load_default()

    dummy = Image.new("RGBA", (1, 1))
    draw_d = ImageDraw.Draw(dummy)
    bbox = draw_d.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    pad_x = 24
    pad_y = 12
    badge_w = tw + pad_x * 2
    badge_h = th + pad_y * 2

    margin_x = 50
    margin_y = 65

    c_top = card_top if card_top is not None else 450
    c_left = card_left if card_left is not None else margin_x
    c_width = card_width if card_width is not None else (W - margin_x * 2)

    p = pos.lower().replace("_", "-")
    if p in ("above-card-left", "card-left", "top-left", "card-top-left", "tl"):
        # Vị trí như ô màu đỏ: Ngay phía trên thẻ bài viết, lệch về góc trái
        x = margin_x
        y = max(40, c_top - badge_h - 22)
    elif p in ("above-card-right", "card-right", "card-top-right"):
        # Phía trên thẻ bài viết, lệch về góc phải
        x = W - badge_w - margin_x
        y = max(40, c_top - badge_h - 22)
    elif p in ("above-card-center", "card-center", "card-top-center", "top-center", "tc"):
        # Phía trên thẻ bài viết, căn giữa
        x = (W - badge_w) // 2
        y = max(40, c_top - badge_h - 22)
    elif p in ("top-right", "tr", "screen-top-right"):
        x = W - badge_w - margin_x
        y = margin_y
    elif p in ("screen-top-left", "corner-top-left"):
        x = margin_x
        y = margin_y
    elif p in ("bottom-left", "bl", "screen-bottom-left"):
        x = margin_x
        y = H - badge_h - 140
    elif p in ("bottom-right", "br", "screen-bottom-right"):
        x = W - badge_w - margin_x
        y = H - badge_h - 260
    else:  # Mặc định: Phía trên thẻ bài viết, góc trái
        x = margin_x
        y = max(40, c_top - badge_h - 22)

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)

    # Nền mờ bo góc hiện đại (đen mờ 70% với viền trắng mờ)
    d.rounded_rectangle(
        [x, y, x + badge_w, y + badge_h],
        radius=16,
        fill=(15, 18, 24, 185),
        outline=(255, 255, 255, 70),
        width=2,
    )

    tx = x + pad_x - bbox[0]
    ty = y + pad_y - bbox[1]

    # Đổ bóng chữ nhẹ
    d.text((tx + 1, ty + 1), text, font=font, fill=(0, 0, 0, 180))
    d.text((tx, ty), text, font=font, fill=(245, 247, 250, 245))

    if image.mode != "RGBA":
        image.paste(overlay, (0, 0), overlay)
    else:
        image.alpha_composite(overlay)


def compose_frame(bg: Path | None, post_png: Path, comment_png: Path | None, out: Path,
                  post_scale: float = 0.92, transparent_bg: bool = False,
                  watermark_text: str = "", watermark_pos: str = "above-card-left"):
    """Ghép nền + thẻ bài viết (phía trên) + thẻ bình luận (phía dưới) + bản quyền kênh.
    Tự động tính toán tỷ lệ co giãn động (Dynamic Layout) để tránh bị tràn màn hình hay đè nhau,
    đồng thời căn chỉnh vị trí cân đối ở giữa màn hình dọc 9:16.

    Args:
        bg:             File ảnh nền tĩnh (nếu transparent_bg=False).
        post_png:       File ảnh thẻ bài viết.
        comment_png:    File ảnh thẻ bình luận (hoặc None nếu cảnh mở đầu).
        out:            Đường dẫn file PNG xuất ra.
        post_scale:     Tỷ lệ co giãn cơ sở (mặc định 0.92).
        transparent_bg: Nếu True, tạo nền mờ bán trong suốt để video nền chuyển động nổi bật phía sau.
        watermark_text: Tên bản quyền kênh cần đóng dấu lên video.
        watermark_pos:  Vị trí bản quyền ('top-right', 'top-left', 'bottom-left', 'bottom-right', 'top-center').
    """
    if transparent_bg or bg is None:
        # Nền tối mờ 30% (alpha 75/255) giúp thẻ nổi bật rõ ràng trên video chuyển động
        base = Image.new("RGBA", (W, H), (0, 0, 0, 75))
    else:
        base = Image.open(bg).convert("RGBA")

    post_img = Image.open(post_png)
    comment_img = Image.open(comment_png) if comment_png else None

    gap = 40
    max_budget_h = H - 200  # Chừa ít nhất 100px ở mép trên và dưới màn hình

    if comment_img is None:
        # Cảnh mở đầu: chỉ có bài viết gốc → căn giữa màn hình
        current_scale = post_scale
        if post_img.height * current_scale > max_budget_h:
            current_scale = max(0.55, min(post_scale, max_budget_h / post_img.height))

        pw = int(post_img.width * current_scale)
        ph = int(post_img.height * current_scale)
        post = post_img.resize((pw, ph), Image.LANCZOS)
        post = _rounded(post, 26)

        top = max(100, (H - post.height) // 2)
        px = (W - post.width) // 2
        base.alpha_composite(post, (px, top))
    else:
        # Các cảnh tiếp theo: bài viết gốc phía trên, bình luận phía dưới
        total_needed_h = (post_img.height + comment_img.height) * post_scale + gap
        current_scale = post_scale
        if total_needed_h > max_budget_h:
            current_scale = max(0.50, min(post_scale, (max_budget_h - gap) / (post_img.height + comment_img.height)))

        pw = int(post_img.width * current_scale)
        ph = int(post_img.height * current_scale)
        post = post_img.resize((pw, ph), Image.LANCZOS)
        post = _rounded(post, 26)

        cw = int(comment_img.width * current_scale)
        ch = int(comment_img.height * current_scale)
        comment = comment_img.resize((cw, ch), Image.LANCZOS)
        comment = _rounded(comment, 28)

        total_h = post.height + gap + comment.height
        top = max(90, (H - total_h) // 2)
        cy = top + post.height + gap

        px = (W - post.width) // 2
        cx = (W - comment.width) // 2

        base.alpha_composite(post, (px, top))
        base.alpha_composite(comment, (cx, cy))

    if watermark_text:
        draw_watermark(base, watermark_text, watermark_pos, card_top=top, card_left=px, card_width=pw)

    if transparent_bg or bg is None:
        base.save(out, format="PNG")
    else:
        base.convert("RGB").save(out)
