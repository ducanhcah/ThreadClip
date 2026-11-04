"""Ghép video dọc 9:16 bằng ffmpeg: mỗi cảnh một file, nối bằng concat, rồi thêm nhạc."""
from __future__ import annotations

import os
import random
import shutil
import subprocess
from sfx_engine.audio_mixer import AudioMixer
from sfx_engine.models import SoundEvent
from pathlib import Path

FPS = 30
PAD = 0.5       # giây lặng sau mỗi đoạn đọc
W, H = 1080, 1920  # kích thước video dọc 9:16


def _find_and_add_ffmpeg_to_path():
    """Tự động phát hiện ffmpeg/ffprobe từ WinGet packages hoặc Windows Registry
    khi terminal chưa kịp tải lại (refresh) biến môi trường PATH mới.
    """
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        return

    candidate_paths: list[str] = [
        str(Path(__file__).resolve().parent.parent / "runtime" / "ffmpeg"),
    ]

    # 1. Quét từ WinGet Packages (nơi winget install Gyan.FFmpeg cài đặt)
    local_app_data = os.getenv("LOCALAPPDATA")
    if local_app_data:
        winget_pkg_dir = Path(local_app_data) / "Microsoft" / "WinGet" / "Packages"
        if winget_pkg_dir.exists():
            for bin_dir in winget_pkg_dir.glob("**/bin"):
                candidate_paths.append(str(bin_dir))

    # 2. Quét từ Windows Registry (User & Machine Environment)
    if os.name == "nt":
        try:
            import winreg
            for hkey, subkey in [
                (winreg.HKEY_CURRENT_USER, r"Environment"),
                (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
            ]:
                try:
                    with winreg.OpenKey(hkey, subkey) as key:
                        val, _ = winreg.QueryValueEx(key, "Path")
                        candidate_paths.extend(val.split(";"))
                except Exception:
                    pass
        except Exception:
            pass

    # 3. Một số đường dẫn thông dụng khác
    candidate_paths.extend([
        r"C:\ffmpeg\bin",
        r"C:\Program Files\ffmpeg\bin",
        r"C:\ProgramData\chocolatey\bin",
    ])

    current_path = os.environ.get("PATH", "")
    for p in candidate_paths:
        p_str = p.strip()
        if not p_str:
            continue
        p_path = Path(p_str)
        if p_path.exists():
            has_ffmpeg = (p_path / "ffmpeg.exe").exists() or (p_path / "ffmpeg").exists()
            has_ffprobe = (p_path / "ffprobe.exe").exists() or (p_path / "ffprobe").exists()
            if has_ffmpeg or has_ffprobe:
                os.environ["PATH"] = p_str + os.pathsep + current_path
                current_path = os.environ["PATH"]
                if shutil.which("ffmpeg") and shutil.which("ffprobe"):
                    return


# Tự động nạp ffmpeg vào PATH ngay khi import module
_find_and_add_ffmpeg_to_path()


def get_ffmpeg_bin() -> str:
    _find_and_add_ffmpeg_to_path()
    return shutil.which("ffmpeg") or "ffmpeg"


def get_ffprobe_bin() -> str:
    _find_and_add_ffmpeg_to_path()
    return shutil.which("ffprobe") or "ffprobe"


def check_dependencies():
    """Kiểm tra sự tồn tại của ffmpeg và ffprobe trong PATH hệ thống."""
    _find_and_add_ffmpeg_to_path()
    missing = []
    if not shutil.which("ffmpeg"):
        missing.append("ffmpeg")
    if not shutil.which("ffprobe"):
        missing.append("ffprobe")
    if missing:
        raise RuntimeError(
            f"Không tìm thấy {' và '.join(missing)} trong PATH hệ thống.\n"
            "Nếu bạn vừa cài đặt qua winget, hãy khởi động lại PowerShell/VS Code để nhận PATH mới,\n"
            "hoặc kiểm tra lại lệnh: `winget install Gyan.FFmpeg`\n"
            "Tải thủ công tại: https://ffmpeg.org/download.html"
        )


def _run(cmd: list[str]):
    # Đảm bảo lệnh đầu tiên được trỏ đúng binary tuyệt đối nếu có
    if cmd and cmd[0] == "ffmpeg":
        cmd[0] = get_ffmpeg_bin()
    elif cmd and cmd[0] == "ffprobe":
        cmd[0] = get_ffprobe_bin()
    subprocess.run(cmd, check=True)


def duration(path: Path) -> float:
    out = subprocess.run(
        [get_ffprobe_bin(), "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return float(out)


def make_scene(frame_png: Path, voice: Path, out: Path, sfx: Path | None = None,
               sfx_offset: float = 0.0, sfx_volume: float = 0.40,
               sound_events: list[SoundEvent] | None = None):
    """Một cảnh = ảnh tĩnh + giọng đọc (+ nhiều sound_events hoặc sfx đơn lẻ kế thừa).

    Hỗ trợ cả danh sách SoundEvent đa điểm (Multi-SFX) lẫn tham số sfx đơn lẻ truyền thống.
    """
    tmp = out.with_name(out.stem + ".tmp.mp4")

    # Ưu tiên sử dụng Multi-SFX AudioMixer nếu có sound_events
    if sound_events is not None:
        mixer = AudioMixer(default_pad=PAD)
        mixed_audio = out.with_name(out.stem + ".mixed.m4a")
        try:
            mixed_audio, dur = mixer.mix_voice_and_sfx(voice, sound_events, mixed_audio, pad=PAD)
            _run([
                "ffmpeg", "-y", "-loglevel", "error",
                "-framerate", str(FPS), "-i", str(frame_png),
                "-i", str(mixed_audio),
                "-filter_complex", f"[0:v]format=yuv420p,loop=-1:1,trim=duration={dur:.3f}[v]",
                "-map", "[v]", "-map", "1:a",
                "-t", f"{dur:.3f}",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-r", str(FPS),
                "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
                "-movflags", "+faststart", str(tmp),
            ])
            tmp.replace(out)
            return
        finally:
            if mixed_audio.exists():
                mixed_audio.unlink(missing_ok=True)

    # Nhánh backward-compatible cho sfx đơn lẻ
    voice_dur = duration(voice)
    sfx_dur = duration(sfx) if (sfx and sfx.exists()) else 0.0
    dur = max(voice_dur + PAD, sfx_offset + sfx_dur) if sfx_dur > 0 else (voice_dur + PAD)

    if sfx and sfx.exists():
        delay_ms = int(max(0.0, sfx_offset) * 1000)
        audio_fc = (
            f"[1:a]volume={sfx_volume:.2f},adelay={delay_ms}|{delay_ms},"
            f"atrim=0:{dur:.3f},afade=t=out:st={max(0.0, dur - 0.25):.2f}:d=0.25[s];"
            f"[2:a]volume=1.0,apad=pad_dur={PAD}[vraw];"
            f"[s][vraw]amix=inputs=2:duration=longest:dropout_transition=0:normalize=0[a]"
        )
        _run([
            "ffmpeg", "-y", "-loglevel", "error",
            "-framerate", str(FPS), "-i", str(frame_png),
            "-i", str(sfx),
            "-i", str(voice),
            "-filter_complex",
            f"[0:v]format=yuv420p,loop=-1:1,trim=duration={dur:.3f}[v];" + audio_fc,
            "-map", "[v]", "-map", "[a]",
            "-t", f"{dur:.3f}",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-r", str(FPS),
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
            "-movflags", "+faststart", str(tmp),
        ])
    else:
        _run([
            "ffmpeg", "-y", "-loglevel", "error",
            "-framerate", str(FPS), "-i", str(frame_png), "-i", str(voice),
            "-vf", f"format=yuv420p,loop=-1:1,trim=duration={dur:.3f}",
            "-af", f"apad=pad_dur={PAD}",
            "-t", f"{dur:.3f}",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-r", str(FPS),
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
            "-movflags", "+faststart", str(tmp),
        ])
    tmp.replace(out)


def concat(scenes: list[Path], out: Path):
    if not scenes:
        raise ValueError("Danh sách cảnh (scenes) rỗng, không thể ghép video.")
    lst = out.with_suffix(".txt")
    content = "".join(f"file '{p.resolve().as_posix()}'\n" for p in scenes)
    lst.write_text(content, encoding="utf-8")
    tmp = out.with_name(out.stem + ".tmp.mp4")
    try:
        _run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
              "-i", str(lst.resolve()), "-c", "copy", str(tmp.resolve())])
        tmp.replace(out)
    except Exception as e:
        print(f"[Concat Error] File list:\n{content}")
        raise
    finally:
        if lst.exists():
            lst.unlink(missing_ok=True)


def pick_music(music_dir: Path) -> Path | None:
    if not music_dir.exists():
        return None
    files = [p for p in music_dir.glob("*") if p.suffix.lower() in {".mp3", ".wav", ".m4a", ".ogg"}]
    return random.choice(files) if files else None


def add_music(video: Path, music: Path, out: Path, volume: float = 0.12):
    """Trộn nhạc nền nhỏ dưới giọng đọc, giữ nguyên hình (-c:v copy)."""
    total = duration(video)
    tmp = out.with_name(out.stem + ".tmp.mp4")
    # Tính toán an toàn cho thời lượng fade out
    fade_d = min(2.0, max(0.5, total * 0.2))
    fade_st = max(0.0, total - fade_d)
    fc = (
        f"[1:a]volume={volume},afade=t=in:d=1,afade=t=out:st={fade_st:.2f}:d={fade_d:.2f}[m];"
        f"[0:a][m]amix=inputs=2:duration=first:dropout_transition=2,volume=1.0[a]"
    )
    _run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(video), "-stream_loop", "-1", "-i", str(music),
        "-filter_complex", fc, "-map", "0:v", "-map", "[a]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", f"{total:.3f}",
        "-movflags", "+faststart", str(tmp),
    ])
    tmp.replace(out)


def pick_video_bg(video_dir: Path) -> Path | None:
    """Chọn ngẫu nhiên một file video từ thư mục assets/video/ làm nền chuyển động.

    Trả về None nếu thư mục không tồn tại hoặc không có file video.
    """
    if not video_dir.exists():
        return None
    files = [p for p in video_dir.rglob("*")
             if p.suffix.lower() in {".mp4", ".webm", ".mov", ".mkv", ".avi"}]
    return random.choice(files) if files else None


def make_video_bg(out: Path, style: str = "lofi", dur: float = 15.0):
    """Tạo video nền chuyển động mượt mà bằng Pillow + FFmpeg (chỉ mất ~2s).

    Args:
        out:   Đường dẫn file .mp4 xuất ra.
        style: "lofi" (tím chill), "dark" (xám đen), "gaming" (xanh neon),
               "cooking" (cam ấm), "nature" (xanh lá).
        dur:   Thời lượng video mẫu (giây).
    """
    from PIL import Image  # noqa: PLC0415

    STYLES = {
        # (r1, g1, b1), (r2, g2, b2)
        "lofi":    ((20, 12, 38),  (48, 22, 75)),
        "dark":    ((10, 12, 16),  (22, 28, 38)),
        "gaming":  ((6, 12, 35),   (0, 78, 146)),
        "cooking": ((45, 18, 5),   (110, 45, 10)),
        "nature":  ((8, 30, 15),   (20, 75, 40)),
    }
    top_rgb, bot_rgb = STYLES.get(style, STYLES["lofi"])

    tmp_img = out.with_suffix(".png")
    im = Image.new("RGB", (W, H))
    px = im.load()
    for y in range(H):
        t = y / H
        r = int(top_rgb[0] + (bot_rgb[0] - top_rgb[0]) * t)
        g = int(top_rgb[1] + (bot_rgb[1] - top_rgb[1]) * t)
        b = int(top_rgb[2] + (bot_rgb[2] - top_rgb[2]) * t)
        for x in range(W):
            px[x, y] = (r, g, b)
    im.save(tmp_img)

    tmp = out.with_name(out.stem + ".tmp.mp4")
    try:
        frames = int(dur * FPS)
        vf = (
            f"zoompan=z='min(zoom+0.0004,1.12)':"
            f"x='iw/2-(iw/zoom/2)+sin(in/45)*30':"
            f"y='ih/2-(ih/zoom/2)+cos(in/45)*30':"
            f"d={frames}:s={W}x{H}:fps={FPS},"
            f"format=yuv420p"
        )
        _run([
            "ffmpeg", "-y", "-loglevel", "error",
            "-loop", "1", "-i", str(tmp_img),
            "-vf", vf,
            "-t", f"{dur:.1f}",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "22",
            "-an",
            str(tmp),
        ])
        tmp.replace(out)
    finally:
        tmp_img.unlink(missing_ok=True)


def make_scene_with_video_bg(frame_png: Path, voice: Path, bg_video: Path,
                              out: Path, sfx: Path | None = None,
                              bg_offset: float = 0.0,
                              sfx_offset: float = 0.0,
                              sfx_volume: float = 0.40,
                              sound_events: list[SoundEvent] | None = None):
    """Cảnh có video nền chuyển động thay vì ảnh tĩnh.

    Tự động scale/crop bg_video về 1080×1920, loop để đủ độ dài, overlay frame.
    Hỗ trợ bg_offset để video nền chạy liên tục không bị giật lặp lại từ đầu qua các cảnh.
    Loại bỏ fade in để không bị nháy đen khi chuyển sang bình luận mới.
    Hỗ trợ sfx_offset để kích hoạt SFX chính xác theo nhịp câu/từ khóa.

    Args:
        frame_png: Ảnh PNG khung hình cảnh (1080×1920).
        voice:     File mp3 giọng đọc chính.
        bg_video:  Video nền (bất kỳ kích thước, sẽ được tự động crop).
        out:       Đường dẫn file .mp4 xuất ra.
        sfx:       File mp3 âm thanh meme (None = không có).
        bg_offset: Điểm bắt đầu (giây) trong video nền để chạy liên tục.
        sfx_offset: Mốc giây kích hoạt SFX.
        sfx_volume: Âm lượng SFX (0.0 - 1.0, mặc định 0.40).
    """
    tmp = out.with_name(out.stem + ".tmp.mp4")
    ss_args = ["-ss", f"{bg_offset:.2f}"] if bg_offset > 0 else []

    if sound_events is not None:
        mixer = AudioMixer(default_pad=PAD)
        mixed_audio = out.with_name(out.stem + ".mixed.m4a")
        try:
            mixed_audio, dur = mixer.mix_voice_and_sfx(voice, sound_events, mixed_audio, pad=PAD)
            vf = (
                f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
                f"crop={W}:{H},setsar=1[bg];"
                f"[1:v]scale={W}:{H}[frame];"
                f"[bg][frame]overlay=0:0,format=yuv420p,"
                f"trim=duration={dur:.3f}[v]"
            )
            _run([
                "ffmpeg", "-y", "-loglevel", "error",
                *ss_args,
                "-stream_loop", "-1", "-i", str(bg_video),
                "-i", str(frame_png),
                "-i", str(mixed_audio),
                "-filter_complex", vf,
                "-map", "[v]", "-map", "2:a",
                "-t", f"{dur:.3f}",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-r", str(FPS),
                "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
                "-movflags", "+faststart", str(tmp),
            ])
            tmp.replace(out)
            return
        finally:
            if mixed_audio.exists():
                mixed_audio.unlink(missing_ok=True)

    voice_dur = duration(voice)
    sfx_dur = duration(sfx) if (sfx and sfx.exists()) else 0.0
    dur = max(voice_dur + PAD, sfx_offset + sfx_dur) if sfx_dur > 0 else (voice_dur + PAD)

    # Video filter: scale bg → crop center → overlay frame PNG lên trên (không fade=in để tránh nháy đen)
    vf = (
        f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H},setsar=1[bg];"
        f"[2:v]scale={W}:{H}[frame];"
        f"[bg][frame]overlay=0:0,format=yuv420p,"
        f"trim=duration={dur:.3f}[v]"
    )

    ss_args = ["-ss", f"{bg_offset:.2f}"] if bg_offset > 0 else []

    if sfx and sfx.exists():
        delay_ms = int(max(0.0, sfx_offset) * 1000)
        audio_fc = (
            f"[1:a]volume={sfx_volume:.2f},adelay={delay_ms}|{delay_ms},"
            f"atrim=0:{dur:.3f},afade=t=out:st={max(0.0, dur - 0.25):.2f}:d=0.25[s];"
            f"[3:a]volume=1.0,apad=pad_dur={PAD}[vraw];"
            f"[s][vraw]amix=inputs=2:duration=longest:dropout_transition=0:normalize=0[a]"
        )
        _run([
            "ffmpeg", "-y", "-loglevel", "error",
            *ss_args,
            "-stream_loop", "-1", "-i", str(bg_video),  # 0: video nền
            "-i", str(sfx),                              # 1: sfx
            "-i", str(frame_png),                        # 2: frame PNG
            "-i", str(voice),                            # 3: giọng đọc
            "-filter_complex", vf + ";" + audio_fc,
            "-map", "[v]", "-map", "[a]",
            "-t", f"{dur:.3f}",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-r", str(FPS),
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
            "-movflags", "+faststart", str(tmp),
        ])
    else:
        audio_fc = f"[1:a]apad=pad_dur={PAD}[a]"
        _run([
            "ffmpeg", "-y", "-loglevel", "error",
            *ss_args,
            "-stream_loop", "-1", "-i", str(bg_video),  # 0: video nền
            "-i", str(voice),                            # 1: giọng đọc
            "-i", str(frame_png),                        # 2: frame PNG
            "-filter_complex", (
                f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
                f"crop={W}:{H},setsar=1[bg];"
                f"[2:v]scale={W}:{H}[frame];"
                f"[bg][frame]overlay=0:0,format=yuv420p,"
                f"trim=duration={dur:.3f}[v];"
                f"[1:a]apad=pad_dur={PAD}[a]"
            ),
            "-map", "[v]", "-map", "[a]",
            "-t", f"{dur:.3f}",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-r", str(FPS),
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
            "-movflags", "+faststart", str(tmp),
        ])
    tmp.replace(out)
