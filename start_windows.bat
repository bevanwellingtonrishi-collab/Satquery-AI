@echo off
echo ============================================
echo   SATQUERY AI - Satellite Intelligence
echo ============================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.10+
    pause
    exit /b 1
)

:: Check Node
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found. Install Node.js 18+
    pause
    exit /b 1
)

echo Starting SatQuery AI...
echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo Mode: DEMO (no API key required)
echo.

:: Start backend
echo [1/2] Starting FastAPI backend...
cd backend
start /B cmd /c "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
cd ..

:: Wait for backend
timeout /t 3 /nobreak >nul

:: Start frontend
echo [2/2] Starting Next.js frontend...
cd frontend
start /B cmd /c "npm run dev"
cd ..

:: Wait and open browser
timeout /t 5 /nobreak >nul
echo.
echo Opening browser...
start http://localhost:3000

echo.
echo ============================================
echo   SatQuery AI is running!
echo   Press Ctrl+C to stop.
echo ============================================
pause
