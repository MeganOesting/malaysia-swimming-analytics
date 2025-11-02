@echo off
chcp 65001 >nul
setlocal ENABLEEXTENSIONS

title MALAYSIA SHELL CLEAN
prompt $P$G
set "PYTHONIOENCODING=utf-8"

REM Jump to the project root (this script's directory)
cd /d "%~dp0"

REM Enter the Statistical Analysis workspace
cd "Statistical Analysis"

echo ==============================================
echo Clean shell ready for Malaysia Swimming Analytics
echo CD: %CD%
echo ==============================================

REM Quick sanity checks
where python
if errorlevel 1 (
  echo Python not found in PATH. Please install Python 3 and retry.
) else (
  python -c "print('python ok')"
)

echo.
echo You can now run commands, e.g.:
echo   python create_delta_folders.py

echo.
cmd /k



