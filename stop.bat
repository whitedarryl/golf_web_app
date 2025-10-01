@echo off
REM Golf Tournament App - Docker Stop Script for Windows

echo.
echo Stopping Golf Tournament App...
echo.

docker-compose down

echo.
echo App stopped successfully!
echo.
pause
