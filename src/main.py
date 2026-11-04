#!/usr/bin/env python3
"""threads2video: link bài Threads -> video dọc 9:16 + tiêu đề TikTok.

Ví dụ:
    python main.py "https://www.threads.com/@its.hgie/post/XXXXXXXX"
    python main.py <link> --top 6 --dark --clean
    python main.py --from-json output/XXXX/data.json     # dựng lại, không cào lại
    python main.py --from-json sample/sample.json --mock-tts   # chạy thử, không tốn tiền
    python main.py <link> --tts-engine edge --edge-voice vi-VN-NamMinhNeural --dark
    python main.py <link> --video-bg assets/video/ --no-sfx
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

import cards
from sound_designer import SoundDesigner, SoundCue, format_cue_report
from sfx_engine.models import SoundEvent
import title as titlemod
import tts
import video
from scraper import Thread, fetch_thread, shortcode_from_url, is_spam_or_ad

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def main():
    ap = argparse.ArgumentParser(description="ThreadClip: Biến bài viết Threads thành video TikTok triệu view")
    ap.add_argument("url", nargs="?", help="Link bài Threads")
    ap.add_argument("--from-json", help="Dùng file data.json đã lưu thay vì cào lại")
    ap.add_argument("--top", type=int, default=5, help="Số bình luận nổi bật (mặc định 5)")
    ap.add_argument("--max-chars", type=int, default=300,
                    help="Bỏ bình luận dài hơn số ký tự này (mặc định 300)")
    ap.add_argument("--include-author-replies", action="store_true",
                    help="Giữ lại bình luận của tác giả (thích hợp cho các bài kể chuyện nhiều phần)")
    ap.add_argument("--out", default=str(ROOT / "output"), help="Thư mục xuất")
    ap.add_argument("--bg", help="Ảnh nền riêng (mặc định: lưới xanh đen hoặc xám đen)")
    ap.add_argument("--dark", action="store_true", help="Bật giao diện tối (Dark Mode) cho video")
    ap.add_argument("--clean", action="store_true",
                    help="Xóa thư mục làm việc tạm thời (work/) sau khi xuất video")

    # ── Nhạc nền ──────────────────────────────────────────────────────────────
    ap.add_argument("--music-dir", default=str(ROOT / "assets" / "music"))
    ap.add_argument("--music-file", help="File nhạc nền cụ thể để dùng (thay vì chọn ngẫu nhiên)")
    ap.add_argument("--music-volume", type=float, default=0.12)
    ap.add_argument("--with-music", action="store_true",
                    help="Bật thêm nhạc nền Lofi / TikTok (mặc định: tắt nhạc nền theo yêu cầu)")

    # ── TTS (giọng đọc) ───────────────────────────────────────────────────────
    ap.add_argument("--edge-voice",
                    help="Tên giọng edge-tts (vd: vi-VN-NamMinhNeural, vi-VN-HoaiMyNeural). "
                         "Mặc định: đọc từ EDGE_TTS_VOICE trong .env")
    ap.add_argument("--rate", "--tts-rate", default="+0%",
                    help="Tốc độ giọng đọc AI (vd: 1.0x, 1.1x, 1.15x, 1.2x hoặc +15%%, -10%%, mặc định: 1.0x)")
    ap.add_argument("--tts-engine", choices=["edge", "gtts"], default="edge",
                    help="Công nghệ giọng đọc (edge: Microsoft Edge Neural tự nhiên, gtts: Google TTS siêu tốc chống nghẽn)")
    ap.add_argument("--mock-tts", action="store_true", help="Giọng giả để test, không gọi TTS")

    # ── Video nền ─────────────────────────────────────────────────────────────
    ap.add_argument("--video-bg",
                    help="File hoặc thư mục chứa video nền (mp4/webm). "
                         "Nếu là thư mục: chọn ngẫu nhiên. Nếu không có: dùng ảnh tĩnh.")
    ap.add_argument("--video-bg-style",
                    choices=["lofi", "dark", "gaming", "cooking", "nature"],
                    default="lofi",
                    help="Phong cách video nền tổng hợp nếu không có file sẵn (mặc định: lofi)")
    ap.add_argument("--no-video-bg", action="store_true",
                    help="Không dùng video nền (giữ ảnh tĩnh như cũ)")

    # ── Meme SFX ──────────────────────────────────────────────────────────────
    ap.add_argument("--sfx-dir", default=str(ROOT / "assets" / "sfx"),
                    help="Thư mục chứa file âm thanh meme .mp3")
    ap.add_argument("--sfx-volume", type=float, default=0.35,
                    help="Âm lượng hiệu ứng âm thanh SFX (0.05 - 1.0, mặc định 0.35)")
    ap.add_argument("--no-sfx", action="store_true", help="Tắt âm thanh meme")

    # ── Bản quyền kênh & Outro (Call to Action) ───────────────────────────────
    ap.add_argument("--watermark", default="",
                    help="Tên bản quyền kênh (vd: @GocThreads hoặc tên kênh)")
    ap.add_argument("--watermark-pos",
                    choices=[
                        "above-card-left", "above-card-right", "above-card-center",
                        "top-right", "top-left", "bottom-left", "bottom-right", "top-center"
                    ],
                    default="above-card-left",
                    help="Vị trí hiển thị bản quyền (mặc định: above-card-left, ngay phía trên thẻ bài viết)")
    ap.add_argument("--mask-user", "--hide-user", action="store_true",
                    help="Ẩn danh: Che tên và ảnh đại diện người dùng trong video")
    ap.add_argument("--no-outro", action="store_true",
                    help="Tắt lời kêu gọi Follow, Thả Tim và Bình luận ở cuối video")

    # ── Playwright / scraper ──────────────────────────────────────────────────
    ap.add_argument("--storage-state", help="File đăng nhập Playwright (xem README)")
    ap.add_argument("--show-browser", action="store_true", help="Hiện cửa sổ trình duyệt khi cào")

    args = ap.parse_args()
    load_dotenv(ROOT / ".env")

    if args.edge_voice:
        os.environ["EDGE_TTS_VOICE"] = args.edge_voice

    # 1. Kiểm tra môi trường & điều kiện tiên quyết (Fail-Fast)
    try:
        video.check_dependencies()
    except RuntimeError as e:
        print(f"\n[Lỗi môi trường] {e}")
        return 1

    start_time = time.time()

    # 2. Thu thập dữ liệu bài viết
    if args.from_json:
        thread = Thread.from_json(Path(args.from_json).read_text(encoding="utf-8"))
        name = Path(args.from_json).parent.name
    elif args.url:
        print("[1/5] Đang mở bài Threads và đọc bình luận…")
        thread = fetch_thread(
            args.url,
            top=args.top,
            max_chars=args.max_chars,
            storage_state=args.storage_state,
            headless=not args.show_browser,
            include_author_replies=args.include_author_replies,
        )
        name = shortcode_from_url(args.url)
    else:
        ap.error("Cần link Threads hoặc --from-json")

    # Tự động loại bỏ bình luận spam, quảng cáo, gắn link ngoài
    raw_count = len(thread.comments)
    thread.comments = [c for c in thread.comments if not is_spam_or_ad(c.text)]
    removed_count = raw_count - len(thread.comments)
    if removed_count > 0:
        print(f"      (Đã lọc bỏ {removed_count} bình luận spam / quảng cáo / gắn link ngoài)")

    thread.comments = thread.comments[: args.top]
    out = Path(args.out) / name
    shots = out / "screenshots"
    work = out / "work"
    for d in (shots, work):
        d.mkdir(parents=True, exist_ok=True)
    (out / "data.json").write_text(thread.to_json(), encoding="utf-8")
    print(f"      Bài của @{thread.main.username}, {len(thread.comments)} bình luận được chọn")

    # 3. Tạo ảnh chụp màn hình các thẻ
    print(f"[2/5] Đang tạo ảnh chụp màn hình ({'Dark' if args.dark else 'Light'} Mode)…")
    post_png, comment_pngs, outro_png = cards.render_cards(
        thread.main,
        thread.comments,
        shots,
        dark=args.dark,
        render_outro=not args.no_outro,
        channel_name=args.watermark,
        mask_user=args.mask_user,
    )
    bg = cards.make_background(work / "bg.png", Path(args.bg) if args.bg else None, dark=args.dark)

    # ── Quyết định video nền ──────────────────────────────────────────────────
    bg_video: Path | None = None
    if not args.no_video_bg:
        if args.video_bg:
            p = Path(args.video_bg)
            if p.is_dir():
                bg_video = video.pick_video_bg(p)
            elif p.is_file():
                bg_video = p
        else:
            # Tự chọn ngẫu nhiên từ assets/video/
            bg_video = video.pick_video_bg(ROOT / "assets" / "video")

        if bg_video is None:
            # Không có file sẵn → tạo video nền tổng hợp
            synth_bg = work / "synth_bg.mp4"
            if not synth_bg.exists():
                print(f"      (Tạo video nền tổng hợp style={args.video_bg_style}…)")
                video.make_video_bg(synth_bg, style=args.video_bg_style, dur=30.0)
            bg_video = synth_bg

    # ── Quyết định SFX dir ────────────────────────────────────────────────────
    sfx_dir = Path(args.sfx_dir) if not args.no_sfx else None

    # 4. Tạo giọng đọc & render từng cảnh
    edge_voice = os.getenv("EDGE_TTS_VOICE")
    tts_label = f"Edge TTS ({edge_voice or 'Tự động Nam/Nữ'})"
    print(f"[3/5] Đang tạo giọng đọc [{tts_label}] và ghép cảnh…")

    # Tính điểm bắt đầu ngẫu nhiên trong video nền để chạy liên tục qua các cảnh
    import random
    bg_cursor = 0.0
    if bg_video and bg_video.exists():
        try:
            total_bg_len = video.duration(bg_video)
            if total_bg_len > 120:
                bg_cursor = random.uniform(0.0, max(0.0, total_bg_len - 240))
        except Exception:
            bg_cursor = 0.0

    segments = [(thread.main.text, None, thread.main.username, thread.main.gender)] + [
        (comment.text, comment_pngs[i], comment.username, comment.gender)
        for i, comment in enumerate(thread.comments)
    ]
    designer = SoundDesigner(sfx_dir) if sfx_dir else None
    all_sound_events: list[SoundEvent] = []
    scenes: list[Path] = []

    for i, (text, cpng, username, explicit_gender) in enumerate(segments):
        if i > 0 and not args.mock_tts:
            time.sleep(0.4)  # Giãn cách nhẹ chống nghẽn kết nối máy chủ giọng đọc

        voice_path = work / f"voice_{i}.mp3"
        voice_path, boundaries, voice_info = tts.synthesize(
            text,
            voice_path,
            mock=args.mock_tts,
            engine=args.tts_engine,
            edge_voice=args.edge_voice,
            gender=explicit_gender,
            username=username or "",
            scene_index=i,
            rate=args.rate,
        )
        voice_dur = video.duration(voice_path)

        user_scale = args.sfx_volume / 0.35
        scene_events: list[SoundEvent] = []
        if designer and not args.no_sfx:
            scene_events = designer.plan_sound_events(
                scene_id=i,
                text=text,
                is_hook=(i == 0),
                sentence_boundaries=boundaries,
                total_duration=voice_dur,
                user_scale=user_scale,
            )
            all_sound_events.extend(scene_events)

        frame = work / f"frame_{i}.png"
        cards.compose_frame(
            bg,
            post_png,
            cpng,
            frame,
            transparent_bg=bool(bg_video),
            watermark_text=args.watermark,
            watermark_pos=args.watermark_pos,
        )
        scene = work / f"scene_{i}.mp4"

        if bg_video:
            video.make_scene_with_video_bg(
                frame, voice_path, bg_video, scene,
                bg_offset=bg_cursor,
                sound_events=scene_events,
            )
            try:
                scene_dur = video.duration(scene)
                bg_cursor += scene_dur
            except Exception:
                pass
        else:
            video.make_scene(
                frame, voice_path, scene,
                sound_events=scene_events,
            )

        if scene_events:
            sfx_names = ", ".join(e.sfx_path.stem for e in scene_events if e.sfx_path)
            print(f"      Cảnh {i + 1}/{len(segments)} hoàn thành | 🎙️ {voice_info} | 🎵 Multi-SFX ({len(scene_events)}): [{sfx_names}]")
        else:
            print(f"      Cảnh {i + 1}/{len(segments)} hoàn thành | 🎙️ {voice_info}")
        scenes.append(scene)

    # ── Cảnh kết thúc (Outro): Kêu gọi Follow, Tim & Cmt ───────────────────
    if not args.no_outro and outro_png:
        print("      Đang tạo cảnh kết thúc (Outro: Follow, Tim & Cmt)…")
        outro_text = (
            "Cảm ơn các bạn đã theo dõi! Hãy thả tim, bình luận và follow kênh để xem thêm nhiều video mới nhé!"
        )
        voice_outro = work / "voice_outro.mp3"
        voice_outro, _, outro_voice_info = tts.synthesize(
            outro_text,
            voice_outro,
            mock=args.mock_tts,
            engine=args.tts_engine,
            edge_voice=args.edge_voice,
            gender=thread.main.gender,
            username=thread.main.username or "",
            scene_index=len(segments),
            rate=args.rate,
        )

        frame_outro = work / "frame_outro.png"
        cards.compose_frame(
            bg,
            outro_png,
            None,
            frame_outro,
            transparent_bg=bool(bg_video),
            watermark_text=args.watermark,
            watermark_pos=args.watermark_pos,
        )
        scene_outro = work / "scene_outro.mp4"

        # Chọn SFX tươi vui cho outro
        outro_sfx = None
        if sfx_dir:
            for sfx_name in ["pop.mp3", "ting.mp3", "bell.mp3", "whoosh.mp3"]:
                p = sfx_dir / sfx_name
                if p.exists():
                    outro_sfx = p
                    break

        user_scale = args.sfx_volume / 0.35
        outro_sfx_vol = round(max(0.05, min(1.0, 0.40 * user_scale)), 2)

        outro_events: list[SoundEvent] = []
        if outro_sfx and not args.no_sfx:
            outro_events.append(
                SoundEvent(
                    event_id=f"evt_outro_1",
                    scene_id=len(segments),
                    anchor_text="Outro Call-to-Action",
                    char_start=0,
                    char_end=len(outro_text),
                    event_type="Hook",
                    emotion="Excitement",
                    sfx_file=outro_sfx,
                    score=90.0,
                    priority=1,
                    start_time=0.2,
                    end_time=1.0,
                    volume=outro_sfx_vol,
                    reason="Âm thanh tươi vui mở màn phần kêu gọi tương tác",
                )
            )
            all_sound_events.extend(outro_events)

        if bg_video:
            video.make_scene_with_video_bg(
                frame_outro,
                voice_outro,
                bg_video,
                scene_outro,
                bg_offset=bg_cursor,
                sound_events=outro_events,
            )
            try:
                bg_cursor += video.duration(scene_outro)
            except Exception:
                pass
        else:
            video.make_scene(
                frame_outro,
                voice_outro,
                scene_outro,
                sound_events=outro_events,
            )

        scenes.append(scene_outro)
        print(f"      Cảnh kết thúc (Outro) hoàn thành | 🎙️ {outro_voice_info} | ❤️ Call To Action")

    # 5. Ghép nối video
    print("[4/5] Đang ghép video tổng hợp…")
    final = out / f"ThreadClip_{name}.mp4"
    if args.with_music:
        joined = work / "joined.mp4"
        video.concat(scenes, joined)
        music: Path | None = None
        if args.music_file and Path(args.music_file).exists():
            music = Path(args.music_file)
        else:
            music = video.pick_music(Path(args.music_dir))
        if music:
            print(f"      Thêm nhạc nền: {music.name}")
            video.add_music(joined, music, final, volume=args.music_volume)
        else:
            joined.replace(final)
    else:
        print("      (Xuất video không nhạc nền theo yêu cầu)")
        video.concat(scenes, final)

    # 6. Tạo tiêu đề TikTok & Báo cáo Sound Design
    print("[5/5] Đang tạo tiêu đề TikTok & Báo cáo Sound Design…")
    title_text = titlemod.make_title(thread)
    (out / "title.txt").write_text(title_text, encoding="utf-8")

    if all_sound_events:
        import json
        (out / "sfx_report.md").write_text(format_cue_report(all_sound_events), encoding="utf-8")
        (out / "sfx_cues.json").write_text(
            json.dumps([c.to_dict() for c in all_sound_events], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # Dọn dẹp file tạm nếu được yêu cầu
    if args.clean:
        print("      Đang dọn dẹp các tệp tạm thời trong work/…")
        shutil.rmtree(work, ignore_errors=True)

    elapsed = time.time() - start_time
    print(f"\nHoàn tất sau {elapsed:.1f}s!")
    print(f"Đường dẫn video: {final} ({video.duration(final):.1f}s)")
    print(f"Tiêu đề TikTok:\n{title_text}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
