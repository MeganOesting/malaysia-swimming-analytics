@echo off
setlocal
set FILE="%~dp0reports\Delta_Comparison_USA_vs_Canada.html"
if not exist %FILE% (
  echo Not found: %FILE%
  pause
  exit /b 1
)
start "" %FILE%



