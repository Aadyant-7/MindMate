@echo off
setlocal
title MindMate
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\MindMate.ps1" -Mode Launch
if errorlevel 1 (
    echo.
    echo MindMate could not start. Read the error above, then try again.
    pause
    exit /b 1
)
endlocal
