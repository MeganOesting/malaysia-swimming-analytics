@echo off
REM Folder Reorganization Migration Script
REM Run this from the project root: "Malaysia Swimming Analytics"
echo Starting folder reorganization...
echo.

REM Stage 1: Move Reference Data (already copied, just verifying)
echo [Stage 1] Reference Data...
if not exist "reference_data\imports\Age_OnTrack_AQUA.xlsx" (
    echo Copying reference data...
    xcopy "data\reference\*" "reference_data\imports\" /Y /Q
    echo Reference data copied.
) else (
    echo Reference data already in place.
)

REM Stage 2: Move Meet Data
echo [Stage 2] Meet Data...
if not exist "meets\active\2024-25" mkdir "meets\active\2024-25"
xcopy "data\meets\*" "meets\active\2024-25\" /Y /Q
echo Meet data moved to meets\active\2024-25\

REM Stage 3: Move Statistical Analysis Project
echo [Stage 3] Statistical Analysis Project...
REM Move Period Data
xcopy "Statistical Analysis\Period Data" "statistical_analysis\data\Period Data\" /E /I /Y /Q
REM Move Delta Data
xcopy "Statistical Analysis\Delta Data" "statistical_analysis\data\Delta Data\" /E /I /Y /Q
REM Move Reports
xcopy "Statistical Analysis\reports" "statistical_analysis\reports\" /E /I /Y /Q
REM Move PhD folder
xcopy "Statistical Analysis\PhD" "statistical_analysis\PhD\" /E /I /Y /Q
REM Move scripts to scripts folder
xcopy "Statistical Analysis\*.py" "statistical_analysis\scripts\" /Y /Q
REM Move documentation and data files
xcopy "Statistical Analysis\*.csv" "statistical_analysis\" /Y /Q
xcopy "Statistical Analysis\*.xlsx" "statistical_analysis\data\" /Y /Q
xcopy "Statistical Analysis\*.txt" "statistical_analysis\" /Y /Q
xcopy "Statistical Analysis\*.md" "statistical_analysis\" /Y /Q
xcopy "Statistical Analysis\*.html" "statistical_analysis\" /Y /Q
xcopy "Statistical Analysis\*.bat" "statistical_analysis\" /Y /Q
REM Move temp/debug scripts
move "Statistical Analysis\debug_*.py" "statistical_analysis\temp\" >nul 2>&1
move "Statistical Analysis\peek_*.py" "statistical_analysis\temp\" >nul 2>&1
move "Statistical Analysis\create_delta_folders.py" "statistical_analysis\temp\" >nul 2>&1
echo Statistical Analysis files moved.

REM Stage 4: Copy Statistical Database
echo [Stage 4] Statistical Database...
if not exist "statistical_analysis\database" mkdir "statistical_analysis\database"
copy "database\malaysia_swimming.db" "statistical_analysis\database\statistical.db" >nul 2>&1
echo Database copied (will need to extract statistical tables separately).

REM Stage 5: Move Times Database Project
echo [Stage 5] Times Database Project...
REM Move src folder
xcopy "src" "times_database\src\" /E /I /Y /Q
REM Move scripts
xcopy "scripts\*" "times_database\scripts\" /E /I /Y /Q
REM Move Docker files
copy "docker-compose.yml" "times_database\" >nul 2>&1
copy "Dockerfile.*" "times_database\" >nul 2>&1
copy "requirements.txt" "times_database\" >nul 2>&1
copy "package.json" "times_database\" >nul 2>&1
copy "next.config.js" "times_database\" >nul 2>&1
copy "tsconfig.json" "times_database\" >nul 2>&1
copy "tailwind.config.js" "times_database\" >nul 2>&1
REM Move public folder if exists
if exist "public" xcopy "public" "times_database\public\" /E /I /Y /Q
REM Copy database for web app
if not exist "times_database\database" mkdir "times_database\database"
copy "database\malaysia_swimming.db" "times_database\database\malaysia_swimming.db" >nul 2>&1
echo Times Database files moved.

REM Stage 6: Move Root-level Check Scripts to temp_scripts
echo [Stage 6] Moving temporary scripts...
if exist "check_*.py" move "check_*.py" "temp_scripts\" >nul 2>&1
if exist "debug_*.py" move "debug_*.py" "temp_scripts\" >nul 2>&1
echo Temporary scripts moved.

echo.
echo ========================================
echo Migration Complete!
echo.
echo IMPORTANT: Next steps:
echo 1. Verify all files moved correctly
echo 2. Run path update scripts (will be created)
echo 3. Test database connections
echo 4. Delete old folders after verification
echo ========================================
pause




