@echo off
REM Safe Docker command runner - bypasses the 'q' prefix issue

set DOCKER_PATH="C:\Program Files\Docker\Docker\resources\bin\docker.exe"
set COMPOSE_PATH="C:\Program Files\Docker\Docker\resources\bin\docker-compose.exe"

if "%1"=="ps" (
    %DOCKER_PATH% ps
) else if "%1"=="compose" (
    %COMPOSE_PATH% %2 %3 %4 %5 %6 %7 %8 %9
) else (
    %DOCKER_PATH% %1 %2 %3 %4 %5 %6 %7 %8 %9
)

