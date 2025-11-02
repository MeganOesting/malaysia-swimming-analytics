@echo off
REM Comprehensive test of all databases and structure
cd /d "C:\Users\megan\OneDrive\Documents\Malaysia Swimming Analytics"

echo ========================================
echo Comprehensive Database Test
echo ========================================
echo.

echo [1] Testing Statistical Database...
cd statistical_analysis
python scripts\test_statistical_db.py
cd ..
echo.

echo [2] Testing Times Database...
cd times_database
python scripts\test_sqlite_db.py
cd ..
echo.

echo ========================================
echo All Tests Complete
echo ========================================
pause




