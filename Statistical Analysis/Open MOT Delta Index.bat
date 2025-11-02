@echo off
setlocal
set FILE="%~dp0MOT_Delta_Index.html"
if not exist %FILE% (
  echo Not found: %FILE%
  pause
  exit /b 1
)
start "" %FILE%



