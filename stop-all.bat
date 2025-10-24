@echo off
echo ========================================
echo Malaysia Swimming Analytics - Stop All
echo ========================================
echo.

cd /d "C:\Users\megan\OneDrive\Documents\Malaysia Swimming Analytics"

echo Stopping all services...
docker-compose down

echo.
echo ========================================
echo All services stopped successfully!
echo ========================================
echo.
echo Press any key to continue...
pause > nul



