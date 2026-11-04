"""Unit tests cho TimestampMapper."""
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from sfx_engine.timestamp_mapper import TimestampMapper


class TestTimestampMapper(unittest.TestCase):
    def setUp(self):
        self.mapper = TimestampMapper()

    def test_sentence_boundary_start_alignment(self):
        """Từ khóa nằm ngay đầu câu thoại -> confidence = 1.0."""
        boundaries = [
            {"text": "Ủa cái gì vậy trời?", "offset": 1.25, "duration": 1.5}
        ]
        res = self.mapper.align_anchor_time(
            full_text="Ủa cái gì vậy trời?",
            anchor_text="ủa",
            sentence_boundaries=boundaries,
            total_duration=3.0,
        )
        self.assertEqual(res.confidence, 1.0)
        self.assertAlmostEqual(res.timestamp, 1.25, delta=0.05)

    def test_word_interpolated_boundary_alignment(self):
        """Từ khóa nằm giữa câu thoại -> confidence = 0.85."""
        boundaries = [
            {"text": "Tưởng mua máy ngon ai ngờ toang luôn", "offset": 2.0, "duration": 2.0}
        ]
        res = self.mapper.align_anchor_time(
            full_text="Tưởng mua máy ngon ai ngờ toang luôn",
            anchor_text="ai ngờ",
            sentence_boundaries=boundaries,
            total_duration=4.0,
        )
        self.assertEqual(res.confidence, 0.85)
        # Nằm giữa câu offset 2.0s + ~1.0s = ~3.0s
        self.assertGreater(res.timestamp, 2.5)
        self.assertLess(res.timestamp, 3.8)

    def test_syllable_estimation_without_boundaries(self):
        """Không có boundary -> Ước lượng âm tiết (confidence = 0.60)."""
        res = self.mapper.align_anchor_time(
            full_text="Đoạn đầu không có gì nhưng đoạn sau toang luôn",
            anchor_text="toang",
            sentence_boundaries=None,
            total_duration=5.0,
        )
        self.assertEqual(res.confidence, 0.60)
        self.assertGreater(res.timestamp, 2.0)


if __name__ == "__main__":
    unittest.main()

