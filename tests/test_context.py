"""Unit tests cho ContextEngine."""
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from sfx_engine.context_engine import ContextEngine


class TestContextEngine(unittest.TestCase):
    def setUp(self):
        self.context = ContextEngine()

    def test_sarcasm_across_comments(self):
        """Kịch bản: Comment 1 mua PC, Comment 2 sập nguồn (Failure), Comment 3 'Trải nghiệm tuyệt vời' -> Sarcasm!"""
        # Comment 1: Bình thường
        score1, _ = self.context.evaluate_context("Mua PC 30 triệu", "Neutral", "Normal")
        self.context.update_history("Neutral", "Normal")
        self.assertEqual(score1, 10.0)

        # Comment 2: Sự cố sập nguồn (Failure)
        score2, _ = self.context.evaluate_context("Chạy game 5 phút thì sập nguồn", "Failure", "Failure")
        self.context.update_history("Failure", "Failure")
        self.assertTrue(self.context.state.has_prior_failure)

        # Comment 3: Khen 'trải nghiệm tuyệt vời' sau khi sập nguồn -> Mỉa mai (Sarcasm)!
        score3, reason = self.context.evaluate_context("Đúng là trải nghiệm tuyệt vời!", "Excitement", "Sarcasm")
        self.assertEqual(score3, 20.0)
        self.assertIn("châm biếm", reason.lower())

    def test_reset_session(self):
        self.context.update_history("Failure", "Failure")
        self.assertTrue(self.context.state.has_prior_failure)
        self.context.reset()
        self.assertFalse(self.context.state.has_prior_failure)


if __name__ == "__main__":
    unittest.main()

