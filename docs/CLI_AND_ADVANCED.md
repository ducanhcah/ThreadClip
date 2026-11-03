# 💻 Hướng dẫn Dành Cho Lập Trình Viên (CLI & Cấu hình Nâng Cao)

Tài liệu này dành cho các bạn muốn chạy tự động hóa hàng loạt bằng script hoặc dòng lệnh Command Prompt / PowerShell.

---

## 🚀 Các lệnh CLI thông dụng

```bash
# 1. Chạy cơ bản nhất:
python src/main.py "https://www.threads.com/@user/post/..."

# 2. Chọn 7 bình luận, bật Dark Mode, tự dọn file tạm:
python src/main.py "https://www.threads.com/@user/post/..." --top 7 --dark --clean

# 3. Tốc độ đọc nhanh 1.15x, đóng dấu bản quyền kênh:
python src/main.py "https://www.threads.com/@user/post/..." --rate 1.15x --watermark "@kenhcuaban" --watermark-pos above-card-left

# 4. Chỉ định video nền và bật nhạc nền TikTok:
python src/main.py "https://www.threads.com/@user/post/..." --video-bg assets/video/Subway-Surfers-Gameplay.mp4 --with-music --music-volume 0.12

# 5. Dựng lại từ file data.json có sẵn (không cần kết nối mạng cào lại):
python src/main.py --from-json output/XXXX/data.json --dark --clean

# 6. Chạy thử pipeline test nhanh không gọi giọng TTS:
python src/main.py --from-json sample/sample.json --mock-tts --dark
```

---

## 📋 Bảng tham số dòng lệnh chi tiết

| Tham số | Mặc định | Ý nghĩa & Mô tả |
|---|---|---|
| `url` | Bắt buộc | Link bài viết Threads cần tạo video. |
| `--from-json` | `None` | Dùng file `data.json` có sẵn thay vì cào lại web. |
| `--top` | `5` | Số bình luận hiển thị trong video. |
| `--rate`, `--tts-rate` | `1.0x` | Tốc độ đọc AI (`1.15x`, `1.2x`, `0.95x` hoặc `+15%`). |
| `--edge-voice` | Tự động | Ghi đè giọng đọc (`vi-VN-NamMinhNeural` hoặc `vi-VN-HoaiMyNeural`). |
| `--dark` | `False` | Giao diện thẻ tối (Dark Mode). |
| `--clean` | `False` | Xóa thư mục làm việc tạm thời `work/` sau khi xuất video. |
| `--watermark` | `""` | Tên bản quyền kênh đóng dấu trên video. |
| `--watermark-pos` | `above-card-left` | Vị trí bản quyền (`above-card-left`, `above-card-right`, `top-right`, `bottom-left`...). |
| `--no-outro` | `False` | Tắt cảnh kêu gọi Follow, Thả Tim và Bình luận ở cuối. |
| `--max-chars` | `300` | Bỏ qua bình luận dài quá số ký tự này để tránh loãng video. |
| `--video-bg` | `assets/video/` | File MP4 nền hoặc thư mục chứa các video nền. |
| `--with-music` | `False` | Bật nhạc nền TikTok. |
| `--music-volume` | `0.12` | Âm lượng nhạc nền so với giọng đọc (từ `0.05` đến `0.50`). |
| `--sfx-volume` | `0.35` | Âm lượng hiệu ứng meme SFX (từ `0.05` đến `1.00`). |
| `--no-sfx` | `False` | Tắt hoàn toàn hiệu ứng âm thanh meme. |
| `--mock-tts` | `False` | Giả lập âm thanh thử nghiệm siêu nhanh (không tốn mạng). |
| `--storage-state` | `None` | File lưu phiên đăng nhập Threads (`state.json`). |

---

## 🔧 Xử lý lỗi nâng cao

- **Nghẽn kết nối Microsoft Edge TTS:** Hệ thống tự động thử lại 5 lần kèm cơ chế đổi giọng dự phòng và fallback tự động sang Google TTS nếu máy chủ Microsoft quá tải.
- **Lưu phiên đăng nhập Threads (`state.json`):** Nếu một bài viết nằm trong nhóm riêng tư, bạn có thể tạo phiên đăng nhập một lần:
  ```bash
  python -m playwright codegen --save-storage=state.json https://www.threads.com
  ```

