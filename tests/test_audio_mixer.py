"""Unit tests cho AudioMixer trong sfx_engine."""
import subprocess
import unittest
from pathlib import Path
import sys

# Ensure src/ is in sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from sfx_engine.models import SoundEvent
from sfx_engine.audio_mixer import AudioMixer, get_audio_duration


class TestAudioMixer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_dir = ROOT / "output" / "test_mixer"
        cls.test_dir.mkdir(parents=True, exist_ok=True)
        cls.sfx_dir = ROOT / "assets" / "sfx"

        # Tạo một file âm thanh giả lập (sinewave 440Hz 4.0s) để test nếu cần
        cls.dummy_voice = cls.test_dir / "dummy_voice.wav"
        subprocess.run(
            [
                "ffmpeg", "-y", "-loglevel", "error",
                "-f", "lavfi", "-i", "sine=frequency=440:duration=4.0",
                "-ar", "44100", "-ac", "2",
                str(cls.dummy_voice)
            ],
            check=True
        )

    def test_duration_measurement(self):
        dur = get_audio_duration(self.dummy_voice)
        self.assertAlmostEqual(dur, 4.0, delta=0.2)

    def test_mix_empty_events(self):
        mixer = AudioMixer(default_pad=0.5)
        out_audio = self.test_dir / "out_empty.m4a"
        res_path, total_dur = mixer.mix_voice_and_sfx(
            voice_path=self.dummy_voice,
            sound_events=[],
            out_path=out_audio,
            pad=0.5,
        )
        self.assertTrue(res_path.exists())
        self.assertAlmostEqual(total_dur, 4.5, delta=0.2)

    def test_mix_three_sfx_events(self):
        """Tiêu chí Phase 1: Trộn ít nhất 3 SFX tại 3 timestamp khác nhau."""
        mixer = AudioMixer(default_pad=0.4)
        out_audio = self.test_dir / "out_3_sfx.m4a"

        # Sử dụng các file SFX có sẵn trong assets/sfx
        ting = self.sfx_dir / "ting.mp3"
        bonk = self.sfx_dir / "bonk.mp3"
        bruh = self.sfx_dir / "bruh.mp3"

        self.assertTrue(ting.exists(), "ting.mp3 phải tồn tại")
        self.assertTrue(bonk.exists(), "bonk.mp3 phải tồn tại")
        self.assertTrue(bruh.exists(), "bruh.mp3 phải tồn tại")

        events = [
            SoundEvent(
                event_id="e1", scene_id=1, anchor_text="ting", char_start=0, char_end=4,
                event_type="Hook", emotion="Excitement", sfx_file=ting, score=90.0, priority=1,
                start_time=0.2, end_time=1.0, volume=0.4, reason="Mở đầu",
            ),
            SoundEvent(
                event_id="e2", scene_id=1, anchor_text="bonk", char_start=10, char_end=14,
                event_type="Transition", emotion="Surprise", sfx_file=bonk, score=85.0, priority=2,
                start_time=1.5, end_time=2.0, volume=0.35, reason="Chuyển vế",
            ),
            SoundEvent(
                event_id="e3", scene_id=1, anchor_text="bruh", char_start=20, char_end=24,
                event_type="Comedy", emotion="Humor", sfx_file=bruh, score=88.0, priority=1,
                start_time=2.8, end_time=3.5, volume=0.4, reason="Punchline",
            ),
        ]

        res_path, total_dur = mixer.mix_voice_and_sfx(
            voice_path=self.dummy_voice,
            sound_events=events,
            out_path=out_audio,
            pad=0.4,
        )
        self.assertTrue(res_path.exists())
        self.assertGreaterEqual(total_dur, 4.4)
        # File không rỗng
        self.assertGreater(res_path.stat().st_size, 5000)

    def test_ignore_invalid_or_missing_sfx(self):
        mixer = AudioMixer(default_pad=0.4)
        out_audio = self.test_dir / "out_invalid.m4a"

        missing_sfx = self.sfx_dir / "khong_ton_tai_123.mp3"
        events = [
            SoundEvent(
                event_id="bad1", scene_id=1, anchor_text="missing", char_start=0, char_end=5,
                event_type="None", emotion="Neutral", sfx_file=missing_sfx, score=50.0, priority=3,
                start_time=0.5, end_time=1.0, volume=0.4, reason="Lỗi",
            ),
            SoundEvent(
                event_id="bad2", scene_id=1, anchor_text="negative_time", char_start=0, char_end=5,
                event_type="None", emotion="Neutral", sfx_file=self.sfx_dir / "ting.mp3",
                score=50.0, priority=3, start_time=-1.0, end_time=0.0, volume=0.4, reason="Lỗi",
            ),
        ]
        res_path, total_dur = mixer.mix_voice_and_sfx(
            voice_path=self.dummy_voice,
            sound_events=events,
            out_path=out_audio,
            pad=0.4,
        )
        self.assertTrue(res_path.exists())
        self.assertAlmostEqual(total_dur, 4.4, delta=0.2)


if __name__ == "__main__":
    unittest.main()
