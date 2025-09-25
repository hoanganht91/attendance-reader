@echo off
echo ========================================
echo Running Attendance System Unit Tests
echo ========================================

:: Navigate to project directory
cd /d "%~dp0.."

:: Activate virtual environment
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo Error: Virtual environment not found!
    echo Please run setup_environment.bat first.
    pause
    exit /b 1
)

echo.
echo Running unit tests...
echo.

:: Run tests
python -m pytest tests/ -v --tb=short

if %errorLevel% equ 0 (
    echo.
    echo ========================================
    echo All tests passed successfully!
    echo ========================================
) else (
    echo.
    echo ========================================
    echo Some tests failed!
    echo ========================================
    echo Please check the error messages above.
)

echo.
pause 