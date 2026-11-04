"""Multi-track Audio Mixer cho Rule-Based Multi-SFX Engine.

Trộn một giọng đọc chính (Voice) với danh sách nhiều hiệu ứng âm thanh (SoundEvent)
được kích hoạt tại các timestamp khác nhau thông qua FFmpeg.
Kiểm soát âm lượng, clipping và đảm bảo giọng đọc luôn rõ ràng.
"""
from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import SoundEvent

logger = logging.getLogger("sfx_engine.audio_mixer")

# Cache thời lượng file âm thanh để tránh gọi ffprobe liên tục
_DURATION_CACHE: dict[str, float] = {}


def _get_ffprobe_bin() -> str:
    import shutil
    return shutil.which("ffprobe") or "ffprobe"


def _get_ffmpeg_bin() -> str:
    import shutil
    return shutil.which("ffmpeg") or "ffmpeg"


def get_audio_duration(path: Path | str) -> float:
    """Đo thời lượng file âm thanh bằng ffprobe (có cache)."""
    p_str = str(Path(path).resolve())
    if p_str in _DURATION_CACHE:
        return _DURATION_CACHE[p_str]

    try:
        res = subprocess.run(
            [
                _get_ffprobe_bin(),
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=nw=1:nk=1",
                p_str,
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        dur = float(res.stdout.strip())
        _DURATION_CACHE[p_str] = dur
        return dur
    except Exception as e:
        logger.warning(f"Không thể đo thời lượng của {path}: {e}")
        return 0.0


class AudioMixer:
    """Bộ trộn âm thanh đa track kết hợp Voice và nhiều SFX."""

    def __init__(self, default_pad: float = 0.40):
        self.default_pad = default_pad

    def mix_voice_and_sfx(
        self,
        voice_path: Path,
        sound_events: list[SoundEvent],
        out_path: Path,
        pad: float | None = None,
    ) -> tuple[Path, float]:
        """Trộn giọng đọc chính với danh sách các SoundEvent.

        Args:
            voice_path: File âm thanh giọng đọc chính (.mp3 / .wav / .m4a).
            sound_events: Danh sách SoundEvent cần chèn.
            out_path: Đường dẫn file âm thanh xuất ra.
            pad: Khoảng đệm tĩnh ở cuối câu thoại (mặc định 0.40s).

        Returns:
            tuple[Path, float]: (đường dẫn file âm thanh đã mix, tổng thời lượng giây).
        """
        if pad is None:
            pad = self.default_pad

        if not voice_path.exists():
            raise FileNotFoundError(f"File giọng đọc không tồn tại: {voice_path}")

        voice_dur = get_audio_duration(voice_path)
        if voice_dur <= 0:
            voice_dur = 1.0

        # Lọc các SoundEvent hợp lệ (file tồn tại, start_time >= 0, volume > 0)
        valid_events: list[SoundEvent] = []
        for e in sound_events:
            p = e.sfx_path
            if p is None or not p.exists():
                logger.debug(f"Bỏ qua SFX không tồn tại: {e.sfx_file}")
                continue
            if e.start_time is None or e.start_time < 0.0:
                logger.debug(f"Bỏ qua SFX có start_time không hợp lệ: {e.start_time}")
                continue
            if e.volume <= 0.0:
                continue
            valid_events.append(e)

        # Tính toán tổng thời lượng cảnh
        total_dur = voice_dur + pad
        for e in valid_events:
            sfx_dur = get_audio_duration(e.sfx_path)
            e_end = (e.start_time or 0.0) + sfx_dur
            if e_end > total_dur:
                total_dur = e_end

        out_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_out = out_path.with_name(out_path.stem + ".tmp" + out_path.suffix)

        # Nếu không có SFX nào hợp lệ, chỉ cần pad nhẹ giọng đọc
        if not valid_events:
            cmd = [
                _get_ffmpeg_bin(), "-y", "-loglevel", "error",
                "-i", str(voice_path),
                "-filter_complex", f"[0:a]apad=pad_dur={pad:.3f}[aout]",
                "-map", "[aout]",
                "-t", f"{total_dur:.3f}",
                "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
                str(tmp_out),
            ]
            subprocess.run(cmd, check=True)
            tmp_out.replace(out_path)
            return out_path, total_dur

        # Xây dựng filter_complex cho nhiều track SFX
        # Input 0: voice_path
        # Input 1..N: valid_events[i-1].sfx_path
        cmd_inputs: list[str] = [
            _get_ffmpeg_bin(), "-y", "-loglevel", "error",
            "-i", str(voice_path),
        ]

        filter_parts: list[str] = []
        # Xử lý voice track (giữ nguyên âm lượng 1.0, pad cuối câu)
        filter_parts.append(f"[0:a]volume=1.0,apad=pad_dur={pad:.3f}[v0]")

        sfx_labels: list[str] = []
        for idx, ev in enumerate(valid_events, start=1):
            cmd_inputs.extend(["-i", str(ev.sfx_path)])
            delay_ms = int(max(0.0, ev.start_time or 0.0) * 1000)
            vol = max(0.05, min(1.0, ev.volume))

            label = f"s{idx}"
            sfx_labels.append(f"[{label}]")
            # adelay nhận format left|right cho stereo
            filter_parts.append(
                f"[{idx}:a]volume={vol:.2f},"
                f"adelay={delay_ms}|{delay_ms},"
                f"atrim=0:{total_dur:.3f}[{label}]"
            )

        # Trộn Voice + tất cả SFX tracks
        all_inputs_str = "[v0]" + "".join(sfx_labels)
        n_inputs = len(valid_events) + 1
        # Sử dụng alimiter để ngăn ngừa digital clipping khi nhiều SFX phát cùng lúc
        filter_parts.append(
            f"{all_inputs_str}amix=inputs={n_inputs}:duration=longest:dropout_transition=0:normalize=0,"
            f"alimiter=limit=0.95:attack=5:release=50[aout]"
        )

        filter_complex_str = ";".join(filter_parts)

        cmd = [
            *cmd_inputs,
            "-filter_complex", filter_complex_str,
            "-map", "[aout]",
            "-t", f"{total_dur:.3f}",
            "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
            str(tmp_out),
        ]

        try:
            subprocess.run(cmd, check=True)
            tmp_out.replace(out_path)
            return out_path, total_dur
        except Exception as err:
            logger.error(f"Lỗi khi trộn âm thanh đa track: {err}")
            if tmp_out.exists():
                tmp_out.unlink(missing_ok=True)
            # Fallback an toàn: xuất voice không sfx nếu FFmpeg filter gặp lỗi
            cmd_fallback = [
                _get_ffmpeg_bin(), "-y", "-loglevel", "error",
                "-i", str(voice_path),
                "-t", f"{voice_dur + pad:.3f}",
                "-c:a", "copy",
                str(out_path),
            ]
            subprocess.run(cmd_fallback, check=True)
            return out_path, voice_dur + pad

