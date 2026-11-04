"""Scoring Engine cho Rule-Based Multi-SFX Engine.

Thực hiện công thức tính điểm chuẩn:
    Score = K + P + C + E + T - N - R
Trong đó:
- K: Keyword match, tối đa 20.
- P: Pattern match, tối đa 25.
- C: Context match, tối đa 20.
- E: Emotion match, tối đa 15.
- T: Timing suitability, tối đa 10.
- N: Negative/exception penalty, tối đa 30.
- R: Repetition penalty, tối đa 15.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ScoreBreakdown:
    """Bảng chi tiết các thành phần điểm số của 1 candidate."""
    k_keyword: float
    p_pattern: float
    c_context: float
    e_emotion: float
    t_timing: float
    n_negative: float
    r_repetition: float
    total_score: float

    def summary(self) -> str:
        return (
            f"Total={self.total_score:.1f} "
            f"(K={self.k_keyword:.0f}, P={self.p_pattern:.0f}, C={self.c_context:.0f}, "
            f"E={self.e_emotion:.0f}, T={self.t_timing:.0f}, N=-{self.n_negative:.0f}, R=-{self.r_repetition:.0f})"
        )


class ScoringEngine:
    """Bộ máy chấm điểm candidate event theo trọng số quy chuẩn."""

    def calculate_score(
        self,
        has_keyword: bool = False,
        pattern_score: float = 0.0,
        context_score: float = 10.0,
        emotion_strength: float = 1.0,
        is_timing_aligned: bool = True,
        negative_penalty: float = 0.0,
        is_repeated_sfx: bool = False,
    ) -> ScoreBreakdown:
        """Tính toán điểm số tổng hợp của candidate."""
        # K: Keyword match (0 - 20)
        k = 18.0 if has_keyword else 0.0

        # P: Pattern match (0 - 25)
        p = min(25.0, pattern_score)

        # C: Context match (0 - 20)
        c = min(20.0, max(0.0, context_score))

        # E: Emotion match (0 - 15)
        e = min(15.0, emotion_strength * 12.0)

        # T: Timing suitability (0 - 10)
        t = 10.0 if is_timing_aligned else 5.0

        # N: Negative / Exception penalty (0 - 30)
        n = min(30.0, max(0.0, negative_penalty))

        # R: Repetition penalty (0 - 15)
        r = 15.0 if is_repeated_sfx else 0.0

        total = k + p + c + e + t - n - r
        total = max(0.0, min(100.0, total))

        return ScoreBreakdown(
            k_keyword=k,
            p_pattern=p,
            c_context=c,
            e_emotion=e,
            t_timing=t,
            n_negative=n,
            r_repetition=r,
            total_score=round(total, 1),
        )

