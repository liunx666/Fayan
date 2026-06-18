@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo ========================================
echo   Fayan - One Click Git Push
echo ========================================
echo.

git status
echo.

set /p msg=Enter commit message (press Enter for default):

if "%msg%"=="" (
    set msg=Regular update
)

echo.
echo Commit message: "%msg%"
echo.

git add .
git commit -m "%msg%"

git push

echo.
echo ========================================
echo   Done. Press any key to exit...
echo ========================================
pause >nul
exit