@echo off
echo ========================================
echo Malaysia Swimming Analytics - Auto Start
echo ========================================
echo.

cd /d "C:\Users\megan\OneDrive\Documents\Malaysia Swimming Analytics"

echo Starting all services...
docker-compose up -d

echo.
echo ========================================
echo All services started successfully!
echo ========================================
echo.
echo Access Points:
echo - Frontend: http://localhost:3000
echo - Backend API: http://localhost:8000
echo - API Documentation: http://localhost:8000/api/docs
echo - Flower Monitoring: http://localhost:5555
echo.
echo Press any key to continue...
pause > nul



