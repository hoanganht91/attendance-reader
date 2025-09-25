@echo off
echo ========================================
echo Uninstalling Attendance System Service
echo ========================================

:: Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Error: This script must be run as Administrator!
    echo Right-click and select "Run as administrator"
    pause
    exit /b 1
)

:: Navigate to project directory
cd /d "%~dp0.."

:: Activate virtual environment
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo Warning: Virtual environment not found!
    echo Attempting to uninstall service anyway...
)

:: Stop the service first if it's running
echo Stopping service if running...
python -c "from src.windows_service import stop_service; stop_service()" 2>nul

:: Wait a moment for service to stop
timeout /t 3 /nobreak >nul

:: Uninstall the service
echo Uninstalling Windows service...
python -c "from src.windows_service import uninstall_service; uninstall_service()"

if %errorLevel% equ 0 (
    echo.
    echo ========================================
    echo Service uninstalled successfully!
    echo ========================================
    echo.
    echo The Attendance System service has been removed from Windows.
    echo.
    echo If you want to reinstall the service later:
    echo 1. Run scripts\install_service.bat as Administrator
    echo.
) else (
    echo.
    echo ========================================
    echo Service uninstallation failed!
    echo ========================================
    echo.
    echo The service may not be installed or there was an error.
    echo You can also try manually removing it using:
    echo - Windows Services (services.msc)
    echo - sc delete AttendanceSystem
    echo.
)

pause 