@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title Cai dat moi truong threads2video_ducanhcah
cd /d "%~dp0"

echo =======================================================
echo     CÀI ĐẶT MÔI TRƯỜNG THREADS2VIDEO_DUCANHCAH
echo =======================================================
echo.

REM ─── BƯỚC 1: KIỂM TRA PYTHON ────────────────────────────
echo [1/4] Đang kiểm tra Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo =======================================================
    echo  [!] THÔNG BÁO: MÁY TÍNH CỦA BẠN CHƯA CÀI ĐẶT PYTHON!
    echo =======================================================
    echo.
    echo  Bạn hãy làm theo các bước sau để cài đặt nhé:
    echo.
    echo  1. Tải bộ cài Python tại: https://www.python.org/downloads/
    echo     (Trình duyệt web sẽ tự động mở trang tải ngay bây giờ)
    echo.
    echo  2. ⚠️ LƯU Ý CỰC KỲ QUAN TRỌNG KHI CÀI ĐẶT:
    echo     Ở màn hình cài đặt đầu tiên, bạn BẮT BUỘC phải tích chọn ô:
    echo     [x] "Add Python to PATH" (ở góc dưới cùng màn hình).
    echo.
    echo  3. Sau khi cài xong Python, bạn hãy MỞ LẠI file INSTALL.bat
    echo     này để hệ thống tiếp tục cài đặt tự động toàn bộ nhé!
    echo.
    echo =======================================================
    echo.
    start https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version

REM ─── BƯỚC 2: KIỂM TRA & TỰ ĐỘNG CÀI ĐẶT FFMPEG ─────────
echo.
echo [2/4] Đang kiểm tra công cụ xử lý video FFmpeg...
where ffmpeg >nul 2>&1
if errorlevel 1 (
    set "FFMPEG_FOUND=0"
    if exist "%LOCALAPPDATA%\Microsoft\WinGet\Packages" (
        for /d %%D in ("%LOCALAPPDATA%\Microsoft\WinGet\Packages\*ffmpeg*") do (
            if exist "%%D\bin\ffmpeg.exe" set "FFMPEG_FOUND=1"
        )
    )
    if "!FFMPEG_FOUND!"=="1" (
        echo [OK] Đã tìm thấy FFmpeg trong gói hệ thống.
    ) else (
        echo Chưa tìm thấy FFmpeg. Đang tự động tải và cài đặt qua winget...
        winget install Gyan.FFmpeg --accept-package-agreements --accept-source-agreements
        if errorlevel 1 (
            echo.
            echo [Lưu ý] Cài đặt FFmpeg tự động chưa hoàn tất.
            echo Nếu sau này báo thiếu FFmpeg, bạn chỉ cần mở PowerShell và gõ:
            echo   winget install Gyan.FFmpeg
            echo.
        ) else (
            echo [OK] Cài đặt FFmpeg thành công!
        )
    )
) else (
    echo [OK] Đã có sẵn FFmpeg trên máy tính.
)

REM ─── BƯỚC 3: CÀI ĐẶT THƯ VIỆN PYTHON ────────────────────
echo.
echo [3/4] Đang cài đặt các thư viện Python (requirements.txt)...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [LỖI] Cài đặt thư viện Python thất bại. Vui lòng kiểm tra lại kết nối mạng.
    pause
    exit /b 1
)

REM ─── BƯỚC 4: CÀI ĐẶT TRÌNH DUYỆT PLAYWRIGHT CHROMIUM ───
echo.
echo [4/4] Đang cài đặt trình duyệt tự động Playwright (Chromium)...
python -m playwright install chromium
if errorlevel 1 (
    echo.
    echo [LỖI] Cài đặt Playwright Chromium thất bại.
    pause
    exit /b 1
)

REM ─── HOÀN TẤT ──────────────────────────────────────────
echo.
echo =======================================================
echo     CÀI ĐẶT TOÀN BỘ HOÀN TẤT THÀNH CÔNG!
echo     Bạn chỉ cần nhấp đúp 'threads2video_ducanhcah.bat'
echo     để mở ứng dụng và bắt đầu tạo video ngay lập tức!
echo =======================================================
echo.
pause
