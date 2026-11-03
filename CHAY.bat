@echo off
chcp 65001 >nul
cd /d "%~dp0"
title ThreadClip

REM 1. Kiem tra Python trong runtime hoac he thong
if exist "%~dp0runtime\python\python.exe" (
    set "PY_EXE=%~dp0runtime\python\python.exe"
    goto :RUN
)

where python >nul 2>&1
if not errorlevel 1 (
    set "PY_EXE=python"
    goto :RUN
)

REM 2. Neu may chua co Python: Tu dong bootstrap runtime
echo ============================================================
echo           CHAO MUNG BAN DEN VOI THREADCLIP!
echo ============================================================
echo.
echo  He thong dang tu dong chuan bi moi truong lan dau...
echo  Qua trinh nay chi mat 1-2 phut. Vui long khong tat cua so!
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0src\bootstrap.ps1"
if exist "%~dp0runtime\python\python.exe" (
    set "PY_EXE=%~dp0runtime\python\python.exe"
    goto :RUN
)

echo.
echo [!] Khong the khoi tao moi truong tu dong.
echo Ban hay cai dat Python tu https://www.python.org/ (nho tich Add Python to PATH)
pause
exit /b 1

:RUN
REM 3. Kiem tra thu vien neu dung Python he thong
%PY_EXE% -c "import edge_tts, playwright, PIL, requests" >nul 2>&1
if errorlevel 1 (
    echo [*] Dang cai dat thu vien lan dau...
    %PY_EXE% -m pip install -r "%~dp0requirements.txt" --quiet
    %PY_EXE% -m playwright install chromium --quiet
)

REM 4. Khoi chay giao dien ThreadClip
%PY_EXE% "%~dp0src\gui.py"
if errorlevel 1 (
    echo.
    echo ============================================================
    echo  [!] Co loi xay ra khi khoi chay ung dung.
    echo ============================================================
    pause
)
