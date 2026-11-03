"""Script tự động đóng gói dự án thành file ZIP sạch đẹp để gửi cho người khác."""
import os
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ZIP_NAME = "threads2video_ducanhcah_package.zip"
OUT_ZIP = ROOT / ZIP_NAME

# Các thư mục và đuôi file không cần gửi (để giảm dung lượng và bảo mật)
EXCLUDE_DIRS = {
    "__pycache__",
    "output",
    ".git",
    ".github",
    ".venv",
    "venv",
    ".idea",
    ".vscode",
}

EXCLUDE_FILES = {
    ZIP_NAME,
    "threads2video_package.zip",
    "state.json",  # Cookie cá nhân không nên chia sẻ
}

EXCLUDE_EXTS = {".pyc", ".pyo", ".pyd", ".tmp"}

# File media đã nén sẵn, dùng ZIP_STORED để đóng gói siêu nhanh
STORED_EXTS = {".mp4", ".mov", ".webm", ".mp3", ".wav", ".png", ".jpg", ".jpeg"}


def make_package():
    print(f"📦 Đang đóng gói dự án vào file: {ZIP_NAME}...")
    if OUT_ZIP.exists():
        OUT_ZIP.unlink()

    total_files = 0
    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(ROOT):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

            for file in files:
                if file in EXCLUDE_FILES:
                    continue
                file_path = Path(root) / file
                if file_path.suffix.lower() in EXCLUDE_EXTS:
                    continue

                rel_path = file_path.relative_to(ROOT)
                if "output" in rel_path.parts:
                    continue

                # Chọn phương thức nén tối ưu tốc độ
                compress_type = (
                    zipfile.ZIP_STORED
                    if file_path.suffix.lower() in STORED_EXTS
                    else zipfile.ZIP_DEFLATED
                )
                zf.write(file_path, arcname=str(rel_path), compress_type=compress_type)
                total_files += 1

    size_mb = OUT_ZIP.stat().st_size / (1024 * 1024)
    print(f"✅ Đã đóng gói thành công {total_files} tệp tin!")
    print(f"📁 Tệp ZIP: {OUT_ZIP} ({size_mb:.1f} MB)")
    print("👉 Bây giờ bạn có thể gửi trực tiếp tệp ZIP này cho người khác qua Zalo, Google Drive hoặc Telegram!")


if __name__ == "__main__":
    make_package()
