"""Unit tests cho TextPreprocessor."""
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from sfx_engine.text_preprocessor import TextPreprocessor


class TestTextPreprocessor(unittest.TestCase):
    def setUp(self):
        self.preprocessor = TextPreprocessor()

    def test_segment_clauses(self):
        text = "Ủa cái gì vậy trời? Tưởng giàu nhưng hết tiền! Cười ỉa luôn á 🤣"
        clauses = self.preprocessor.segment_clauses(text)
        self.assertGreaterEqual(len(clauses), 3)
        self.assertTrue(clauses[0].has_question)
        self.assertTrue(clauses[1].has_exclamation)
        self.assertTrue(clauses[2].has_emoji)

    def test_map_anchor_position(self):
        full = "Tưởng mua PC ngon, ai ngờ máy ko lên nguồn!"
        anchor = "ai ngờ"
        start, end, rel = self.preprocessor.map_anchor_position(full, anchor)
        self.assertGreater(start, 0)
        self.assertGreater(end, start)
        self.assertGreater(rel, 0.3)
        self.assertLess(rel, 0.6)

    def test_extract_emojis(self):
        text = "Hài hước vãi 🤣😂 kkk"
        emojis = self.preprocessor.extract_emojis(text)
        self.assertIn("🤣", emojis[0] if emojis else "")


if __name__ == "__main__":
    unittest.main()

