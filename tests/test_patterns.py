"""Unit tests cho PatternDetector và Negation/Exception Handling theo đúng ma trận Test Section 8."""
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from sfx_engine.pattern_detector import PatternDetector


class TestPatternDetector(unittest.TestCase):
    def setUp(self):
        self.detector = PatternDetector()

    def test_neutral_sentence_no_sfx(self):
        """'Hôm nay trời đẹp' -> Không pattern cảm xúc, không SFX."""
        matches = self.detector.detect_patterns("Hôm nay trời đẹp")
        self.assertEqual(len(matches), 0)

    def test_surprise_pattern(self):
        """'Ủa cái gì vậy?' -> Surprise."""
        matches = self.detector.detect_patterns("Ủa cái gì vậy?")
        self.assertGreaterEqual(len(matches), 1)
        cats = [m.category for m in matches]
        self.assertIn("Surprise", cats)

    def test_plot_twist_pattern(self):
        """'Tưởng giàu nhưng hết tiền' -> Plot twist."""
        matches = self.detector.detect_patterns("Tưởng giàu nhưng hết tiền")
        self.assertGreaterEqual(len(matches), 1)
        cats = [m.category for m in matches]
        self.assertIn("PlotTwist", cats)

    def test_negation_khong_buon_cuoi(self):
        """'Không buồn cười chút nào' -> Không Laugh / Không Humor."""
        exc = self.detector.check_negations_and_exceptions("Không buồn cười chút nào", "Humor")
        self.assertTrue(exc.is_suppressed)
        self.assertGreater(exc.penalty, 30)

        # Quét patterns cũng không sinh ra Humor
        matches = self.detector.detect_patterns("Không buồn cười chút nào")
        humor_matches = [m for m in matches if m.category == "Humor"]
        self.assertEqual(len(humor_matches), 0)

    def test_negation_dung_co_cuoi(self):
        """'Đừng có cười' -> Không Laugh / Không Humor."""
        exc = self.detector.check_negations_and_exceptions("Đừng có cười", "Humor")
        self.assertTrue(exc.is_suppressed)

        matches = self.detector.detect_patterns("Đừng có cười")
        humor_matches = [m for m in matches if m.category == "Humor"]
        self.assertEqual(len(humor_matches), 0)

    def test_negation_khong_phai_het_cuu(self):
        """'Không phải hết cứu' -> Không Failure / Không Comedy."""
        exc_f = self.detector.check_negations_and_exceptions("Không phải hết cứu đâu", "Failure")
        self.assertTrue(exc_f.is_suppressed)

        exc_h = self.detector.check_negations_and_exceptions("Không phải hết cứu đâu", "Humor")
        self.assertTrue(exc_h.is_suppressed)

    def test_negation_tuong_hai_nhung_chang_vui(self):
        """'Tưởng hài nhưng chẳng vui' -> Không Laugh."""
        exc = self.detector.check_negations_and_exceptions("Tưởng hài nhưng chẳng vui", "Humor")
        self.assertTrue(exc.is_suppressed)

    def test_failure_chet_may_giua_duong(self):
        """'Chết máy giữa đường' -> Failure, không mặc định Comedy."""
        matches = self.detector.detect_patterns("Chết máy giữa đường")
        self.assertGreaterEqual(len(matches), 1)
        cats = [m.category for m in matches]
        self.assertIn("Failure", cats)

    def test_haha_dung_la_het_cuu(self):
        """'Haha, đúng là hết cứu' -> Khớp cả Humor và Punchline."""
        matches = self.detector.detect_patterns("Haha, đúng là hết cứu")
        self.assertGreaterEqual(len(matches), 1)
        cats = [m.category for m in matches]
        self.assertIn("Humor", cats)


if __name__ == "__main__":
    unittest.main()

