@echo off
REM Malaysia Swimming Analytics - Automated Development Startup Script
REM This script checks dependencies and starts both frontend and backend servers

echo ========================================
echo Malaysia Swimming Analytics
echo Automated Development Startup
echo ========================================
echo.

cd /d "%~dp0"

REM Check Python installation
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)
python --version
echo.

REM Check Node.js installation
echo [2/5] Checking Node.js installation...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js 18+ from https://nodejs.org/
    pause
    exit /b 1
)
node --version
echo.

REM Check and install Python dependencies
echo [3/5] Checking Python dependencies...
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo Installing Python dependencies from requirements.txt...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install Python dependencies
        pause
        exit /b 1
    )
    echo Python dependencies installed successfully.
) else (
    echo Python dependencies are already installed.
)
echo.

REM Check and install Node dependencies
echo [4/5] Checking Node.js dependencies...
if not exist "node_modules" (
    echo Installing Node.js dependencies from package.json...
    call npm install
    if errorlevel 1 (
        echo ERROR: Failed to install Node.js dependencies
        pause
        exit /b 1
    )
    echo Node.js dependencies installed successfully.
) else (
    echo Node.js dependencies are already installed.
)
echo.

REM Check database exists
echo [5/5] Checking database...
if exist "malaysia_swimming.db" (
    echo Database found: malaysia_swimming.db
) else (
    echo WARNING: Database not found. It will be created on first upload.
)
echo.

echo ========================================
echo Starting Development Servers...
echo ========================================
echo.
echo IMPORTANT: This will open TWO terminal windows:
echo   - Terminal 1: FastAPI Backend (port 8000)
echo   - Terminal 2: Next.js Frontend (port 3000)
echo.
echo Press any key to continue...
pause >nul

REM Start backend in new window
echo Starting Backend Server...
start "Malaysia Swimming Analytics - Backend" cmd /k "cd /d %~dp0 && python -m uvicorn src.web.main:app --reload --host 127.0.0.1 --port 8000"

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend in new window
echo Starting Frontend Server...
start "Malaysia Swimming Analytics - Frontend" cmd /k "cd /d %~dp0 && npm run dev"

echo.
echo ========================================
echo Servers Starting...
echo ========================================
echo.
echo Backend API: http://localhost:8000
echo Backend Docs: http://localhost:8000/api/docs
echo Frontend: http://localhost:3000
echo Admin Panel: http://localhost:3000/admin
echo.
echo Both servers are running in separate windows.
echo Close those windows to stop the servers.
echo.
echo Press any key to exit this startup script...
pause >nul















