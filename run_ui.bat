@echo off
title threads2video_ducanhcah
cd /d "%~dp0"
python gui.py
if errorlevel 1 (
    echo.
    echo [Loi] Khong the khoi dong giao dien. Nhan phim bat ky de thoat...
    pause >nul
)

