@echo off
echo ========================================
echo   Email Campaign Worker (Self-hosted)
echo   Quick Start Script
echo ========================================
echo.

REM Check if .env exists
if not exist .env (
    echo [ERROR] .env file not found!
    echo.
    echo Please create .env file from .env.example:
    echo   1. Copy .env.example to .env
    echo   2. Fill in MongoDB, backend URL, and Google credentials
    echo.
    pause
    exit /b 1
)

echo [1/3] Checking dependencies...
echo [INFO] Installing dependencies...
call npm install

echo.
echo [2/3] Verifying TypeScript compilation...
call npx tsc --noEmit
if errorlevel 1 (
    echo [ERROR] TypeScript compilation failed!
    pause
    exit /b 1
)
echo [OK] TypeScript compilation successful

echo ========================================
echo   Server Starting...
echo   Press Ctrl+C to stop
echo ========================================
echo.

echo [3/3] Starting worker server...
echo.
call npm run dev
