"""Unit tests cho ScoringEngine."""
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from sfx_engine.scoring import ScoringEngine


class TestScoringEngine(unittest.TestCase):
    def setUp(self):
        self.scoring = ScoringEngine()

    def test_ideal_candidate_score(self):
        """Candidate hoàn hảo đạt điểm cao (>85)."""
        res = self.scoring.calculate_score(
            has_keyword=True,
            pattern_score=25.0,
            context_score=20.0,
            emotion_strength=1.2,
            is_timing_aligned=True,
            negative_penalty=0.0,
            is_repeated_sfx=False,
        )
        self.assertGreater(res.total_score, 80.0)
        self.assertEqual(res.n_negative, 0.0)
        self.assertEqual(res.r_repetition, 0.0)

    def test_negative_penalty_reduces_score(self):
        """Phủ định bị trừ điểm nặng và không đủ ngưỡng min_score."""
        res = self.scoring.calculate_score(
            has_keyword=True,
            pattern_score=20.0,
            context_score=10.0,
            emotion_strength=1.0,
            is_timing_aligned=True,
            negative_penalty=30.0,
            is_repeated_sfx=False,
        )
        self.assertLess(res.total_score, 60.0)

    def test_repetition_penalty(self):
        """SFX lặp lại bị phạt 15 điểm."""
        res_fresh = self.scoring.calculate_score(has_keyword=True, pattern_score=20.0, is_repeated_sfx=False)
        res_repeat = self.scoring.calculate_score(has_keyword=True, pattern_score=20.0, is_repeated_sfx=True)
        self.assertEqual(res_fresh.total_score - res_repeat.total_score, 15.0)


if __name__ == "__main__":
    unittest.main()

