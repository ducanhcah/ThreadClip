"""Giao diện đồ họa (GUI) cao cấp cho threads2video Studio.

Thiết kế tối ưu:
  - Bảng màu High-Contrast hiện đại, các ô nhập liệu đồng bộ nền tối, chữ rõ nét.
  - Sắp xếp logic theo các khối rõ ràng: Nguồn dữ liệu -> Cấu hình Video/Giọng đọc/Âm thanh -> Nâng cao.
  - Tự động mở video sau khi tạo xong, hiển thị Live Terminal Logs.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText

ROOT = Path(__file__).resolve().parent
PYTHON_EXE = sys.executable


class HelpDialog(tk.Toplevel):
    def __init__(self, parent: tk.Tk):
        super().__init__(parent)
        self.title("📖 Hướng dẫn sử dụng - threads2video_ducanhcah")
        self.geometry("780x680")
        self.minsize(680, 520)
        self.configure(bg="#141517")
        self.transient(parent)
        self.grab_set()

        # Căn giữa cửa sổ theo ứng dụng chính
        try:
            x = parent.winfo_x() + (parent.winfo_width() - 780) // 2
            y = parent.winfo_y() + (parent.winfo_height() - 680) // 2
            self.geometry(f"+{max(0, x)}+{max(0, y)}")
        except Exception:
            pass

        self._build_ui()

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg="#0d0e11", pady=12, padx=16)
        hdr.pack(fill="x")
        tk.Label(hdr, text="📖 HƯỚNG DẪN SỬ DỤNG threads2video_ducanhcah",
                 font=("Segoe UI", 13, "bold"), bg="#0d0e11", fg="#38bdf8").pack(anchor="w")
        tk.Label(hdr, text="Tài liệu tóm tắt thao tác, cấu hình và tính năng tự động thông minh",
                 font=("Segoe UI", 9), bg="#0d0e11", fg="#94a3b8").pack(anchor="w")

        # Khung văn bản cuộn
        body = tk.Frame(self, bg="#141517", padx=14, pady=10)
        body.pack(fill="both", expand=True)

        txt = ScrolledText(body, bg="#1e2124", fg="#f1f5f9", font=("Segoe UI", 10),
                           wrap="word", relief="solid", bd=1, padx=12, pady=12)
        txt.pack(fill="both", expand=True)

        # Định dạng thẻ màu sắc
        txt.tag_config("h1", font=("Segoe UI", 12, "bold"), foreground="#38bdf8", spacing3=6, spacing1=10)
        txt.tag_config("bullet", font=("Segoe UI", 10), foreground="#e2e8f0", lmargin1=16, lmargin2=32)

        help_content = [
            ("h1", "1. CÁCH TẠO VIDEO NHANH (3 BƯỚC)"),
            ("bullet", "• Bước 1: Sao chép liên kết bài viết Threads bất kỳ (ví dụ: https://www.threads.com/@user/post/...)."),
            ("bullet", "• Bước 2: Bấm nút '📋 Dán link' trên giao diện. Chọn video nền (Subway Surfers, Minecraft...) và nhạc nền TikTok nếu thích."),
            ("bullet", "• Bước 3: Bấm nút '🚀 BẮT ĐẦU TẠO VIDEO'. Chờ tiến trình chạy xong, video hoàn thành sẽ tự động mở!"),

            ("h1", "2. TÍNH NĂNG ÂM THANH & MEME SFX"),
            ("bullet", "• Meme SFX viral TikTok: Tự động phân tích ngữ cảnh (hài hước, sốc, bất ngờ) để chèn đúng sound effect (pop, ting, bruh, gasp, wow...)."),
            ("bullet", "• Âm lượng SFX: Thanh trượt cho phép chỉnh âm lượng hiệu ứng âm thanh từ 5% đến 100% (mặc định 35%)."),
            ("bullet", "• Nhạc nền TikTok: Tự động lặp (loop) và hạ âm lượng (ducking) xuống 12% để tôn giọng đọc AI rõ ràng, không bị chói."),

            ("h1", "3. HỆ THỐNG GIỌNG ĐỌC AI (100% MIỄN PHÍ)"),
            ("bullet", "• Tự động (Nam/Nữ theo bài): Nhận diện giới tính người đăng dựa theo tên tài khoản hoặc các từ xưng hô trong bài. Bình luận của người khác sẽ tự động xen kẽ giọng để người xem dễ phân biệt người nói."),
            ("bullet", "• Tùy chỉnh tốc độ đọc linh hoạt: Hỗ trợ từ chậm rãi tâm sự (0.85x, 0.9x) đến tốc độ nhanh cuốn hút (1.1x, 1.15x, 1.2x, 1.25x) phù hợp với từng thể loại nội dung hài hước, drama hay kể chuyện."),
            ("bullet", "• Chuẩn hóa từ viết tắt & Teencode: Tự động dịch teencode Gen Z (ko -> không, dc -> được, vl -> rất, cmt -> bình luận, bthg -> bình thường, iu -> yêu, cx -> cũng...) giúp giọng đọc tự nhiên 100% tiếng Việt."),

            ("h1", "4. BỘ LỌC BÌNH LUẬN THÔNG MINH"),
            ("bullet", "• Tự động loại bỏ link ngoài: Link Shopee, Lazada, TikTok Shop, bio, nhóm Telegram, Zalo... bị xóa tự động để tránh dính bản quyền và vi phạm chính sách kiểm duyệt của TikTok."),
            ("bullet", "• Lọc spam cờ bạc, tuyển CTV: Tự loại bỏ các bình luận spam lừa đảo 'việc nhẹ lương cao', 'tài xỉu', 'nhận tiền thưởng'."),

            ("h1", "5. BẢN QUYỀN KÊNH & KÊU GỌI FOLLOW/TIM/CMT"),
            ("bullet", "• Bản quyền kênh (Watermark): Đóng dấu tên kênh ở vị trí chuẩn TikTok (mặc định: ngay phía trên thẻ bài viết lệch trái). Có thể tùy chọn đổi sang góc phải, ở giữa hoặc các góc màn hình."),
            ("bullet", "• Kêu gọi tương tác ở cuối video (Outro): Tự động chèn cảnh thẻ Outro bắt mắt kèm lời đọc AI nhắc người xem Follow kênh, Thả Tim và Bình luận."),

            ("h1", "6. TÙY CHỌN NÂNG CAO"),
            ("bullet", "• Giới hạn ký tự bình luận (--max-chars): Bỏ qua bình luận quá dài (mặc định 300 ký tự) để video ngắn gọn, giữ chân người xem."),
            ("bullet", "• Giữ phản hồi của tác giả: Mặc định lọc bỏ trả lời của chính tác giả để video tập trung vào ý kiến cộng đồng. Tích chọn nếu muốn giữ lại."),
            ("bullet", "• Phiên đăng nhập Threads (--storage-state): Dành cho trường hợp Threads bắt đăng nhập để xem nội dung.")
        ]

        for tag, line in help_content:
            txt.insert("end", line + "\n", tag)

        txt.config(state="disabled")

        # Footer
        ftr = tk.Frame(self, bg="#0d0e11", pady=10, padx=16)
        ftr.pack(fill="x")

        open_readme_btn = tk.Button(ftr, text="📄 Mở tài liệu chi tiết (README.md)",
                                    font=("Segoe UI", 9, "bold"), bg="#2563eb", fg="#ffffff",
                                    activebackground="#1d4ed8", activeforeground="#ffffff",
                                    relief="solid", bd=1, padx=12, pady=5, cursor="hand2",
                                    command=self._open_readme)
        open_readme_btn.pack(side="left")

        close_btn = tk.Button(ftr, text="Đóng", font=("Segoe UI", 9),
                              bg="#2d323b", fg="#e2e8f0", activebackground="#3f4654",
                              activeforeground="#ffffff", relief="solid", bd=1, padx=16, pady=5,
                              cursor="hand2", command=self.destroy)
        close_btn.pack(side="right")

    def _open_readme(self):
        readme_path = ROOT / "README.md"
        if readme_path.exists():
            try:
                if os.name == "nt":
                    os.startfile(str(readme_path.resolve()))
                elif sys.platform == "darwin":
                    subprocess.run(["open", str(readme_path.resolve())])
                else:
                    subprocess.run(["xdg-open", str(readme_path.resolve())])
            except Exception as e:
                messagebox.showerror("Lỗi mở file", str(e), parent=self)
        else:
            messagebox.showwarning("Không tìm thấy", "File README.md không tồn tại!", parent=self)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("threads2video_ducanhcah - Tạo Video TikTok Từ Threads")
        self.geometry("980x920")
        self.minsize(900, 780)
        self.configure(bg="#141517")

        self.process: subprocess.Popen | None = None
        self.is_running = False
        self.current_video_path: Path | None = None
        self.tiktok_title: str = ""
        self.adv_expanded = False

        self._setup_styles()
        self._build_ui()
        self._refresh_assets()

    def _setup_styles(self):
        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        bg_main = "#141517"
        bg_card = "#1e2124"
        bg_input = "#121316"
        fg_white = "#ffffff"
        fg_sub = "#cbd5e1"
        accent_blue = "#2563eb"
        border_col = "#333740"

        self.style.configure(".", background=bg_main, foreground=fg_white, font=("Segoe UI", 10))
        self.style.configure("TLabelframe", background=bg_card, relief="solid", borderwidth=1,
                             bordercolor=border_col)
        self.style.configure("TLabelframe.Label", background=bg_card, foreground="#38bdf8",
                             font=("Segoe UI", 10, "bold"))
        self.style.configure("TLabel", background=bg_card, foreground=fg_white, font=("Segoe UI", 9))
        self.style.configure("TCheckbutton", background=bg_card, foreground=fg_white,
                             font=("Segoe UI", 9, "bold"))
        self.style.configure("TRadiobutton", background=bg_card, foreground=fg_white,
                             font=("Segoe UI", 9))
        self.style.map("TCheckbutton", foreground=[("active", "#38bdf8")])
        self.style.map("TRadiobutton", foreground=[("active", "#38bdf8")])

        # Combobox tương phản cao
        self.style.configure("TCombobox", fieldbackground=bg_input, background="#2b2f38",
                             foreground=fg_white, bordercolor=border_col, arrowcolor="#ffffff",
                             padding=4)
        self.style.map("TCombobox",
                       fieldbackground=[("readonly", bg_input), ("disabled", "#17181c")],
                       foreground=[("readonly", fg_white), ("disabled", "#64748b")],
                       selectbackground=[("readonly", accent_blue)],
                       selectforeground=[("readonly", fg_white)])

        self.option_add("*TCombobox*Listbox.background", "#1c1e22")
        self.option_add("*TCombobox*Listbox.foreground", "#ffffff")
        self.option_add("*TCombobox*Listbox.selectBackground", accent_blue)
        self.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")
        self.option_add("*TCombobox*Listbox.font", ("Segoe UI", 9))

        # Nút bấm ttk
        self.style.configure("Primary.TButton", font=("Segoe UI", 11, "bold"),
                             background="#16a34a", foreground="#ffffff", padding=8)
        self.style.map("Primary.TButton",
                       background=[("active", "#22c55e"), ("disabled", "#272a30")],
                       foreground=[("disabled", "#64748b")])

        self.style.configure("Danger.TButton", font=("Segoe UI", 10, "bold"),
                             background="#dc2626", foreground="#ffffff", padding=7)
        self.style.map("Danger.TButton",
                       background=[("active", "#ef4444"), ("disabled", "#272a30")],
                       foreground=[("disabled", "#64748b")])

        self.style.configure("Secondary.TButton", font=("Segoe UI", 9),
                             background="#2d323b", foreground="#e2e8f0", padding=4)
        self.style.map("Secondary.TButton",
                       background=[("active", "#3f4654"), ("disabled", "#1a1c20")],
                       foreground=[("disabled", "#64748b")])

        self.style.configure("Green.Horizontal.TProgressbar",
                             troughcolor="#121316", background="#10b981", bordercolor="#333740")

    def _build_ui(self):
        # ── Header ───────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg="#0d0e11", pady=10, padx=18)
        hdr.pack(fill="x")

        hdr_left = tk.Frame(hdr, bg="#0d0e11")
        hdr_left.pack(side="left")

        title_lbl = tk.Label(hdr_left, text="🎬 threads2video_ducanhcah", font=("Segoe UI", 15, "bold"),
                             bg="#0d0e11", fg="#38bdf8")
        title_lbl.pack(anchor="w")
        sub_lbl = tk.Label(hdr_left, text="Tự động tạo video TikTok 9:16: Giọng đọc AI tiếng Việt, Video nền chuyển động & Meme SFX",
                           font=("Segoe UI", 9), bg="#0d0e11", fg="#94a3b8")
        sub_lbl.pack(anchor="w")

        hdr_right = tk.Frame(hdr, bg="#0d0e11")
        hdr_right.pack(side="right", padx=(10, 0))

        help_btn = tk.Button(hdr_right, text="📖 Hướng dẫn sử dụng", font=("Segoe UI", 10, "bold"),
                             bg="#1e293b", fg="#38bdf8", activebackground="#334155",
                             activeforeground="#ffffff", relief="solid", bd=1, padx=12, pady=6,
                             cursor="hand2", command=self._open_help_dialog)
        help_btn.pack(side="right")

        # Footer thanh bản quyền góc dưới
        ftr_bar = tk.Frame(self, bg="#0d0e11", pady=3, padx=16)
        ftr_bar.pack(fill="x", side="bottom")
        tk.Label(ftr_bar, text="threads2video_ducanhcah Studio • Bản quyền thuộc về ducanhcah",
                 font=("Segoe UI", 8), bg="#0d0e11", fg="#64748b").pack(side="right")

        # Container chính cuộn hoặc padding
        main = tk.Frame(self, bg="#141517", padx=14, pady=6)
        main.pack(fill="both", expand=True)

        # ── KHỐI 1: Nguồn dữ liệu ──────────────────────────────────────────────
        src_box = ttk.LabelFrame(main, text=" 🔗 Link bài viết Threads ", padding=8)
        src_box.pack(fill="x", pady=(0, 6))

        # Dòng: Link URL
        r_url = tk.Frame(src_box, bg="#1e2124")
        r_url.pack(fill="x")

        tk.Label(r_url, text="Link Threads:", font=("Segoe UI", 9, "bold"),
                 bg="#1e2124", fg="#ffffff", width=12, anchor="w").pack(side="left")
        self.url_var = tk.StringVar()
        self.url_entry = tk.Entry(r_url, textvariable=self.url_var, font=("Segoe UI", 10),
                                  bg="#121316", fg="#ffffff", insertbackground="#38bdf8",
                                  relief="solid", bd=1)
        self.url_entry.pack(side="left", fill="x", expand=True, ipady=3, padx=(0, 6))

        paste_btn = ttk.Button(r_url, text="📋 Dán link", style="Secondary.TButton",
                               command=self._paste_clipboard)
        paste_btn.pack(side="right")

        # ── KHỐI 2: Tùy chọn Video & Giọng đọc ──────────────────────────────────
        opts_box = ttk.LabelFrame(main, text=" ⚙️ Tùy chọn Video & Giọng đọc ", padding=8)
        opts_box.pack(fill="x", pady=(0, 6))

        # Dòng 1: Số cmt + Dark Mode + Giọng đọc AI + Dọn dẹp
        row1 = tk.Frame(opts_box, bg="#1e2124")
        row1.pack(fill="x", pady=(0, 6))

        tk.Label(row1, text="Số bình luận:", font=("Segoe UI", 9), bg="#1e2124", fg="#ffffff").pack(side="left", padx=(0, 4))
        self.top_var = tk.StringVar(value="5")
        top_cb = ttk.Combobox(row1, textvariable=self.top_var, values=["3", "5", "7", "10", "15"],
                              width=4, state="readonly")
        top_cb.pack(side="left", padx=(0, 14))

        self.dark_var = tk.BooleanVar(value=True)
        dark_chk = ttk.Checkbutton(row1, text="Dark Mode", variable=self.dark_var)
        dark_chk.pack(side="left", padx=(0, 14))

        tk.Label(row1, text="Giọng đọc AI:", font=("Segoe UI", 9), bg="#1e2124", fg="#ffffff").pack(side="left", padx=(0, 4))
        self.voice_var = tk.StringVar(value="Tự động (Nam/Nữ theo bài)")
        voice_cb = ttk.Combobox(row1, textvariable=self.voice_var,
                                values=[
                                    "Tự động (Nam/Nữ theo bài)",
                                    "Nam chuẩn (vi-VN-NamMinhNeural)",
                                    "Nữ chuẩn (vi-VN-HoaiMyNeural)",
                                ],
                                width=24, state="readonly")
        voice_cb.pack(side="left", padx=(0, 12))

        tk.Label(row1, text="Tốc độ:", font=("Segoe UI", 9, "bold"), bg="#1e2124", fg="#38bdf8").pack(side="left", padx=(0, 4))
        self.rate_var = tk.StringVar(value="1.0x (Bình thường)")
        rate_cb = ttk.Combobox(row1, textvariable=self.rate_var,
                               values=[
                                   "1.0x (Bình thường)",
                                   "1.1x (Hơi nhanh - Cuốn)",
                                   "1.15x (Chuẩn TikTok viral)",
                                   "1.2x (Nhanh)",
                                   "1.25x (Rất nhanh)",
                                   "0.9x (Chậm rãi, tâm sự)",
                                   "0.85x (Chậm)",
                               ],
                               width=18, state="readonly")
        rate_cb.pack(side="left", padx=(0, 14))

        self.clean_var = tk.BooleanVar(value=True)
        clean_chk = ttk.Checkbutton(row1, text="Tự dọn dẹp work/", variable=self.clean_var)
        clean_chk.pack(side="left")

        # Phân cách
        tk.Frame(opts_box, height=1, bg="#2d323b").pack(fill="x", pady=4)

        # Dòng 2: Video nền (Bố cục grid đồng đều, dễ nhìn)
        row_bg = tk.Frame(opts_box, bg="#1e2124")
        row_bg.pack(fill="x", pady=(2, 4))

        tk.Label(row_bg, text="Video nền:", font=("Segoe UI", 9, "bold"),
                 bg="#1e2124", fg="#38bdf8", width=10, anchor="w").pack(side="left")

        self.bg_mode_var = tk.StringVar(value="preset")
        rb_preset = ttk.Radiobutton(row_bg, text="Có sẵn:", variable=self.bg_mode_var,
                                    value="preset", command=self._on_bg_mode_change)
        rb_preset.pack(side="left", padx=(0, 4))

        self.bg_preset_var = tk.StringVar(value="[Ngẫu nhiên]")
        self.bg_preset_cb = ttk.Combobox(row_bg, textvariable=self.bg_preset_var,
                                         width=28, state="readonly")
        self.bg_preset_cb.pack(side="left", padx=(0, 14))

        rb_none = ttk.Radiobutton(row_bg, text="Không dùng video nền (ảnh tĩnh)",
                                  variable=self.bg_mode_var, value="none",
                                  command=self._on_bg_mode_change)
        rb_none.pack(side="left")

        # Dòng 2.2: Tự thêm MP4
        row_custom_bg = tk.Frame(opts_box, bg="#1e2124")
        row_custom_bg.pack(fill="x", pady=(2, 4))

        tk.Label(row_custom_bg, text="", width=10).pack(side="left")  # Căn lề
        rb_custom = ttk.Radiobutton(row_custom_bg, text="Tự chọn file MP4:",
                                    variable=self.bg_mode_var, value="custom",
                                    command=self._on_bg_mode_change)
        rb_custom.pack(side="left", padx=(0, 4))

        self.custom_bg_var = tk.StringVar()
        self.custom_bg_entry = tk.Entry(row_custom_bg, textvariable=self.custom_bg_var,
                                        font=("Segoe UI", 9), bg="#121316", fg="#ffffff",
                                        disabledbackground="#17181c", disabledforeground="#555d6b",
                                        relief="solid", bd=1, state="disabled", width=34)
        self.custom_bg_entry.pack(side="left", padx=(0, 6), ipady=2)

        self.browse_bg_btn = ttk.Button(row_custom_bg, text="📁 Chọn file...",
                                        style="Secondary.TButton",
                                        command=self._browse_custom_video, state="disabled")
        self.browse_bg_btn.pack(side="left")

        # Phân cách
        tk.Frame(opts_box, height=1, bg="#2d323b").pack(fill="x", pady=4)

        # Dòng 3.1: Meme SFX & Âm lượng SFX
        row_sfx = tk.Frame(opts_box, bg="#1e2124")
        row_sfx.pack(fill="x", pady=(2, 3))

        self.sfx_var = tk.BooleanVar(value=True)
        self.sfx_chk = ttk.Checkbutton(row_sfx, text="Meme SFX viral TikTok (24 âm thanh):",
                                       variable=self.sfx_var, command=self._on_sfx_toggle)
        self.sfx_chk.pack(side="left", padx=(0, 8))

        self.sfx_vol_lbl = tk.Label(row_sfx, text="Âm lượng: 35%", font=("Segoe UI", 9),
                                    bg="#1e2124", fg="#38bdf8", width=13, anchor="w")
        self.sfx_vol_lbl.pack(side="left")

        self.sfx_vol_scale = tk.Scale(row_sfx, from_=5, to=100, orient="horizontal",
                                      showvalue=0, command=self._on_sfx_vol_change,
                                      bg="#1e2124", fg="#38bdf8", troughcolor="#121316",
                                      activebackground="#10b981", highlightthickness=0,
                                      bd=0, length=120)
        self.sfx_vol_scale.set(35)
        self.sfx_vol_scale.pack(side="left")

        # Dòng 3.2: Nhạc nền TikTok & Âm lượng Nhạc
        row_sound = tk.Frame(opts_box, bg="#1e2124")
        row_sound.pack(fill="x", pady=(2, 2))

        self.music_var = tk.BooleanVar(value=False)
        music_chk = ttk.Checkbutton(row_sound, text="Bật nhạc nền TikTok:", variable=self.music_var,
                                    command=self._on_music_toggle)
        music_chk.pack(side="left", padx=(0, 6))

        self.music_choice_var = tk.StringVar(value="[Ngẫu nhiên]")
        self.music_cb = ttk.Combobox(row_sound, textvariable=self.music_choice_var,
                                     width=26, state="disabled")
        self.music_cb.pack(side="left", padx=(0, 10))

        self.vol_lbl = tk.Label(row_sound, text="Âm lượng: 12%", font=("Segoe UI", 9),
                                bg="#1e2124", fg="#38bdf8", width=13, anchor="w")
        self.vol_lbl.pack(side="left")

        # Custom Slider thẩm mỹ
        self.music_vol_scale = tk.Scale(row_sound, from_=5, to=50, orient="horizontal",
                                        showvalue=0, command=self._on_vol_change,
                                        bg="#1e2124", fg="#38bdf8", troughcolor="#121316",
                                        activebackground="#10b981", highlightthickness=0,
                                        bd=0, length=120)
        self.music_vol_scale.set(12)
        self.music_vol_scale.config(state="disabled")
        self.music_vol_scale.pack(side="left")

        # Phân cách
        tk.Frame(opts_box, height=1, bg="#2d323b").pack(fill="x", pady=4)

        # Dòng 4: Bản quyền kênh (Watermark) & Kêu gọi Follow/Tim/Cmt (Outro)
        row_wm = tk.Frame(opts_box, bg="#1e2124")
        row_wm.pack(fill="x", pady=(2, 2))

        self.watermark_var = tk.BooleanVar(value=False)
        self.watermark_chk = ttk.Checkbutton(row_wm, text="Bản quyền kênh (Watermark):",
                                             variable=self.watermark_var,
                                             command=self._on_watermark_toggle)
        self.watermark_chk.pack(side="left", padx=(0, 6))

        self.watermark_text_var = tk.StringVar(value="@ducanhcah")
        self.watermark_entry = tk.Entry(row_wm, textvariable=self.watermark_text_var,
                                        font=("Segoe UI", 9), bg="#121316", fg="#ffffff",
                                        disabledbackground="#17181c", disabledforeground="#555d6b",
                                        relief="solid", bd=1, state="disabled", width=18)
        self.watermark_entry.pack(side="left", padx=(0, 10), ipady=2)

        tk.Label(row_wm, text="Vị trí:", font=("Segoe UI", 9), bg="#1e2124", fg="#ffffff").pack(side="left", padx=(0, 4))
        self.watermark_pos_var = tk.StringVar(value="Phía trên thẻ - Góc trái (Khuyên dùng)")
        self.watermark_pos_cb = ttk.Combobox(row_wm, textvariable=self.watermark_pos_var,
                                             values=[
                                                 "Phía trên thẻ - Góc trái (Khuyên dùng)",
                                                 "Phía trên thẻ - Góc phải",
                                                 "Phía trên thẻ - Ở giữa",
                                                 "Góc trên cùng bên phải màn hình",
                                                 "Góc trên cùng bên trái màn hình",
                                                 "Góc dưới cùng bên trái màn hình",
                                                 "Góc dưới cùng bên phải màn hình",
                                             ],
                                             width=32, state="disabled")
        self.watermark_pos_cb.pack(side="left", padx=(0, 14))

        self.outro_var = tk.BooleanVar(value=True)
        self.outro_chk = ttk.Checkbutton(row_wm, text="Hiện Follow, Tim & Cmt ở cuối video",
                                         variable=self.outro_var)
        self.outro_chk.pack(side="left")

        # ── KHỐI 3: Tùy chọn nâng cao (Ẩn/Hiện) ────────────────────────────────
        adv_bar = tk.Frame(main, bg="#141517")
        adv_bar.pack(fill="x", pady=(2, 4))

        self.adv_btn = tk.Button(adv_bar, text="▶ Mở rộng tùy chọn nâng cao (Độ dài cmt, Session Threads, Test nhanh...)",
                                 font=("Segoe UI", 9), bg="#1e2124", fg="#94a3b8",
                                 activebackground="#2a2e35", activeforeground="#ffffff",
                                 relief="solid", bd=1, padx=8, pady=4, cursor="hand2",
                                 command=self._toggle_advanced)
        self.adv_btn.pack(side="left")

        self.adv_frame = tk.Frame(main, bg="#181a1d", padx=10, pady=8, relief="solid", bd=1)
        # Được pack khi bấm nút mở rộng

        # Advanced Row 1: Max chars + Author replies + Show browser + Mock TTS
        ar1 = tk.Frame(self.adv_frame, bg="#181a1d")
        ar1.pack(fill="x", pady=(0, 4))

        tk.Label(ar1, text="Giới hạn ký tự bình luận (--max-chars):", font=("Segoe UI", 9),
                 bg="#181a1d", fg="#cbd5e1").pack(side="left", padx=(0, 4))
        self.max_chars_var = tk.StringVar(value="300")
        max_cb = ttk.Combobox(ar1, textvariable=self.max_chars_var,
                              values=["150", "200", "250", "300", "400", "500", "800"],
                              width=5, state="readonly")
        max_cb.pack(side="left", padx=(0, 14))

        self.author_replies_var = tk.BooleanVar(value=False)
        auth_chk = ttk.Checkbutton(ar1, text="Giữ phản hồi của tác giả (--include-author-replies)",
                                   variable=self.author_replies_var)
        auth_chk.pack(side="left", padx=(0, 14))

        self.show_browser_var = tk.BooleanVar(value=False)
        browser_chk = ttk.Checkbutton(ar1, text="Hiện trình duyệt (--show-browser)",
                                      variable=self.show_browser_var)
        browser_chk.pack(side="left", padx=(0, 14))

        self.mock_tts_var = tk.BooleanVar(value=False)
        mock_chk = ttk.Checkbutton(ar1, text="Test nhanh (--mock-tts)",
                                   variable=self.mock_tts_var)
        mock_chk.pack(side="left")

        # Advanced Row 2: Session Threads (state.json)
        ar2 = tk.Frame(self.adv_frame, bg="#181a1d")
        ar2.pack(fill="x", pady=(4, 0))

        tk.Label(ar2, text="Phiên đăng nhập Threads (--storage-state):", font=("Segoe UI", 9),
                 bg="#181a1d", fg="#cbd5e1").pack(side="left", padx=(0, 6))
        self.storage_state_var = tk.StringVar()
        self.storage_entry = tk.Entry(ar2, textvariable=self.storage_state_var, font=("Segoe UI", 9),
                                      bg="#121316", fg="#94a3b8", relief="solid", bd=1)
        self.storage_entry.pack(side="left", fill="x", expand=True, ipady=2, padx=(0, 6))

        browse_state_btn = ttk.Button(ar2, text="📁 Chọn state.json...", style="Secondary.TButton",
                                      command=self._browse_storage_state)
        browse_state_btn.pack(side="left", padx=(0, 4))

        clear_state_btn = ttk.Button(ar2, text="✖", style="Secondary.TButton",
                                     command=lambda: self.storage_state_var.set(""))
        clear_state_btn.pack(side="left")

        # ── KHỐI 4: Nút bấm & Thanh tiến trình ─────────────────────────────────
        act_box = tk.Frame(main, bg="#141517")
        act_box.pack(fill="x", pady=(4, 6))

        self.run_btn = ttk.Button(act_box, text="🚀 BẮT ĐẦU TẠO VIDEO", style="Primary.TButton",
                                  command=self._start_task)
        self.run_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.stop_btn = ttk.Button(act_box, text="⏹ Dừng", style="Danger.TButton",
                                   command=self._stop_task, state="disabled")
        self.stop_btn.pack(side="right")

        # Thanh tiến trình
        prog_row = tk.Frame(main, bg="#141517")
        prog_row.pack(fill="x", pady=(0, 4))

        self.prog_var = tk.DoubleVar(value=0)
        self.prog_bar = ttk.Progressbar(prog_row, variable=self.prog_var, maximum=100,
                                        style="Green.Horizontal.TProgressbar")
        self.prog_bar.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.status_lbl = tk.Label(prog_row, text="Sẵn sàng", font=("Segoe UI", 9, "bold"),
                                   bg="#141517", fg="#38bdf8", width=30, anchor="e")
        self.status_lbl.pack(side="right")

        # ── KHỐI 5: Live Terminal Logs ─────────────────────────────────────────
        term_box = ttk.LabelFrame(main, text=" 🖥️ Tiến trình & Nhật ký (Live Terminal Logs) ", padding=4)
        term_box.pack(fill="both", expand=True, pady=(0, 4))

        self.log_text = ScrolledText(term_box, bg="#0d0e11", fg="#e2e8f0",
                                     insertbackground="#38bdf8", font=("Consolas", 10),
                                     relief="flat", wrap="word")
        self.log_text.pack(fill="both", expand=True)

        self.log_text.tag_config("info", foreground="#94a3b8")
        self.log_text.tag_config("step", foreground="#38bdf8", font=("Consolas", 10, "bold"))
        self.log_text.tag_config("success", foreground="#34d399", font=("Consolas", 10, "bold"))
        self.log_text.tag_config("warning", foreground="#fbbf24")
        self.log_text.tag_config("error", foreground="#f87171", font=("Consolas", 10, "bold"))
        self.log_text.tag_config("sfx", foreground="#fde047", font=("Consolas", 10, "bold"))

        # ── KHỐI 6: Kết quả Video ──────────────────────────────────────────────
        res_box = ttk.LabelFrame(main, text=" 🎯 Kết quả Video ", padding=6)
        res_box.pack(fill="x")

        res_row = tk.Frame(res_box, bg="#1e2124")
        res_row.pack(fill="x")

        self.res_path_var = tk.StringVar(value="Chưa có video được tạo")
        self.res_path_lbl = tk.Entry(res_row, textvariable=self.res_path_var, font=("Segoe UI", 9),
                                     bg="#121316", fg="#64748b", relief="solid", bd=1,
                                     state="readonly")
        self.res_path_lbl.pack(side="left", fill="x", expand=True, padx=(0, 8), ipady=3)

        self.open_vid_btn = ttk.Button(res_row, text="▶ Mở video", style="Secondary.TButton",
                                       command=self._open_current_video, state="disabled")
        self.open_vid_btn.pack(side="left", padx=(0, 6))

        self.open_dir_btn = ttk.Button(res_row, text="📁 Mở thư mục", style="Secondary.TButton",
                                       command=self._open_current_dir, state="disabled")
        self.open_dir_btn.pack(side="left", padx=(0, 6))

        self.copy_title_btn = ttk.Button(res_row, text="📋 Sao chép tiêu đề", style="Secondary.TButton",
                                         command=self._copy_tiktok_title, state="disabled")
        self.copy_title_btn.pack(side="left")

    # ── Refresh & Populate Assets ─────────────────────────────────────────────

    def _refresh_assets(self):
        v_dir = ROOT / "assets" / "video"
        v_files = ["[Ngẫu nhiên]"]
        if v_dir.exists():
            for p in sorted(v_dir.glob("*.mp4")):
                v_files.append(p.name)
        self.bg_preset_cb["values"] = v_files
        self.bg_preset_var.set(v_files[0])

        m_dir = ROOT / "assets" / "music"
        m_files = ["[Ngẫu nhiên]"]
        if m_dir.exists():
            for p in sorted(m_dir.glob("*.mp3")):
                m_files.append(p.name)
        self.music_cb["values"] = m_files
        self.music_choice_var.set(m_files[0])

    # ── Event Handlers ────────────────────────────────────────────────────────

    def _paste_clipboard(self):
        try:
            txt = self.clipboard_get().strip()
            if txt:
                self.url_var.set(txt)
        except Exception:
            pass

    def _on_sfx_toggle(self):
        if self.sfx_var.get():
            self.sfx_vol_scale.config(state="normal")
        else:
            self.sfx_vol_scale.config(state="disabled")

    def _on_sfx_vol_change(self, val):
        self.sfx_vol_lbl.config(text=f"Âm lượng: {int(float(val))}%")

    def _browse_storage_state(self):
        p = filedialog.askopenfilename(
            title="Chọn file session (state.json)",
            filetypes=[("File JSON", "*.json"), ("Tất cả file", "*.*")]
        )
        if p:
            self.storage_state_var.set(p)

    def _toggle_advanced(self):
        if self.adv_expanded:
            self.adv_frame.pack_forget()
            self.adv_btn.config(text="▶ Mở rộng tùy chọn nâng cao (Độ dài cmt, Session Threads, Test nhanh...)")
            self.adv_expanded = False
        else:
            self.adv_frame.pack(fill="x", pady=(2, 4), after=self.adv_btn.master)
            self.adv_btn.config(text="▲ Thu gọn tùy chọn nâng cao")
            self.adv_expanded = True

    def _on_bg_mode_change(self):
        mode = self.bg_mode_var.get()
        if mode == "preset":
            self.bg_preset_cb.config(state="readonly")
            self.custom_bg_entry.config(state="disabled")
            self.browse_bg_btn.config(state="disabled")
        elif mode == "custom":
            self.bg_preset_cb.config(state="disabled")
            self.custom_bg_entry.config(state="normal")
            self.browse_bg_btn.config(state="normal")
        else:
            self.bg_preset_cb.config(state="disabled")
            self.custom_bg_entry.config(state="disabled")
            self.browse_bg_btn.config(state="disabled")

    def _on_music_toggle(self):
        if self.music_var.get():
            self.music_cb.config(state="readonly")
            self.music_vol_scale.config(state="normal")
        else:
            self.music_cb.config(state="disabled")
            self.music_vol_scale.config(state="disabled")

    def _on_watermark_toggle(self):
        if self.watermark_var.get():
            self.watermark_entry.config(state="normal")
            self.watermark_pos_cb.config(state="readonly")
        else:
            self.watermark_entry.config(state="disabled")
            self.watermark_pos_cb.config(state="disabled")

    def _on_vol_change(self, val):
        self.vol_lbl.config(text=f"Âm lượng: {int(float(val))}%")

    def _browse_custom_video(self):
        p = filedialog.askopenfilename(
            title="Chọn file video nền MP4",
            filetypes=[("Video MP4", "*.mp4"), ("Tất cả video", "*.mp4;*.webm;*.mov;*.mkv")]
        )
        if p:
            self.custom_bg_var.set(p)

    def _log(self, text: str, tag: str | None = None):
        self.log_text.config(state="normal")
        if tag:
            self.log_text.insert("end", text, tag)
        else:
            if text.startswith("[1/5]") or text.startswith("[2/5]") or text.startswith("[3/5]") or \
               text.startswith("[4/5]") or text.startswith("[5/5]"):
                self.log_text.insert("end", text, "step")
            elif "hoàn tất" in text.lower() or "thành công" in text.lower():
                self.log_text.insert("end", text, "success")
            elif "lỗi" in text.lower() or "error" in text.lower() or "traceback" in text.lower():
                self.log_text.insert("end", text, "error")
            elif "sfx:" in text.lower() or "🎵 sfx:" in text.lower():
                self.log_text.insert("end", text, "sfx")
            else:
                self.log_text.insert("end", text, "info")

        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _open_help_dialog(self):
        HelpDialog(self)

    def _open_current_video(self):
        if self.current_video_path and self.current_video_path.exists():
            try:
                if os.name == "nt":
                    os.startfile(str(self.current_video_path.resolve()))
                elif sys.platform == "darwin":
                    subprocess.run(["open", str(self.current_video_path.resolve())])
                else:
                    subprocess.run(["xdg-open", str(self.current_video_path.resolve())])
            except Exception as e:
                messagebox.showerror("Lỗi mở video", str(e))

    def _open_current_dir(self):
        if self.current_video_path and self.current_video_path.exists():
            try:
                if os.name == "nt":
                    subprocess.run(["explorer", f"/select,{str(self.current_video_path.resolve())}"])
                else:
                    subprocess.run(["open" if sys.platform == "darwin" else "xdg-open",
                                    str(self.current_video_path.parent.resolve())])
            except Exception as e:
                messagebox.showerror("Lỗi mở thư mục", str(e))

    def _copy_tiktok_title(self):
        if self.tiktok_title:
            self.clipboard_clear()
            self.clipboard_append(self.tiktok_title)
            messagebox.showinfo("Đã sao chép", "Đã sao chép tiêu đề và hashtag TikTok vào bộ nhớ tạm!")

    # ── Chạy tiến trình chính ─────────────────────────────────────────────────

    def _start_task(self):
        url = self.url_var.get().strip()

        if not url:
            messagebox.showwarning("Thiếu dữ liệu", "Vui lòng nhập link bài viết Threads!")
            self.url_entry.focus_set()
            return

        cmd = [PYTHON_EXE, "-u", str(ROOT / "main.py"), url]

        # Top comments
        cmd.extend(["--top", self.top_var.get()])

        # Max chars
        try:
            mc = int(self.max_chars_var.get().strip())
            cmd.extend(["--max-chars", str(mc)])
        except ValueError:
            pass

        # Include author replies
        if self.author_replies_var.get():
            cmd.append("--include-author-replies")

        # Dark mode
        if self.dark_var.get():
            cmd.append("--dark")

        # Clean work
        if self.clean_var.get():
            cmd.append("--clean")

        # SFX
        if not self.sfx_var.get():
            cmd.append("--no-sfx")
        else:
            s_vol = float(self.sfx_vol_scale.get()) / 100.0
            cmd.extend(["--sfx-volume", f"{s_vol:.2f}"])

        # Music
        if self.music_var.get():
            cmd.append("--with-music")
            m_choice = self.music_choice_var.get()
            if m_choice and m_choice != "[Ngẫu nhiên]":
                m_path = ROOT / "assets" / "music" / m_choice
                if m_path.exists():
                    cmd.extend(["--music-file", str(m_path)])
            vol = float(self.music_vol_scale.get()) / 100.0
            cmd.extend(["--music-volume", f"{vol:.2f}"])

        # Giọng đọc
        v_choice = self.voice_var.get()
        if "NamMinh" in v_choice:
            cmd.extend(["--edge-voice", "vi-VN-NamMinhNeural"])
        elif "HoaiMy" in v_choice:
            cmd.extend(["--edge-voice", "vi-VN-HoaiMyNeural"])

        # Tốc độ đọc
        r_choice = self.rate_var.get()
        if "1.15x" in r_choice:
            cmd.extend(["--rate", "1.15x"])
        elif "1.1x" in r_choice:
            cmd.extend(["--rate", "1.1x"])
        elif "1.25x" in r_choice:
            cmd.extend(["--rate", "1.25x"])
        elif "1.2x" in r_choice:
            cmd.extend(["--rate", "1.2x"])
        elif "0.9x" in r_choice:
            cmd.extend(["--rate", "0.9x"])
        elif "0.85x" in r_choice:
            cmd.extend(["--rate", "0.85x"])
        else:
            cmd.extend(["--rate", "1.0x"])

        # Mock TTS
        if self.mock_tts_var.get():
            cmd.append("--mock-tts")

        # Video nền
        bg_mode = self.bg_mode_var.get()
        if bg_mode == "none":
            cmd.append("--no-video-bg")
        elif bg_mode == "custom":
            cust_p = self.custom_bg_var.get().strip()
            if cust_p and Path(cust_p).exists():
                cmd.extend(["--video-bg", cust_p])
            else:
                messagebox.showwarning("Thiếu video nền", "Vui lòng bấm 'Chọn file MP4...' để chọn video của bạn!")
                return
        else:
            v_choice = self.bg_preset_var.get()
            if v_choice and v_choice != "[Ngẫu nhiên]":
                v_path = ROOT / "assets" / "video" / v_choice
                if v_path.exists():
                    cmd.extend(["--video-bg", str(v_path)])

        # Show browser
        if self.show_browser_var.get():
            cmd.append("--show-browser")

        # Storage state
        state_p = self.storage_state_var.get().strip()
        if state_p:
            if Path(state_p).exists():
                cmd.extend(["--storage-state", state_p])
            else:
                messagebox.showwarning("Lỗi file session", f"File session không tồn tại:\n{state_p}")
                return

        # Bản quyền kênh (Watermark)
        if self.watermark_var.get():
            wm_text = self.watermark_text_var.get().strip()
            if wm_text:
                cmd.extend(["--watermark", wm_text])
                pos_map = {
                    "Phía trên thẻ - Góc trái (Khuyên dùng)": "above-card-left",
                    "Phía trên thẻ - Góc phải": "above-card-right",
                    "Phía trên thẻ - Ở giữa": "above-card-center",
                    "Góc trên cùng bên phải màn hình": "top-right",
                    "Góc trên cùng bên trái màn hình": "top-left",
                    "Góc dưới cùng bên trái màn hình": "bottom-left",
                    "Góc dưới cùng bên phải màn hình": "bottom-right",
                }
                cmd.extend(["--watermark-pos", pos_map.get(self.watermark_pos_var.get(), "above-card-left")])

        # Outro (Kêu gọi Follow, Tim & Cmt)
        if not self.outro_var.get():
            cmd.append("--no-outro")

        # Reset state
        self.is_running = True
        self.run_btn.config(state="disabled", text="⏳ Đang tạo video...")
        self.stop_btn.config(state="normal")
        self.open_vid_btn.config(state="disabled")
        self.open_dir_btn.config(state="disabled")
        self.copy_title_btn.config(state="disabled")
        self.prog_var.set(5)
        self.status_lbl.config(text="Đang khởi động...", fg="#38bdf8")

        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.config(state="disabled")
        self._log(f"Lệnh thực thi: {' '.join(cmd)}\n\n")

        threading.Thread(target=self._run_subprocess, args=(cmd,), daemon=True).start()

    def _stop_task(self):
        if self.process and self.is_running:
            if messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn hủy quá trình tạo video?"):
                try:
                    self.process.terminate()
                except Exception:
                    pass
                self._log("\n[Đã hủy bởi người dùng]\n", "warning")
                self._finish_task(success=False, canceled=True)

    def _run_subprocess(self, cmd: list[str]):
        extracted_video_path: Path | None = None
        extracted_title: str = ""
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
                bufsize=1
            )

            for line in iter(self.process.stdout.readline, ""):
                if not line:
                    break

                self.after(0, self._log, line)

                if "[1/5]" in line:
                    self.after(0, self._update_progress, 15, "Đọc bài & bình luận...")
                elif "[2/5]" in line:
                    self.after(0, self._update_progress, 35, "Tạo ảnh chụp thẻ Threads...")
                elif "[3/5]" in line:
                    self.after(0, self._update_progress, 55, "Tạo giọng AI & ghép cảnh...")
                elif "[4/5]" in line:
                    self.after(0, self._update_progress, 85, "Ghép video tổng hợp...")
                elif "[5/5]" in line:
                    self.after(0, self._update_progress, 95, "Tạo tiêu đề TikTok...")
                elif "Cảnh " in line and "hoàn thành" in line:
                    m = re.search(r"Cảnh (\d+)/(\d+)", line)
                    if m:
                        curr, tot = int(m.group(1)), int(m.group(2))
                        p = 55 + int((curr / tot) * 28)
                        self.after(0, self._update_progress, p, f"Ghép cảnh {curr}/{tot}...")

                if "Đường dẫn video:" in line:
                    m = re.search(r"Đường dẫn video:\s*(.+?)(?:\s*\(\d+.*s\))?$", line.strip())
                    if m:
                        extracted_video_path = Path(m.group(1).strip())

                if "Tiêu đề TikTok:" in line:
                    capturing_title = True
                    continue
                if capturing_title:
                    extracted_title += line

            self.process.stdout.close()
            ret_code = self.process.wait()
            success = (ret_code == 0 and extracted_video_path and extracted_video_path.exists())

            self.after(0, self._finish_task, success, False, extracted_video_path, extracted_title.strip())

        except Exception as e:
            self.after(0, self._log, f"\n[Lỗi ngoại lệ] {e}\n", "error")
            self.after(0, self._finish_task, False, False)

    def _update_progress(self, val: float, text: str):
        self.prog_var.set(val)
        self.status_lbl.config(text=text)

    def _finish_task(self, success: bool, canceled: bool = False,
                     video_path: Path | None = None, title: str = ""):
        self.is_running = False
        self.process = None
        self.run_btn.config(state="normal", text="🚀 BẮT ĐẦU TẠO VIDEO")
        self.stop_btn.config(state="disabled")

        if canceled:
            self.status_lbl.config(text="Đã hủy", fg="#fbbf24")
            self.prog_var.set(0)
            return

        if success and video_path:
            self.current_video_path = video_path
            self.tiktok_title = title
            self.prog_var.set(100)
            self.status_lbl.config(text="✨ Hoàn tất thành công!", fg="#34d399")

            self.res_path_var.set(str(video_path.resolve()))
            self.res_path_lbl.config(fg="#34d399")
            self.open_vid_btn.config(state="normal")
            self.open_dir_btn.config(state="normal")
            if title:
                self.copy_title_btn.config(state="normal")

            self._log("\n=======================================================\n", "success")
            self._log("🎉 TẠO VIDEO THÀNH CÔNG!\n", "success")
            self._log(f"📂 Vị trí file: {video_path.resolve()}\n", "info")
            self._log("=======================================================\n\n", "success")

            self._open_current_video()

        else:
            self.status_lbl.config(text="❌ Có lỗi xảy ra!", fg="#f87171")


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
