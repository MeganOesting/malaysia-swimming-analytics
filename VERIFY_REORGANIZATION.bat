@echo off
REM Quick verification script for folder reorganization
echo ========================================
echo Folder Reorganization Verification
echo ========================================
echo.

echo [1] Checking Statistical Analysis...
cd statistical_analysis
if exist "database\statistical.db" (
    echo   ✅ Database exists
    python scripts\test_statistical_db.py
) else (
    echo   ❌ Database missing
)
cd ..

echo.
echo [2] Checking Times Database...
cd times_database
if exist "database\malaysia_swimming.db" (
    echo   ✅ Database exists
    if exist "scripts\test_sqlite_db.py" (
        python scripts\test_sqlite_db.py
    ) else (
        echo   ⚠️  Test script not found
        echo   ⚠️  Note: test_database_connection.py is for PostgreSQL
    )
) else (
    echo   ❌ Database missing
)
cd ..

echo.
echo [3] Checking Reference Data...
if exist "reference_data\imports\Age_OnTrack_AQUA.xlsx" (
    echo   ✅ Age_OnTrack_AQUA.xlsx exists
) else (
    echo   ❌ Missing
)
if exist "reference_data\imports\Clubs_By_State.xlsx" (
    echo   ✅ Clubs_By_State.xlsx exists
) else (
    echo   ❌ Missing
)

echo.
echo [4] Checking Meet Data...
if exist "meets\active\2024-25" (
    dir /B "meets\active\2024-25" | find /C /V "" > temp_count.txt
    set /p file_count=<temp_count.txt
    del temp_count.txt
    echo   ✅ Found %file_count% files in meets\active\2024-25\
) else (
    echo   ❌ Missing
)

echo.
echo ========================================
echo Verification Complete
echo ========================================
pause

