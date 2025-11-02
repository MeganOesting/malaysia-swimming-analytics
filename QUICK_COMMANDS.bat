@echo off
REM Quick navigation commands for the reorganized structure
echo ========================================
echo Malaysia Swimming Analytics - Quick Commands
echo ========================================
echo.
echo Current location: %CD%
echo.
echo Available commands:
echo.
echo 1. Clean up statistical tables:
echo    cd times_database
echo    python scripts\cleanup_statistical_tables.py
echo.
echo 2. Test Statistical Database:
echo    cd statistical_analysis
echo    python scripts\test_statistical_db.py
echo.
echo 3. Test Times Database:
echo    cd times_database
echo    python scripts\test_sqlite_db.py
echo.
echo 4. Verify Everything:
echo    VERIFY_REORGANIZATION.bat
echo.
echo ========================================
echo.
echo Navigating to project root...
cd /d "C:\Users\megan\OneDrive\Documents\Malaysia Swimming Analytics"
echo Current directory: %CD%
echo.
echo You can now run:
echo   - cd times_database ^&^& python scripts\cleanup_statistical_tables.py
echo   - cd statistical_analysis ^&^& python scripts\test_statistical_db.py
echo   - VERIFY_REORGANIZATION.bat
echo.
pause




