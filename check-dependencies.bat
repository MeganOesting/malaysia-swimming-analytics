@echo off
REM Quick dependency checker for Malaysia Swimming Analytics

echo ========================================
echo Malaysia Swimming Analytics
echo Dependency Checker
echo ========================================
echo.

cd /d "%~dp0"

echo Checking Python dependencies...
python -c "import fastapi; import uvicorn; import pandas; import openpyxl; import sqlite3; print('✓ All critical Python packages installed')" 2>nul
if errorlevel 1 (
    echo ✗ Missing Python packages
    echo Run: pip install -r requirements.txt
) else (
    echo ✓ Python dependencies OK
)
echo.

echo Checking Node.js dependencies...
if exist "node_modules\next" (
    echo ✓ Node.js dependencies OK
) else (
    echo ✗ Missing Node.js packages
    echo Run: npm install
)
echo.

echo Checking database...
if exist "malaysia_swimming.db" (
    echo ✓ Database found
) else (
    echo ⚠ Database not found (will be created on first upload)
)
echo.

pause















