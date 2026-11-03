@echo off
chcp 65001 >nul
title Cai dat moi truong threads2video_ducanhcah
cd /d "%~dp0"

echo =======================================================
echo     CÀI ĐẶT MÔI TRƯỜNG THREADS2VIDEO_DUCANHCAH
echo =======================================================
echo.

echo [1/3] Đang kiểm tra Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [LỖI] Không tìm thấy Python trên máy tính!
    echo Vui lòng cài đặt Python (>= 3.10) từ https://www.python.org/
    echo Lưu ý: Khi cài nhớ tích chọn "Add Python to PATH".
    echo.
    pause
    exit /b 1
)
python --version

echo.
echo [2/3] Đang cài đặt các thư viện Python (requirements.txt)...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [LỖI] Cài đặt thư viện Python thất bại. Vui lòng kiểm tra kết nối mạng.
    pause
    exit /b 1
)

echo.
echo [3/3] Đang cài đặt trình duyệt tự động Playwright (Chromium)...
python -m playwright install chromium
if errorlevel 1 (
    echo [LỖI] Cài đặt Playwright Chromium thất bại.
    pause
    exit /b 1
)

echo.
echo =======================================================
echo     CÀI ĐẶT HOÀN TẤT THÀNH CÔNG!
echo     Bạn có thể chạy 'run_ui.bat' để mở ứng dụng ngay.
echo =======================================================
echo.
pause

