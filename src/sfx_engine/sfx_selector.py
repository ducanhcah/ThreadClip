"""SFX Selector cho Rule-Based Multi-SFX Engine.

Lựa chọn tệp âm thanh phù hợp từ thư viện assets/sfx dựa trên:
- Thể loại (Category): Hook, Humor, Surprise, Failure, Suspense, PlotTwist, Emphasis
- Cảm xúc (Emotion)
- Chống lặp lại âm thanh đã phát gần đây
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = ROOT / "config"
SFX_DIR = ROOT / "assets" / "sfx"


class SFXSelector:
    """Bộ chọn tệp âm thanh (SFX Selector)."""

    def __init__(self, sfx_dir: Path | None = None, config_dir: Path | None = None):
        self.sfx_dir = sfx_dir or SFX_DIR
        self.config_dir = config_dir or CONFIG_DIR
        self.library: dict[str, list[dict[str, Any]]] = self._load_library()

    def _load_library(self) -> dict[str, list[dict[str, Any]]]:
        path = self.config_dir / "sfx_library.json"
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                return data.get("categories", {})
            except Exception:
                pass
        return {}

    def select_sfx(
        self,
        category: str,
        emotion: str = "Neutral",
        recent_history: list[str] | None = None,
    ) -> tuple[Path | None, float]:
        """Chọn file SFX tốt nhất và mức âm lượng tương ứng.

        Returns:
            tuple[Path | None, float]: (đường dẫn file, âm lượng cơ bản)
        """
        recent = recent_history or []
        candidates = self.library.get(category) or self.library.get(emotion) or self.library.get("Neutral", [])

        # Lọc các file thực sự tồn tại trên ổ đĩa
        available: list[tuple[Path, float]] = []
        for item in candidates:
            f_name = item.get("file", "")
            f_path = self.sfx_dir / f_name
            if f_path.exists():
                available.append((f_path, float(item.get("volume", 0.35))))

        if not available:
            # Fallback nếu category rỗng: tìm file bất kỳ trong assets/sfx
            for default_name in ["ting.mp3", "pop.mp3", "bonk.mp3"]:
                p = self.sfx_dir / default_name
                if p.exists():
                    return p, 0.35
            return None, 0.0

        # Ưu tiên chọn file chưa phát gần đây
        non_recent = [cand for cand in available if cand[0].name not in recent]
        if non_recent:
            return non_recent[0]

        # Nếu tất cả đều nằm trong recent, chọn ứng viên đầu tiên
        return available[0]

