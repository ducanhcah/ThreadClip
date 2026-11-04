"""ThreadClip Studio - Giao diện đồ họa tối giản, hiện đại (1 màn hình, 1 việc).

Triết lý thiết kế:
  - Tối giản: Mở app là thấy ngay ô dán link + nút TẠO VIDEO.
  - Tự động nhận diện link Threads từ clipboard khi vừa mở app.
  - 3 Preset thông minh: "Viral nhanh", "Tâm sự", "Hài hước" thay thế các cài đặt phức tạp.
  - Tiến trình trực quan với các bước thân thiện, ẩn log kỹ thuật sau nút "Chi tiết".
  - Tự nhớ tên kênh bản quyền (Watermark) vào config.json cho các lần sau.
  - Báo lỗi tiếng Việt dễ hiểu kèm nút "Copy lỗi" để gửi hỗ trợ.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText

SRC_DIR = Path(__file__).resolve().parent
ROOT = SRC_DIR.parent
CONFIG_FILE = ROOT / ".config.json"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Ưu tiên Python hiện tại hoặc Python trong runtime
PYTHON_EXE = sys.executable
if (ROOT / "runtime" / "python" / "python.exe").exists():
    PYTHON_EXE = str((ROOT / "runtime" / "python" / "python.exe").resolve())


POS_MAP = {
    "Phía trên thẻ - Lệch trái (Chuẩn TikTok)": "above-card-left",
    "Phía trên thẻ - Lệch phải": "above-card-right",
    "Phía trên thẻ - Căn giữa": "above-card-center",
    "Góc trên bên phải màn hình": "top-right",
    "Góc dưới bên trái màn hình": "bottom-left",
    "Góc dưới bên phải màn hình": "bottom-right",
}
REV_POS_MAP = {v: k for k, v in POS_MAP.items()}

TTS_ENGINE_MAP = {
    "Edge Neural (Chuẩn tự nhiên)": "edge",
    "Google TTS (Cực nhanh, chống lag)": "gtts",
}
REV_TTS_ENGINE_MAP = {v: k for k, v in TTS_ENGINE_MAP.items()}


def load_config() -> dict:
    default_config = {
        "watermark": "",
        "watermark_pos": "above-card-left",
        "preset": "viral",
        "rate": "1.15x",
        "top": 5,
        "enable_music": True,
        "enable_video_bg": True,
        "with_outro": True,
        "custom_video": "",
        "mask_user": False,
        "tts_engine": "edge",
    }
    if CONFIG_FILE.exists():
        try:
            saved = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            default_config.update(saved)
        except Exception:
            pass
    return default_config


def save_config(cfg: dict):
    try:
        CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


class ThreadClipApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ThreadClip - Tạo Video TikTok Từ Threads")
        self.geometry("780x760")
        self.minsize(700, 680)
        self.configure(bg="#0f1117")

        # Căn giữa màn hình
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = max(0, (sw - 780) // 2)
        y = max(0, (sh - 760) // 2)
        self.geometry(f"+{x}+{y}")

        self.cfg = load_config()
        self.is_running = False
        self.process: subprocess.Popen | None = None
        self.current_video_path: Path | None = None
        self.tiktok_title: str = ""
        self.log_buffer: list[str] = []
        self.show_details = False
        self.show_advanced = False

        self._setup_styles()
        self._build_ui()
        self._auto_detect_clipboard()

    def _setup_styles(self):
        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        # Màu sắc chủ đạo Dark Mode sang trọng
        self.c_bg = "#0f1117"
        self.c_card = "#1a1d24"
        self.c_border = "#2e3440"
        self.c_text = "#f8fafc"
        self.c_subtext = "#94a3b8"
        self.c_accent = "#3b82f6"
        self.c_success = "#10b981"
        self.c_error = "#ef4444"

        # Style Progressbar
        self.style.configure(
            "TProgressbar",
            background=self.c_accent,
            troughcolor="#1e222b",
            borderwidth=0,
            thickness=8,
        )

    def _build_ui(self):
        # ── HEADER ─────────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=self.c_bg, padx=24, pady=16)
        hdr.pack(fill="x")

        title_box = tk.Frame(hdr, bg=self.c_bg)
        title_box.pack(side="left")

        logo_lbl = tk.Label(
            title_box, text="🎬 ThreadClip",
            font=("Segoe UI", 18, "bold"), bg=self.c_bg, fg="#38bdf8"
        )
        logo_lbl.pack(anchor="w")

        tagline_lbl = tk.Label(
            title_box, text="Biến bài viết Threads thành video TikTok triệu view chỉ với 1 cú click",
            font=("Segoe UI", 9), bg=self.c_bg, fg=self.c_subtext
        )
        tagline_lbl.pack(anchor="w")

        # Khung chứa nội dung cuộn chính
        main_container = tk.Frame(self, bg=self.c_bg, padx=24)
        main_container.pack(fill="both", expand=True)

        # ── 1. CARD CHÍNH: DÁN LINK THREADS ────────────────────────────────────
        link_card = tk.Frame(main_container, bg=self.c_card, bd=1, relief="solid", highlightbackground=self.c_border, highlightthickness=1)
        link_card.pack(fill="x", pady=(0, 14), ipadx=14, ipady=12)

        lbl_row = tk.Frame(link_card, bg=self.c_card)
        lbl_row.pack(fill="x", padx=12, pady=(4, 6))

        tk.Label(
            lbl_row, text="📌 Dán liên kết bài viết Threads:",
            font=("Segoe UI", 10, "bold"), bg=self.c_card, fg=self.c_text
        ).pack(side="left")

        self.clip_hint = tk.Label(
            lbl_row, text="", font=("Segoe UI", 8, "italic"), bg=self.c_card, fg=self.c_success
        )
        self.clip_hint.pack(side="right")

        input_row = tk.Frame(link_card, bg=self.c_card)
        input_row.pack(fill="x", padx=12, pady=(0, 6))

        self.url_var = tk.StringVar()
        self.url_entry = tk.Entry(
            input_row, textvariable=self.url_var,
            font=("Segoe UI", 11), bg="#111318", fg="#f1f5f9",
            insertbackground="#38bdf8", relief="flat", bd=0, highlightthickness=1,
            highlightbackground="#334155", highlightcolor=self.c_accent
        )
        self.url_entry.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 8))

        paste_btn = tk.Button(
            input_row, text="📋 Dán link", font=("Segoe UI", 9, "bold"),
            bg="#2563eb", fg="#ffffff", activebackground="#1d4ed8", activeforeground="#ffffff",
            relief="flat", bd=0, padx=14, pady=6, cursor="hand2", command=self._paste_clipboard
        )
        paste_btn.pack(side="right")

        # ── 2. PRESETS THÔNG MINH (3 LỰA CHỌN) ─────────────────────────────────
        preset_card = tk.Frame(main_container, bg=self.c_card, bd=1, relief="solid", highlightbackground=self.c_border, highlightthickness=1)
        preset_card.pack(fill="x", pady=(0, 14), padx=0, ipadx=10, ipady=10)

        tk.Label(
            preset_card, text="🎯 Chọn phong cách video:",
            font=("Segoe UI", 9, "bold"), bg=self.c_card, fg=self.c_subtext
        ).pack(anchor="w", padx=12, pady=(2, 8))

        presets_box = tk.Frame(preset_card, bg=self.c_card)
        presets_box.pack(fill="x", padx=10)

        self.preset_var = tk.StringVar(value=self.cfg.get("preset", "viral"))

        self.preset_cards = {}
        preset_defs = [
            ("viral", "⚡ Viral nhanh", "1.15x • 5 cmt • Gameplay vui nhộn • SFX meme", "#3b82f6"),
            ("story", "☕ Tâm sự", "0.95x • 7 cmt • ASMR thư giãn • Nhạc êm dịu", "#a855f7"),
            ("comedy", "🤣 Hài hước", "1.1x • 5 cmt • Minecraft Parkour • Meme hài", "#f59e0b"),
        ]

        for idx, (p_id, p_name, p_desc, p_color) in enumerate(preset_defs):
            btn = tk.Button(
                presets_box, text=f"{p_name}\n{p_desc}",
                font=("Segoe UI", 9, "bold"), justify="center",
                relief="flat", bd=1, cursor="hand2", padx=8, pady=8,
                command=lambda pid=p_id: self._select_preset(pid)
            )
            btn.grid(row=0, column=idx, sticky="nsew", padx=4)
            presets_box.grid_columnconfigure(idx, weight=1)
            self.preset_cards[p_id] = (btn, p_color)

        self._update_preset_buttons()

        # ── 3. NÚT LỚN DUY NHẤT: TẠO VIDEO ─────────────────────────────────────
        action_box = tk.Frame(main_container, bg=self.c_bg)
        action_box.pack(fill="x", pady=(2, 10))

        self.action_btn = tk.Button(
            action_box, text="🚀 TẠO VIDEO NGAY",
            font=("Segoe UI", 12, "bold"), bg="#2563eb", fg="#ffffff",
            activebackground="#1d4ed8", activeforeground="#ffffff",
            relief="flat", bd=0, pady=10, cursor="hand2", command=self._start_task
        )
        self.action_btn.pack(fill="x")

        # ── 4. THANH TIẾN TRÌNH & TRẠNG THÁI ────────────────────────────────────
        self.status_card = tk.Frame(main_container, bg=self.c_card, bd=1, relief="solid", highlightbackground=self.c_border, highlightthickness=1)
        self.status_card.pack(fill="x", pady=(0, 10), ipadx=12, ipady=10)

        status_header = tk.Frame(self.status_card, bg=self.c_card)
        status_header.pack(fill="x")

        self.status_lbl = tk.Label(
            status_header, text="Sẵn sàng tạo video",
            font=("Segoe UI", 10, "bold"), bg=self.c_card, fg="#38bdf8"
        )
        self.status_lbl.pack(side="left")

        self.detail_toggle_btn = tk.Button(
            status_header, text="▶ Chi tiết kỹ thuật",
            font=("Segoe UI", 8), bg=self.c_card, fg=self.c_subtext,
            activebackground=self.c_card, activeforeground=self.c_text,
            relief="flat", bd=0, cursor="hand2", command=self._toggle_details
        )
        self.detail_toggle_btn.pack(side="right")

        self.prog_var = tk.DoubleVar(value=0)
        self.prog_bar = ttk.Progressbar(self.status_card, variable=self.prog_var, maximum=100, style="TProgressbar")
        self.prog_bar.pack(fill="x", pady=(8, 4))

        # Khung hành động sau khi thành công (ẩn mặc định)
        self.success_box = tk.Frame(self.status_card, bg=self.c_card)
        
        self.open_vid_btn = tk.Button(
            self.success_box, text="🎬 Xem video",
            font=("Segoe UI", 9, "bold"), bg="#059669", fg="#ffffff",
            activebackground="#047857", activeforeground="#ffffff",
            relief="flat", bd=0, padx=12, pady=5, cursor="hand2", command=self._open_video
        )
        self.open_vid_btn.pack(side="left", padx=(0, 8))

        self.open_dir_btn = tk.Button(
            self.success_box, text="📁 Mở thư mục",
            font=("Segoe UI", 9), bg="#334155", fg="#ffffff",
            activebackground="#475569", activeforeground="#ffffff",
            relief="flat", bd=0, padx=12, pady=5, cursor="hand2", command=self._open_dir
        )
        self.open_dir_btn.pack(side="left", padx=(0, 8))

        self.copy_title_btn = tk.Button(
            self.success_box, text="📋 Copy tiêu đề TikTok",
            font=("Segoe UI", 9), bg="#334155", fg="#ffffff",
            activebackground="#475569", activeforeground="#ffffff",
            relief="flat", bd=0, padx=12, pady=5, cursor="hand2", command=self._copy_title
        )
        self.copy_title_btn.pack(side="left")

        # Khung báo lỗi và nút copy lỗi (ẩn mặc định)
        self.error_box = tk.Frame(self.status_card, bg=self.c_card)
        self.copy_err_btn = tk.Button(
            self.error_box, text="📋 Copy mã lỗi để gửi hỗ trợ",
            font=("Segoe UI", 9, "bold"), bg="#dc2626", fg="#ffffff",
            activebackground="#b91c1c", activeforeground="#ffffff",
            relief="flat", bd=0, padx=12, pady=5, cursor="hand2", command=self._copy_error
        )
        self.copy_err_btn.pack(side="left")

        # Khung log chi tiết kỹ thuật (ẩn mặc định)
        self.log_container = tk.Frame(self.status_card, bg="#111318")
        self.log_text = ScrolledText(
            self.log_container, height=6, bg="#111318", fg="#94a3b8",
            font=("Consolas", 8), wrap="word", relief="flat", bd=0
        )
        self.log_text.pack(fill="both", expand=True, padx=4, pady=4)
        self.log_text.tag_config("err", foreground="#f87171")
        self.log_text.tag_config("ok", foreground="#34d399")

        # ── 5. TÙY CHỌN NÂNG CAO (GẬP LẠI MẶC ĐỊNH) ───────────────────────────
        adv_card = tk.Frame(main_container, bg=self.c_bg)
        adv_card.pack(fill="x", pady=(4, 10))

        self.adv_header = tk.Button(
            adv_card, text="⚙️ Tùy chọn nâng cao (Bản quyền kênh, giọng đọc, nền...) ▼",
            font=("Segoe UI", 9), bg=self.c_bg, fg=self.c_subtext,
            activebackground=self.c_bg, activeforeground=self.c_text,
            relief="flat", bd=0, cursor="hand2", anchor="w", command=self._toggle_advanced
        )
        self.adv_header.pack(fill="x")

        self.adv_body = tk.Frame(adv_card, bg=self.c_card, bd=1, relief="solid", highlightbackground=self.c_border, highlightthickness=1)

        # Hàng 1: Bản quyền kênh (Watermark)
        r1 = tk.Frame(self.adv_body, bg=self.c_card)
        r1.pack(fill="x", padx=14, pady=(10, 6))

        tk.Label(r1, text="Bản quyền kênh (Watermark):", font=("Segoe UI", 9), bg=self.c_card, fg=self.c_text).pack(side="left")
        self.wm_var = tk.StringVar(value=self.cfg.get("watermark", ""))
        self.wm_entry = tk.Entry(
            r1, textvariable=self.wm_var, width=18, font=("Segoe UI", 9),
            bg="#111318", fg=self.c_text, insertbackground=self.c_accent,
            relief="flat", bd=0, highlightthickness=1, highlightbackground="#334155"
        )
        self.wm_entry.pack(side="left", padx=8, ipady=3)
        tk.Label(r1, text="(Tự lưu lại cho lần sau)", font=("Segoe UI", 8), bg=self.c_card, fg=self.c_subtext).pack(side="left")

        # Vị trí watermark tiếng Việt
        raw_pos = self.cfg.get("watermark_pos", "above-card-left")
        init_pos_label = REV_POS_MAP.get(raw_pos, list(POS_MAP.keys())[0])
        self.wm_pos_label_var = tk.StringVar(value=init_pos_label)
        wm_pos_cb = ttk.Combobox(
            r1, textvariable=self.wm_pos_label_var, state="readonly", width=34,
            values=list(POS_MAP.keys())
        )
        wm_pos_cb.pack(side="right")
        tk.Label(r1, text="Vị trí:", font=("Segoe UI", 9), bg=self.c_card, fg=self.c_text).pack(side="right", padx=6)

        # Hàng 2: Số bình luận & Tốc độ đọc
        r2 = tk.Frame(self.adv_body, bg=self.c_card)
        r2.pack(fill="x", padx=14, pady=6)

        tk.Label(r2, text="Số bình luận:", font=("Segoe UI", 9), bg=self.c_card, fg=self.c_text).pack(side="left")
        self.top_var = tk.IntVar(value=self.cfg.get("top", 5))
        top_cb = ttk.Combobox(r2, textvariable=self.top_var, state="readonly", width=6, values=[3, 5, 7, 10, 15])
        top_cb.pack(side="left", padx=8)

        tk.Label(r2, text="Tốc độ đọc:", font=("Segoe UI", 9), bg=self.c_card, fg=self.c_text).pack(side="left", padx=(14, 6))
        self.rate_var = tk.StringVar(value=self.cfg.get("rate", "1.15x"))
        rate_cb = ttk.Combobox(r2, textvariable=self.rate_var, state="readonly", width=8, values=["0.85x", "0.95x", "1.0x", "1.1x", "1.15x", "1.2x", "1.25x"])
        rate_cb.pack(side="left")

        tk.Label(r2, text="Giọng đọc:", font=("Segoe UI", 9), bg=self.c_card, fg=self.c_text).pack(side="left", padx=(14, 6))
        raw_engine = self.cfg.get("tts_engine", "edge")
        init_engine_label = REV_TTS_ENGINE_MAP.get(raw_engine, list(TTS_ENGINE_MAP.keys())[0])
        self.tts_engine_label_var = tk.StringVar(value=init_engine_label)
        engine_cb = ttk.Combobox(
            r2, textvariable=self.tts_engine_label_var, state="readonly", width=25,
            values=list(TTS_ENGINE_MAP.keys())
        )
        engine_cb.pack(side="left")

        # Hàng 3: Bật/Tắt Nhạc nền, Video nền & Màn Outro
        r3 = tk.Frame(self.adv_body, bg=self.c_card)
        r3.pack(fill="x", padx=14, pady=6)

        self.enable_video_bg_var = tk.BooleanVar(value=self.cfg.get("enable_video_bg", True))
        tk.Checkbutton(
            r3, text="Bật video nền chuyển động", variable=self.enable_video_bg_var,
            font=("Segoe UI", 9), bg=self.c_card, fg=self.c_text,
            selectcolor="#111318", activebackground=self.c_card, activeforeground=self.c_text,
            command=self._on_video_bg_toggle
        ).pack(side="left", padx=(0, 14))

        self.enable_music_var = tk.BooleanVar(value=self.cfg.get("enable_music", True))
        tk.Checkbutton(
            r3, text="Bật nhạc nền TikTok", variable=self.enable_music_var,
            font=("Segoe UI", 9), bg=self.c_card, fg=self.c_text,
            selectcolor="#111318", activebackground=self.c_card, activeforeground=self.c_text
        ).pack(side="left", padx=(0, 14))

        self.outro_var = tk.BooleanVar(value=self.cfg.get("with_outro", True))
        tk.Checkbutton(
            r3, text="Màn Outro", variable=self.outro_var,
            font=("Segoe UI", 9), bg=self.c_card, fg=self.c_text,
            selectcolor="#111318", activebackground=self.c_card, activeforeground=self.c_text
        ).pack(side="left", padx=(0, 14))

        self.mask_user_var = tk.BooleanVar(value=self.cfg.get("mask_user", False))
        tk.Checkbutton(
            r3, text="Ẩn danh (Che tên & avatar)", variable=self.mask_user_var,
            font=("Segoe UI", 9), bg=self.c_card, fg=self.c_text,
            selectcolor="#111318", activebackground=self.c_card, activeforeground=self.c_text
        ).pack(side="left")

        # Hàng 4: Video nền riêng tùy chọn (MP4)
        self.r4 = tk.Frame(self.adv_body, bg=self.c_card)
        self.r4.pack(fill="x", padx=14, pady=(6, 12))

        self.custom_vid_lbl = tk.Label(self.r4, text="Video nền riêng (MP4):", font=("Segoe UI", 9), bg=self.c_card, fg=self.c_text)
        self.custom_vid_lbl.pack(side="left")
        self.custom_vid_var = tk.StringVar(value=self.cfg.get("custom_video", ""))
        self.custom_entry = tk.Entry(
            self.r4, textvariable=self.custom_vid_var, font=("Segoe UI", 9),
            bg="#111318", fg=self.c_text, relief="flat", bd=0, highlightthickness=1, highlightbackground="#334155"
        )
        self.custom_entry.pack(side="left", fill="x", expand=True, padx=8, ipady=3)

        self.browse_vid_btn = tk.Button(
            self.r4, text="Chọn file...", font=("Segoe UI", 8),
            bg="#334155", fg="#ffffff", activebackground="#475569", activeforeground="#ffffff",
            relief="flat", bd=0, padx=8, pady=3, cursor="hand2", command=self._choose_custom_video
        )
        self.browse_vid_btn.pack(side="right")

    # ── LOGIC XỬ LÝ ────────────────────────────────────────────────────────────
    def _auto_detect_clipboard(self):
        """Tự động kiểm tra clipboard khi mở app."""
        try:
            clip = self.clipboard_get().strip()
            if ("threads.net" in clip or "threads.com" in clip) and len(clip) > 15:
                self.url_var.set(clip)
                self.clip_hint.config(text="✨ Đã tự nhận link từ clipboard!")
        except Exception:
            pass

    def _paste_clipboard(self):
        try:
            clip = self.clipboard_get().strip()
            if clip:
                self.url_var.set(clip)
                self.clip_hint.config(text="✓ Đã dán!")
        except Exception:
            pass

    def _select_preset(self, p_id: str):
        self.preset_var.set(p_id)
        if p_id == "viral":
            self.rate_var.set("1.15x")
            self.top_var.set(5)
        elif p_id == "story":
            self.rate_var.set("0.95x")
            self.top_var.set(7)
        elif p_id == "comedy":
            self.rate_var.set("1.1x")
            self.top_var.set(5)
        self._update_preset_buttons()

    def _update_preset_buttons(self):
        cur = self.preset_var.get()
        for pid, (btn, color) in self.preset_cards.items():
            if pid == cur:
                btn.config(bg=color, fg="#ffffff", bd=2, highlightbackground="#ffffff")
            else:
                btn.config(bg="#222630", fg="#94a3b8", bd=1, highlightbackground=self.c_border)

    def _toggle_details(self):
        self.show_details = not self.show_details
        if self.show_details:
            self.detail_toggle_btn.config(text="▼ Ẩn chi tiết")
            self.log_container.pack(fill="both", expand=True, pady=(8, 0))
        else:
            self.detail_toggle_btn.config(text="▶ Chi tiết kỹ thuật")
            self.log_container.pack_forget()

    def _toggle_advanced(self):
        self.show_advanced = not self.show_advanced
        if self.show_advanced:
            self.adv_header.config(text="⚙️ Tùy chọn nâng cao (Click để đóng) ▲")
            self.adv_body.pack(fill="x", pady=(6, 0))
        else:
            self.adv_header.config(text="⚙️ Tùy chọn nâng cao (Bản quyền kênh, giọng đọc, nền...) ▼")
            self.adv_body.pack_forget()

    def _on_video_bg_toggle(self):
        enabled = self.enable_video_bg_var.get()
        state = "normal" if enabled else "disabled"
        fg = self.c_text if enabled else self.c_subtext
        self.custom_vid_lbl.config(fg=fg)
        self.custom_entry.config(state=state)
        self.browse_vid_btn.config(state=state)

    def _choose_custom_video(self):
        f = filedialog.askopenfilename(
            title="Chọn file video nền (MP4)",
            filetypes=[("Video file", "*.mp4;*.webm;*.mov;*.mkv"), ("Tất cả", "*.*")]
        )
        if f:
            self.custom_vid_var.set(f)

    def _log(self, text: str):
        self.log_buffer.append(text)
        tag = None
        if "Lỗi" in text or "error" in text.lower():
            tag = "err"
        elif "thành công" in text.lower() or "hoàn tất" in text.lower():
            tag = "ok"

        self.log_text.insert("end", text, tag)
        self.log_text.see("end")

    def _start_task(self):
        if self.is_running:
            return

        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("Thiếu liên kết", "Vui lòng dán link bài viết Threads cần tạo video!")
            self.url_entry.focus_set()
            return

        # Lưu cài đặt
        self.cfg["watermark"] = self.wm_var.get().strip()
        pos_cli = POS_MAP.get(self.wm_pos_label_var.get(), "above-card-left")
        self.cfg["watermark_pos"] = pos_cli
        self.cfg["preset"] = self.preset_var.get()
        self.cfg["rate"] = self.rate_var.get()
        self.cfg["top"] = self.top_var.get()
        self.cfg["enable_music"] = self.enable_music_var.get()
        self.cfg["enable_video_bg"] = self.enable_video_bg_var.get()
        self.cfg["with_outro"] = self.outro_var.get()
        self.cfg["custom_video"] = self.custom_vid_var.get().strip()
        self.cfg["mask_user"] = self.mask_user_var.get()
        engine_key = TTS_ENGINE_MAP.get(self.tts_engine_label_var.get(), "edge")
        self.cfg["tts_engine"] = engine_key
        save_config(self.cfg)

        # Cập nhật giao diện khi bắt đầu chạy
        self.is_running = True
        self.log_buffer = []
        self.log_text.delete("1.0", "end")
        self.prog_var.set(5)
        self.status_lbl.config(text="⏳ Đang khởi động...", fg="#38bdf8")
        self.action_btn.config(state="disabled", text="⏳ ĐANG XỬ LÝ VIDEO...", bg="#475569")
        self.success_box.pack_forget()
        self.error_box.pack_forget()

        # Dựng lệnh CLI
        cmd = [PYTHON_EXE, "-u", str(SRC_DIR / "main.py"), url]
        cmd.extend(["--top", str(self.top_var.get())])
        cmd.extend(["--rate", self.rate_var.get()])
        cmd.extend(["--dark", "--clean"])

        if self.wm_var.get().strip():
            cmd.extend(["--watermark", self.wm_var.get().strip()])
            cmd.extend(["--watermark-pos", pos_cli])

        if not self.outro_var.get():
            cmd.append("--no-outro")

        if self.mask_user_var.get():
            cmd.append("--mask-user")

        cmd.extend(["--tts-engine", engine_key])

        # Xử lý Video nền
        if not self.enable_video_bg_var.get():
            cmd.append("--no-video-bg")
        else:
            custom_v = self.custom_vid_var.get().strip()
            preset = self.preset_var.get()
            if custom_v and Path(custom_v).exists():
                cmd.extend(["--video-bg", custom_v])
            elif preset == "viral":
                subway = ROOT / "assets" / "video" / "Subway-Surfers-Gameplay.mp4"
                if subway.exists():
                    cmd.extend(["--video-bg", str(subway)])
                else:
                    cmd.extend(["--video-bg", str(ROOT / "assets" / "video")])
            elif preset == "story":
                sand = ROOT / "assets" / "video" / "Satisfying-Kinetic-Sand-ASMR.mp4"
                if sand.exists():
                    cmd.extend(["--video-bg", str(sand)])
                else:
                    cmd.extend(["--video-bg", str(ROOT / "assets" / "video")])
            elif preset == "comedy":
                mc = ROOT / "assets" / "video" / "Minecraft-Parkour-Gameplay.mp4"
                if mc.exists():
                    cmd.extend(["--video-bg", str(mc)])
                else:
                    cmd.extend(["--video-bg", str(ROOT / "assets" / "video")])

        # Xử lý Nhạc nền & SFX
        preset = self.preset_var.get()
        if self.enable_music_var.get():
            cmd.append("--with-music")
            if preset == "viral":
                cmd.extend(["--music-volume", "0.12"])
            elif preset == "story":
                cmd.extend(["--music-volume", "0.10"])
            elif preset == "comedy":
                cmd.extend(["--music-volume", "0.14"])

        if preset == "story":
            cmd.append("--no-sfx")
        elif preset == "viral":
            cmd.extend(["--sfx-volume", "0.35"])
        elif preset == "comedy":
            cmd.extend(["--sfx-volume", "0.45"])

        t = threading.Thread(target=self._run_process, args=(cmd,), daemon=True)
        t.start()

    def _run_process(self, cmd: list[str]):
        video_out: Path | None = None
        extracted_title = ""
        capturing_title = False

        try:
            startupinfo = None
            if os.name == "nt":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                startupinfo=startupinfo,
                bufsize=1,
            )

            for line in iter(self.process.stdout.readline, ""):
                if not line:
                    break
                self.after(0, self._log, line)

                # Cập nhật trạng thái thân thiện
                if "[1/5]" in line:
                    self.after(0, self._update_step, 20, "🔍 Bước 1/4: Đang đọc bài Threads & lọc bình luận...")
                elif "[2/5]" in line:
                    self.after(0, self._update_step, 40, "🎨 Bước 2/4: Đang tạo ảnh thẻ bài Threads & bản quyền...")
                elif "[3/5]" in line:
                    self.after(0, self._update_step, 65, "🎙️ Bước 3/4: Đang tạo giọng đọc AI & chèn âm thanh...")
                elif "[4/5]" in line:
                    self.after(0, self._update_step, 85, "🎬 Bước 4/4: Đang ghép video TikTok & nhạc nền...")
                elif "Cảnh " in line and "hoàn thành" in line:
                    m = re.search(r"Cảnh (\d+)/(\d+)", line)
                    if m:
                        c, t = int(m.group(1)), int(m.group(2))
                        p = 40 + int((c / max(1, t)) * 40)
                        self.after(0, self._update_step, p, f"🎙️ Bước 3/4: Đang ghép cảnh {c}/{t}...")

                if "Đường dẫn video:" in line:
                    m = re.search(r"Đường dẫn video:\s*(.+?)(?:\s*\(\d+.*s\))?$", line.strip())
                    if m:
                        video_out = Path(m.group(1).strip())

                if "Tiêu đề TikTok:" in line:
                    capturing_title = True
                    continue
                if capturing_title:
                    extracted_title += line

            self.process.stdout.close()
            code = self.process.wait()
            success = (code == 0 and video_out and video_out.exists())
            self.after(0, self._finish_task, success, video_out, extracted_title.strip())

        except Exception as e:
            self.after(0, self._log, f"\n[Lỗi hệ thống] {e}\n")
            self.after(0, self._finish_task, False, None, "")

    def _update_step(self, progress: float, text: str):
        self.prog_var.set(progress)
        self.status_lbl.config(text=text, fg="#38bdf8")

    def _finish_task(self, success: bool, video_path: Path | None, title: str):
        self.is_running = False
        self.process = None
        self.action_btn.config(state="normal", text="🚀 TẠO VIDEO NGAY", bg="#2563eb")

        if success and video_path:
            self.current_video_path = video_path
            self.tiktok_title = title
            self.prog_var.set(100)
            self.status_lbl.config(text=f"🎉 Tạo video thành công! ({video_path.name})", fg=self.c_success)
            self.success_box.pack(fill="x", pady=(8, 0))
            self._open_video()
        else:
            self.prog_var.set(0)
            self.status_lbl.config(text="❌ Không thể tạo video. Vui lòng bấm Chi tiết để xem lỗi.", fg=self.c_error)
            self.error_box.pack(fill="x", pady=(8, 0))

    def _open_video(self):
        if self.current_video_path and self.current_video_path.exists():
            try:
                os.startfile(str(self.current_video_path.resolve()))
            except Exception:
                pass

    def _open_dir(self):
        if self.current_video_path and self.current_video_path.exists():
            folder = self.current_video_path.parent
            try:
                os.startfile(str(folder.resolve()))
            except Exception:
                pass

    def _copy_title(self):
        if self.tiktok_title:
            self.clipboard_clear()
            self.clipboard_append(self.tiktok_title)
            messagebox.showinfo("Đã sao chép", "Đã sao chép tiêu đề & hashtag TikTok vào bộ nhớ tạm!")

    def _copy_error(self):
        err_text = "".join(self.log_buffer)
        if not err_text.strip():
            err_text = "Không ghi nhận được log lỗi chi tiết."
        self.clipboard_clear()
        self.clipboard_append(err_text)
        messagebox.showinfo("Đã sao chép", "Đã sao chép toàn bộ mã lỗi! Bạn có thể dán gửi cho hỗ trợ.")


def main():
    try:
        app = ThreadClipApp()
        app.mainloop()
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Lỗi khởi động ThreadClip",
                f"Đã xảy ra sự cố khi mở ứng dụng:\n\n{e}\n\nVui lòng chụp màn hình hoặc gửi mã lỗi để được hỗ trợ."
            )
            root.destroy()
        except Exception:
            print(f"[Lỗi khởi động ThreadClip]\n{tb}")


if __name__ == "__main__":
    main()
