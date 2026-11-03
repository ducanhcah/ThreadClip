# 🎬 threads2video_ducanhcah — Tự Động Tạo Video Ngắn TikTok Từ Threads

> Biến link bài viết **Threads** bất kỳ thành **video ngắn 9:16** chuẩn TikTok, Facebook Reels, YouTube Shorts chỉ với 1 cú click chuột — Tự động chụp thẻ bài viết Threads, lồng giọng đọc AI tiếng Việt 100% miễn phí, video nền chuyển động gameplay cuốn hút, hiệu ứng âm thanh meme hài hước, tùy chỉnh tốc độ đọc và gắn bản quyền kênh.

---

## ✨ Tính năng nổi bật

- 🎙️ **Giọng đọc AI tiếng Việt 100% miễn phí:** Sử dụng công nghệ Microsoft Edge Neural TTS cao cấp, không tốn phí, không cần đăng ký tài khoản hay API Key (hoàn toàn không dùng Claude, Gemini hay OpenAI). Tự động nhận diện Nam/Nữ và xen kẽ giọng giữa các bình luận để video sống động như một cuộc đối thoại thật.
- ⚡ **Tùy chỉnh tốc độ đọc (0.85x – 1.25x):** Dễ dàng điều chỉnh tốc độ đọc: từ chậm rãi tâm sự (`0.85x`, `0.9x`) đến tốc độ nhanh cuốn hút chuẩn viral TikTok (`1.1x`, `1.15x`, `1.2x`) giúp tối ưu tỷ lệ giữ chân người xem (retention rate).
- 🗣️ **Chuẩn hóa tiếng Việt & Teencode Gen Z thịnh hành:** Tích hợp bộ từ điển thông minh tự động phát hiện và dịch hàng trăm từ viết tắt, từ lóng trên mạng xã hội (`ko` $\rightarrow$ không, `dc` $\rightarrow$ được, `vl/vcl` $\rightarrow$ rất, `cmt` $\rightarrow$ bình luận, `thik` $\rightarrow$ thích, `iu/iuu` $\rightarrow$ yêu, `bùn` $\rightarrow$ buồn, `zui` $\rightarrow$ vui, `sn` $\rightarrow$ sinh nhật, `mn` $\rightarrow$ mọi người, `1xx` $\rightarrow$ hơn một trăm nghìn, `50k` $\rightarrow$ năm mươi nghìn...).
- 🛡️ **Bộ lọc Spam & Link ngoài tự động:** Tự động phát hiện và loại bỏ triệt để các bình luận gắn link ngoài (Shopee, Lazada, TikTok Shop, bio, nhóm Telegram, Zalo...), quảng cáo lừa đảo, cờ bạc tài xỉu, "tuyển ctv việc nhẹ lương cao", đảm bảo video chỉ giữ lại nội dung thảo luận chất lượng.
- 🎮 **Video nền chuyển động & Nhạc nền TikTok:** Tích hợp sẵn các video nền gameplay và ASMR cực cuốn (Subway Surfers, Minecraft Parkour, Làm bánh/Nấu ăn, Cắt cát Kinetic Sand, Slime ASMR). Video nền chạy nối tiếp mượt mà qua các cảnh, không bị ngắt quãng giật cục.
- 💥 **Meme Sound Effects (SFX) viral TikTok:** Phân tích ngữ cảnh từng cảnh (hài hước, bất ngờ, sốc, kịch tính...) để chèn âm thanh meme đúng thời điểm (pop, bruh, ting, gasp, wow...). Tích hợp thanh trượt chỉnh âm lượng SFX (5% – 100%) và âm lượng nhạc nền (5% – 50%).
- 🏷️ **Tự động tạo Tiêu đề & Hashtag TikTok:** Tự động phân tích nội dung bài viết và tạo sẵn tiêu đề TikTok hấp dẫn, bắt trend kèm bộ hashtag viral (`#threads #topic #fyp #viral #xuhuong`).
- 🛡️ **Bản quyền kênh (Watermark) đa vị trí:** Đóng dấu thương hiệu kênh (`@ducanhcah` hoặc tên riêng của bạn) với thiết kế huy hiệu bo góc mờ sang trọng. Vị trí mặc định: ngay phía trên đầu thẻ bài viết lệch trái (vị trí vàng tránh toàn bộ thanh điều hướng và nút tương tác của TikTok).
- 🔔 **Cảnh kết thúc tương tác (Outro: Follow, Tim & Cmt):** Tự động chèn thẻ Outro bắt mắt ở cuối video: *"Hãy bấm Follow kênh, thả Tim và để lại Bình luận để đón xem những video mới nhất nhé! ✨"* kèm giọng đọc AI và SFX tươi vui giúp tối đa hóa lượt follow.

---

## 📋 Yêu cầu hệ thống

| Phần mềm | Phiên bản | Ghi chú |
|---|---|---|
| **Python** | ≥ 3.10 (3.10 – 3.15) | Bắt buộc tích chọn **"Add Python to PATH"** khi cài |
| **FFmpeg & FFprobe** | Mới nhất | Cài tự động cực nhanh qua lệnh Windows: `winget install Gyan.FFmpeg` |
| **Playwright Chromium** | Mới nhất | Tự động cài đặt 100% qua file `install.bat` |
| **Hệ điều hành** | Windows 10 / 11 (64-bit) | Hỗ trợ cả macOS & Linux qua giao diện dòng lệnh (CLI) |

---

## 🚀 Cài đặt & Chạy

### Cách nhanh nhất trên Windows
1. Tải file cài đặt **[threads2video_ducanhcah_package.zip](https://github.com/ducanhcah/threads2video_ducanhcah/releases/latest)** trong mục **[Releases](https://github.com/ducanhcah/threads2video_ducanhcah/releases)**.
2. **Giải nén toàn bộ file ZIP** ra một thư mục mới (Ví dụ: `D:\threads2video_ducanhcah`). **Không chạy trực tiếp bên trong file ZIP.**
3. Cài đặt **[Python (>= 3.10)](https://www.python.org/downloads/)** nếu máy chưa có *(⚠️ Bắt buộc tích chọn vào ô **"Add Python to PATH"** ở bước cài đặt đầu tiên)*.
4. Cài đặt **FFmpeg** (nếu máy chưa có) bằng cách mở PowerShell và gõ:
   ```powershell
   winget install Gyan.FFmpeg
   ```
5. Nhấp đúp chuột vào file **`install.bat`** (chỉ cần chạy **1 lần duy nhất** lúc mới tải về để tự động cài thư viện và Playwright Chromium).
6. Nhấp đúp file **`run_ui.bat`** để mở giao diện Studio tạo video.

> ⚠️ **Lưu ý:** Không tải *"Source code (zip)"* nếu bạn muốn sử dụng ngay đầy đủ tài nguyên. File source tự động của GitHub không chứa các video nền nặng (Subway Surfers, Minecraft...); hãy tải đúng file **`threads2video_ducanhcah_package.zip`** ở mục **Releases**.

---

### Dấu hiệu cài đặt thành công
Sau khi nhấp đúp `run_ui.bat`:
- Cửa sổ ứng dụng **`threads2video_ducanhcah`** hiển thị giao diện Dark Mode hiện đại.
- Danh sách video nền (*Subway Surfers, Minecraft, ASMR...*) và nhạc nền hiển thị đầy đủ trong menu chọn.
- Khung nhật ký bên dưới sẵn sàng ghi nhận tiến trình tạo video.

---

## 🖥️ Hướng dẫn sử dụng giao diện (GUI)

Chỉ với **3 bước đơn giản** để tạo một video hoàn chỉnh:

```text
[1. Dán link bài Threads] ──> [2. Chọn tùy chọn video/nhạc/tốc độ] ──> [3. Bấm BẮT ĐẦU TẠO VIDEO]
```

1. **Bước 1: Dán link bài viết:**
   - Sao chép liên kết bài viết Threads bất kỳ (ví dụ: `https://www.threads.com/@user/post/...`).
   - Bấm nút **📋 Dán link** trên giao diện.
2. **Bước 2: Tùy chỉnh theo ý muốn:**
   - **Số bình luận:** Chọn 3, 5, 7, 10 hoặc 15 bình luận nổi bật nhất.
   - **Tốc độ đọc:** Chọn `1.15x (Chuẩn TikTok viral)` để video cuốn hút hơn, hoặc `1.0x (Bình thường)`, `0.9x (Chậm rãi, tâm sự)`.
   - **Video nền:** Chọn video có sẵn (Subway Surfers, Minecraft Parkour, ASMR...) hoặc tự chọn file MP4 từ máy tính.
   - **Meme SFX & Nhạc nền:** Bật/tắt và chỉnh âm lượng linh hoạt bằng thanh trượt.
   - **Bản quyền kênh (Watermark):** Tích chọn để đóng dấu tên kênh của bạn (mặc định: `@ducanhcah` ở vị trí phía trên thẻ bài viết).
   - **Cảnh kết thúc (Outro):** Tích chọn để tự động thêm lời kêu gọi Follow, Tim & Cmt ở cuối video.
3. **Bước 3: Bấm tạo video:**
   - Bấm nút **🚀 BẮT ĐẦU TẠO VIDEO**.
   - Theo dõi tiến trình trực tiếp qua khung Terminal Logs bên dưới.
   - Khi hoàn thành, video sẽ **tự động mở phát ngay lập tức**, đồng thời hiển thị đường dẫn file, nút **📁 Mở thư mục** và nút **📋 Sao chép tiêu đề TikTok**.

> 💡 **Mẹo:** Trên giao diện có nút **📖 Hướng dẫn sử dụng** ở góc trên bên phải. Bạn có thể bấm vào bất kỳ lúc nào để xem nhanh tài liệu ngay trong ứng dụng.

---

## 💻 Dành cho lập trình viên — Chạy bằng CLI (Dòng lệnh)

Nếu muốn chạy qua Command Prompt / PowerShell hoặc tự động hóa hàng loạt bằng script:

```bash
# 1. Chạy cơ bản nhất:
python main.py "https://www.threads.com/@user/post/..."

# 2. Lấy 7 bình luận, bật Dark Mode, dọn dẹp file tạm sau khi làm xong:
python main.py "https://www.threads.com/@user/post/..." --top 7 --dark --clean

# 3. Đọc tốc độ nhanh 1.15x chuẩn TikTok, gắn bản quyền kênh:
python main.py "https://www.threads.com/@user/post/..." --rate 1.15x --watermark "@ducanhcah" --watermark-pos above-card-left

# 4. Chỉ định video nền Subway Surfers và bật nhạc nền:
python main.py "https://www.threads.com/@user/post/..." --video-bg assets/video/Subway-Surfers-Gameplay.mp4 --with-music --music-volume 0.10

# 5. Cố định giọng đọc nam tiếng Việt:
python main.py "https://www.threads.com/@user/post/..." --edge-voice vi-VN-NamMinhNeural

# 6. Dựng lại video từ dữ liệu data.json đã cào (không cần cào lại mạng):
python main.py --from-json output/XXXX/data.json --dark --clean

# 7. Chạy thử test pipeline siêu nhanh bằng âm thanh giả (không tốn mạng):
python main.py --from-json sample/sample.json --mock-tts --dark
```

### 📋 Bảng tham số dòng lệnh chi tiết:

| Tham số | Mặc định | Ý nghĩa & Mô tả chi tiết |
|---|---|---|
| `url` | Bắt buộc | Đường link bài viết Threads cần tạo video. |
| `--from-json` | `None` | Dùng file `data.json` có sẵn thay vì cào lại web. |
| `--top` | `5` | Số lượng bình luận được chọn hiển thị trong video. |
| `--rate`, `--tts-rate` | `1.0x` | Tốc độ đọc AI (vd: `1.15x`, `1.2x` nhanh cuốn hút, `0.9x` chậm tâm sự hoặc `+15%`, `-10%`). |
| `--edge-voice` | Tự động | Ghi đè giọng đọc (`vi-VN-NamMinhNeural` hoặc `vi-VN-HoaiMyNeural`). |
| `--dark` | `False` | Sử dụng giao diện tối (Dark Mode) cho các thẻ bài viết. |
| `--clean` | `False` | Tự động xóa thư mục file tạm (`work/`) sau khi render xong. |
| `--watermark` | `""` | Tên bản quyền kênh đóng dấu trên video (vd: `@ducanhcah`). |
| `--watermark-pos` | `above-card-left` | Vị trí bản quyền (`above-card-left` [mặc định chuẩn TikTok], `above-card-right`, `above-card-center`, `top-right`, `top-left`, `bottom-left`, `bottom-right`). |
| `--no-outro` | `False` | Tắt cảnh kêu gọi Follow, Thả Tim và Bình luận ở cuối video. |
| `--max-chars` | `300` | Bỏ qua bình luận dài quá số ký tự này để tránh làm loãng video. |
| `--include-author-replies` | `False` | Giữ lại các phản hồi của chính chủ thớt (mặc định chỉ lấy bình luận của người khác). |
| `--video-bg` | `assets/video/` | Đường dẫn file MP4 nền hoặc thư mục chứa các video nền. |
| `--no-video-bg` | `False` | Tắt video nền, dùng nền ảnh tĩnh dạng lưới truyền thống. |
| `--with-music` | `False` | Bật nhạc nền TikTok (mặc định tắt để giọng đọc rõ nét nhất). |
| `--music-file` | `None` | Chọn chính xác một file nhạc nền `.mp3` cụ thể. |
| `--music-volume` | `0.12` | Âm lượng nhạc nền so với giọng đọc (từ `0.05` đến `0.50`). |
| `--sfx-volume` | `0.35` | Âm lượng hiệu ứng âm thanh meme SFX (từ `0.05` đến `1.00`). |
| `--no-sfx` | `False` | Tắt hoàn toàn hiệu ứng âm thanh meme. |
| `--show-browser` | `False` | Mở trực quan cửa sổ trình duyệt Chromium khi cào bài viết. |
| `--mock-tts` | `False` | Giả lập âm thanh thử nghiệm siêu nhanh (không tốn mạng). |
| `--storage-state` | `None` | Đường dẫn file cookie/phiên đăng nhập Threads (`state.json`). |

---

## 📁 Cấu trúc thư mục

```text
threads2video_ducanhcah/
├── assets/
│   ├── music/              # 🎵 10 bản nhạc nền TikTok viral (Monkeys Spinning, Sneaky Snitch...)
│   ├── sfx/                # 💥 24 hiệu ứng âm thanh meme TikTok (pop, bruh, ting, gasp...)
│   └── video/              # 🎬 5 video nền gameplay & ASMR (Subway Surfers, Minecraft...)
├── output/                 # 🎯 Thư mục xuất video thành phẩm (video.mp4, title.txt, data.json)
├── run_ui.bat              # 🚀 Nhấp đúp để mở giao diện đồ họa Studio
├── install.bat             # ⚙️ Script cài đặt tự động môi trường (chạy 1 lần đầu)
├── gui.py                  # Mã nguồn giao diện người dùng Tkinter Dark Mode
├── main.py                 # Script điều phối chính toàn bộ quy trình dựng video
├── tts.py                  # Module tổng hợp giọng đọc AI tiếng Việt Edge TTS & tốc độ đọc
├── cards.py                # Module dựng thẻ bài viết/bình luận Threads & đóng dấu bản quyền
├── text_norm.py            # Bộ từ điển chuẩn hóa Teencode & từ lóng mạng xã hội Gen Z
├── meme_sfx.py             # Thư viện âm thanh meme TikTok
├── sound_designer.py       # Hệ thống phân tích cảm xúc và canh nhịp SFX tự động
├── title.py                # Bộ tạo tiêu đề TikTok và hashtag thịnh hành
├── video.py                # Xử lý video, ghép cảnh, lặp nền và trộn âm thanh bằng FFmpeg
├── scraper.py              # Trình cào dữ liệu bài viết & bình luận Threads qua Playwright
├── requirements.txt        # Danh sách thư viện Python cần thiết
└── README.md               # Tài liệu hướng dẫn sử dụng này
```

---

## 🎵 Thêm nhạc & video nền tùy thích

Dự án đã chuẩn bị sẵn tài nguyên phong phú trong thư mục `assets/` để chạy được ngay:
- **Thêm bài nhạc nền:** Thả file `.mp3`, `.wav`, `.ogg` vào `assets/music/`.
- **Thêm video nền gameplay/ASMR:** Thả file `.mp4`, `.mov`, `.webm` vào `assets/video/`.
- **Thêm âm thanh meme:** Thả file `.mp3` vào `assets/sfx/`.

*(Lưu ý: Ứng dụng tự động quét và hiển thị toàn bộ file bạn thêm vào danh sách lựa chọn trên giao diện UI).*

---

## 🔧 Xử lý lỗi thường gặp (Troubleshooting)

**1. `python` không được nhận diện là lệnh nội bộ:**
> Do khi cài đặt Python bạn chưa tích chọn **"Add Python to PATH"**. Hãy tải lại bộ cài Python, chọn *Modify* và tích chọn ô này, sau đó khởi động lại máy tính.

**2. Không tìm thấy `ffmpeg` hoặc `ffprobe`:**
> Mở PowerShell và chạy lệnh `winget install Gyan.FFmpeg`. Ứng dụng đã có cơ chế tự động quét WinGet Packages và Windows Registry để nhận diện FFmpeg ngay lập tức.

**3. Gặp lỗi "No audio was received" khi tạo giọng đọc Edge TTS:**
> Lỗi này do máy chủ Microsoft phản hồi chậm hoặc mạng gia đình bị nghẽn WebSocket tạm thời. Hệ thống đã tích hợp sẵn cơ chế tự động thử lại 5 lần kèm đổi giọng dự phòng thông minh. Bạn chỉ cần bấm tạo lại là sẽ thành công.

**4. Bình luận chứa link Shopee/Lazada không xuất hiện trong video:**
> Đây là tính năng chủ động nhằm bảo vệ kênh của bạn. Hệ thống tự động lọc bỏ các bình luận gắn link ngoài, spam mua sắm để video không bị TikTok/Facebook đánh gậy vi phạm chính sách quảng cáo.

**5. Khi nào cần dùng `state.json` (Phiên đăng nhập Threads)?**
> Thông thường Threads cho phép xem bài viết công khai không cần đăng nhập. Tuy nhiên, nếu một bài viết ở chế độ riêng tư hoặc Threads yêu cầu xác thực, bạn chỉ cần mở terminal và chạy lệnh sau một lần để lưu phiên:
> ```bash
> python -m playwright codegen --save-storage=state.json https://www.threads.com
> ```
> Đăng nhập tài khoản của bạn xong rồi đóng cửa sổ lại. Sau đó chọn file `state.json` này trong mục **Tùy chọn nâng cao** trên giao diện.

---

## 📞 Liên hệ & Bản quyền

- 👑 **Tác giả:** **ducanhcah**
- 🎬 **Dự án:** **threads2video_ducanhcah**
- 🛡️ **Bản quyền:** Thuộc sở hữu của **ducanhcah**
- 🌐 **Kênh nội dung:** *(Cập nhật link TikTok / Threads / Facebook của bạn tại đây)*
- 💬 **Hỗ trợ / Góp ý:** Liên hệ qua Zalo / Telegram / Kênh cá nhân

---
*Made with ❤️ by **ducanhcah** — Tối ưu hóa cho Content Creator TikTok, Reels & Shorts.*
