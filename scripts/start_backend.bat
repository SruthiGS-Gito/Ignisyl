@echo off
REM IGNISYL Backend Startup Script (Windows)

echo ============================================================================
echo IGNISYL Backend Server
echo ============================================================================
echo.

REM Navigate to project root
cd /d "%~dp0\.."

REM Check if virtual environment exists
if not exist "venv\" (
    echo ERROR: Virtual environment not found!
    echo Please create it first: python -m venv venv
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Verify Python
echo.
echo Python: %PYTHON%
python --version
echo.

REM Check if dependencies are installed
echo Checking dependencies...
python -c "import fastapi, uvicorn" 2>nul
if errorlevel 1 (
    echo.
    echo ERROR: Required dependencies not installed!
    echo.
    echo Please install dependencies first:
    echo   python scripts/install_dependencies.py
    echo.
    echo Or install manually:
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo Dependencies OK
echo.

REM Start backend server
echo ============================================================================
echo Starting backend server on http://127.0.0.1:8000
echo ============================================================================
echo.
echo Press CTRL+C to stop the server
echo.

cd backend
python main.py

REM If we get here, server stopped
echo.
echo Server stopped.
pause
