@echo off
REM Run USA vs Canada comparison (updated to use SQLite)
cd /d "C:\Users\megan\OneDrive\Documents\Malaysia Swimming Analytics\statistical_analysis"
python scripts\compare_deltas_canada.py
echo.
echo Reports generated:
echo   - reports\Delta_Comparison_USA_vs_Canada.csv
echo   - reports\Delta_Comparison_USA_vs_Canada.html
pause




