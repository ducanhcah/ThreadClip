"""Master Rule-Based Multi-SFX Engine.

Bộ điều phối trung tâm kết nối toàn bộ 5 module:
1. TextPreprocessor: Chuẩn hóa & phân đoạn mệnh đề, bảo toàn ký hiệu.
2. PatternDetector: Nhận diện cấu trúc câu, từ khóa cảm xúc và loại trừ phủ định.
3. ContextEngine: Phân tích tương phản ngữ cảnh đa bình luận (Sarcasm detection).
4. ScoringEngine: Chấm điểm quy chuẩn K + P + C + E + T - N - R.
5. TimestampMapper: Canh mốc thời gian âm thanh chính xác theo boundary / âm tiết.
6. SFXSelector & CooldownManager: Chọn tệp âm thanh và điều tiết mật độ.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from .audio_mixer import AudioMixer
from .context_engine import ContextEngine
from .cooldown_manager import CooldownManager
from .models import SceneEvents, SoundEvent
from .pattern_detector import PatternDetector
from .scoring import ScoringEngine
from .sfx_selector import SFXSelector
from .text_preprocessor import TextPreprocessor
from .timestamp_mapper import TimestampMapper

logger = logging.getLogger("sfx_engine")


class SFXEngine:
    """Hệ thống Rule-Based Multi-SFX Engine hoàn chỉnh."""

    def __init__(self, sfx_dir: Path | None = None, config_dir: Path | None = None):
        self.preprocessor = TextPreprocessor()
        self.pattern_detector = PatternDetector(config_dir=config_dir)
        self.context_engine = ContextEngine()
        self.scoring_engine = ScoringEngine()
        self.timestamp_mapper = TimestampMapper()
        self.sfx_selector = SFXSelector(sfx_dir=sfx_dir, config_dir=config_dir)
        self.cooldown_manager = CooldownManager()
        self.audio_mixer = AudioMixer()

    def reset_session(self):
        """Khởi tạo lại session ngữ cảnh (cho bài viết mới)."""
        self.context_engine.reset()
        self.cooldown_manager.recent_sfx.clear()

    def process_scene(
        self,
        scene_id: int,
        text: str,
        is_hook: bool = False,
        sentence_boundaries: list[dict[str, Any]] | None = None,
        total_duration: float = 3.0,
        user_scale: float = 1.0,
    ) -> list[SoundEvent]:
        """Phân tích văn bản và tạo danh sách SoundEvent tối ưu cho phân cảnh."""
        raw_text = text.strip()
        if not raw_text:
            return []

        candidates: list[SoundEvent] = []
        evt_counter = 1

        # 1. Sự kiện Hook mở đầu video (Luôn có ting.mp3 tại 0.15s)
        if is_hook:
            ting_path, base_vol = self.sfx_selector.select_sfx("Hook", "Excitement")
            if ting_path and ting_path.exists():
                candidates.append(
                    SoundEvent(
                        event_id=f"evt_{scene_id}_{evt_counter}",
                        scene_id=scene_id,
                        anchor_text="Mở đầu video",
                        char_start=0,
                        char_end=min(15, len(raw_text)),
                        event_type="Hook",
                        emotion="Excitement",
                        sfx_file=ting_path,
                        score=95.0,
                        priority=1,
                        start_time=0.15,
                        end_time=0.95,
                        volume=round(max(0.05, min(1.0, 0.45 * user_scale)), 2),
                        reason="Âm thanh ting mở màn video TikTok thu hút chú ý",
                        timing_confidence=1.0,
                    )
                )
                evt_counter += 1

        # 2. Phân đoạn mệnh đề (Clause Segmentation)
        clauses = self.preprocessor.segment_clauses(raw_text)
        if not clauses:
            return self.cooldown_manager.filter_and_schedule(candidates)

        # 3. Quét pattern và đánh giá ngữ cảnh cho từng mệnh đề
        for clause in clauses:
            # Nhận diện pattern
            patterns = self.pattern_detector.detect_patterns(clause.norm_text)
            if not patterns:
                continue

            for pat in patterns:
                # Kiểm tra phủ định (Negation check)
                exc = self.pattern_detector.check_negations_and_exceptions(clause.norm_text, pat.category)
                if exc.is_suppressed:
                    continue

                # Đánh giá ngữ cảnh (Context Engine)
                ctx_score, ctx_reason = self.context_engine.evaluate_context(
                    current_text=clause.norm_text,
                    detected_emotion=pat.emotion,
                    detected_type=pat.event_type,
                )

                # Chọn tệp âm thanh (SFX Selector, chống lặp cả với các sự kiện vừa chọn trong cùng cảnh)
                current_scene_sfx = [c.sfx_path.name for c in candidates if c.sfx_path]
                sfx_file, sfx_vol = self.sfx_selector.select_sfx(
                    category=pat.category,
                    emotion=pat.emotion,
                    recent_history=self.cooldown_manager.recent_sfx + current_scene_sfx,
                )
                if not sfx_file or not sfx_file.exists():
                    continue

                # Canh mốc thời gian âm thanh chính xác (Timestamp Mapper)
                time_res = self.timestamp_mapper.align_anchor_time(
                    full_text=raw_text,
                    anchor_text=pat.anchor_text,
                    sentence_boundaries=sentence_boundaries,
                    total_duration=total_duration,
                )

                # Chấm điểm quy chuẩn (Scoring Engine)
                is_repeated = self.cooldown_manager.is_repeated(sfx_file.name)
                score_res = self.scoring_engine.calculate_score(
                    has_keyword=True,
                    pattern_score=pat.base_score,
                    context_score=ctx_score,
                    emotion_strength=1.2,
                    is_timing_aligned=(time_res.confidence >= 0.8),
                    negative_penalty=exc.penalty,
                    is_repeated_sfx=is_repeated,
                )

                # Ghi nhận trạng thái ngữ cảnh cho các bình luận tiếp theo
                self.context_engine.update_history(pat.emotion, pat.event_type)

                candidates.append(
                    SoundEvent(
                        event_id=f"evt_{scene_id}_{evt_counter}",
                        scene_id=scene_id,
                        anchor_text=pat.anchor_text,
                        char_start=clause.char_start,
                        char_end=clause.char_end,
                        event_type=pat.event_type,
                        emotion=pat.emotion,
                        sfx_file=sfx_file,
                        score=score_res.total_score,
                        priority=pat.priority,
                        start_time=time_res.timestamp,
                        end_time=round(time_res.timestamp + 0.8, 2),
                        volume=round(max(0.05, min(1.0, sfx_vol * user_scale)), 2),
                        reason=f"{pat.reason} | {ctx_reason} ({score_res.summary()})",
                        timing_confidence=time_res.confidence,
                    )
                )
                evt_counter += 1

        # 4. Lọc qua Cooldown Manager (min_gap, min_score, chống lặp)
        final_events = self.cooldown_manager.filter_and_schedule(candidates)
        return final_events
