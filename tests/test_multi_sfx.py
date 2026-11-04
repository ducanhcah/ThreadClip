"""Unit tests cho Multi-SFX planning và backward compatibility trong sound_designer."""
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from sound_designer import SoundDesigner, SoundCue, format_cue_report
from sfx_engine.models import SoundEvent


class TestMultiSFX(unittest.TestCase):
    def setUp(self):
        self.sfx_dir = ROOT / "assets" / "sfx"
        self.designer = SoundDesigner(self.sfx_dir)

    def test_hook_scene_always_starts_with_ting(self):
        """Scene 0 (is_hook=True) luôn kích hoạt ting.mp3 đầu video."""
        events = self.designer.plan_sound_events(
            scene_id=0,
            text="Đừng bao giờ mua vòng phong thủy online nếu chưa biết điều này!",
            is_hook=True,
            total_duration=3.5,
        )
        self.assertGreaterEqual(len(events), 1)
        first = events[0]
        self.assertEqual(first.event_type, "Hook")
        self.assertEqual(first.sfx_path.name, "ting.mp3")
        self.assertAlmostEqual(first.start_time, 0.15, delta=0.05)

    def test_comment_with_three_sfx_events(self):
        """Tiêu chí Phase 1: Một bình luận có thể nhận diện và tạo ít nhất 3 SFX tại 3 timestamp khác nhau."""
        # Câu bình luận có 3 chuyển biến:
        # 1) "Ủa cái gì vậy trời?" -> Bất ngờ / Curiosity (Surprise)
        # 2) "ai ngờ mua xong máy sập nguồn" -> Plot twist / Warning / Failure
        # 3) "cười ỉa luôn á bà con!" -> Humor / Punchline
        boundaries = [
            {"text": "Ủa cái gì vậy trời?", "offset": 0.0, "duration": 1.2},
            {"text": "ai ngờ mua xong máy toang luôn!", "offset": 1.3, "duration": 1.5},
            {"text": "cười ỉa luôn á bà con ơi!", "offset": 2.9, "duration": 1.4},
        ]
        full_text = "Ủa cái gì vậy trời? Ai ngờ mua xong máy toang luôn! Cười ỉa luôn á bà con ơi!"

        events = self.designer.plan_sound_events(
            scene_id=1,
            text=full_text,
            is_hook=False,
            sentence_boundaries=boundaries,
            total_duration=4.5,
        )

        # Kiểm tra đạt tối thiểu 3 sự kiện SFX
        self.assertGreaterEqual(len(events), 3, f"Phải phát hiện ít nhất 3 SFX, nhận được: {len(events)}")

        # Kiểm tra 3 sự kiện có timestamp khác nhau và cách nhau tối thiểu 0.6s
        timestamps = [e.start_time for e in events]
        for i in range(len(timestamps) - 1):
            self.assertGreaterEqual(
                timestamps[i + 1] - timestamps[i],
                0.55,
                f"SFX {i+1} và {i+2} phải cách nhau ít nhất 0.6s để không dính chùm",
            )

        # Kiểm tra file SFX đều tồn tại trên đĩa
        for e in events:
            self.assertTrue(e.sfx_path.exists(), f"File {e.sfx_file} phải tồn tại thực tế")

    def test_backward_compatibility_plan_sound_cue(self):
        """Đảm bảo hàm plan_sound_cue cũ vẫn hoạt động trơn tru."""
        cue = self.designer.plan_sound_cue(
            text="Cười ỉa luôn á, hài vãi chưởng!",
            is_hook=False,
            total_duration=3.0,
        )
        self.assertIsInstance(cue, SoundCue)
        self.assertEqual(cue.emotion, "Humor")
        self.assertIsNotNone(cue.sfx_file)
        self.assertTrue(cue.sfx_file.exists())

    def test_format_cue_report_with_sound_events(self):
        """Báo cáo Markdown format đúng cả SoundEvent."""
        events = [
            SoundEvent(
                event_id="e1", scene_id=1, anchor_text="cười ỉa", char_start=0, char_end=7,
                event_type="Comedy", emotion="Humor", sfx_file=self.sfx_dir / "bonk.mp3",
                score=85.0, priority=1, start_time=1.2, end_time=1.8, volume=0.4, reason="Hài hước",
            )
        ]
        report_md = format_cue_report(events)
        self.assertIn("| Cảnh 1 |", report_md)
        self.assertIn("bonk.mp3", report_md)
        self.assertIn("Score: 85", report_md)


if __name__ == "__main__":
    unittest.main()

