@echo off
chcp 65001 >nul
title Dong goi du an threads2video_ducanhcah
cd /d "%~dp0"

echo =======================================================
echo     ĐÓNG GÓI DỰ ÁN THREADS2VIDEO_DUCANHCAH
echo =======================================================
echo.
python package.py
echo.
pause

