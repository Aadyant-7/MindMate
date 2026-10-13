@echo off
setlocal
title Build MindMate
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\MindMate.ps1" -Mode Build
if errorlevel 1 (
    echo.
    echo The Windows app could not be built. Read the error above.
    pause
    exit /b 1
)
echo.
echo Finished. The application is in the dist folder.
pause
endlocal
