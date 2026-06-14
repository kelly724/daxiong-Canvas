@echo off
cd /d "%~dp0"

echo ============================================
echo   Build Windows Distribution Package
echo ============================================
echo.
echo This will create a clean zip in the dist folder.
echo It will not include API\.env, data, logs, or root output.
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\package_windows.ps1"

echo.
pause
