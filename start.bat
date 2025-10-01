@echo off
REM Golf Tournament App - Docker Startup Script for Windows
REM This script starts the entire application using Docker

echo.
echo ========================================
echo    Tony G's Golf Tournament App
echo ========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not running!
    echo Please start Docker Desktop and try again.
    echo.
    pause
    exit /b 1
)

echo [1/3] Starting Docker containers...
docker-compose up -d

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to start containers.
    pause
    exit /b 1
)

echo.
echo [2/3] Waiting for database to be ready...
timeout /t 10 /nobreak >nul

echo.
echo [3/3] Opening web browser...
timeout /t 3 /nobreak >nul
start http://localhost:5001

echo.
echo ========================================
echo     Application is now running!
echo ========================================
echo.
echo  Main App:          http://localhost:5001
echo  Golf Calculator:   http://localhost:5001/golf_score_calculator
echo  Five Results:      http://localhost:5001/five_results
echo  Callaway Results:  http://localhost:5001/callaway_results
echo.
echo To stop the app, run: stop.bat
echo To view logs, run: docker-compose logs -f
echo.
pause
