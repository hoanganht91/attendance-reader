@echo off
echo ========================================
echo Stopping Attendance System Service
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
    call venv\Scripts\activate.bat
) else (
    echo Warning: Virtual environment not found!
)

:: Stop the service
echo Stopping Windows service...
python -c "from src.windows_service import stop_service; stop_service()"

if %errorLevel% equ 0 (
    echo.
    echo ========================================
    echo Service stopped successfully!
    echo ========================================
    echo.
    echo The Attendance System service has been stopped.
    echo.
    echo You can:
    echo - Start service again: scripts\start_service.bat
    echo - Check service status: scripts\service_status.bat
    echo - View logs: logs\service.log and logs\app.log
    echo - Uninstall service: scripts\uninstall_service.bat
    echo.
) else (
    echo.
    echo ========================================
    echo Failed to stop service!
    echo ========================================
    echo.
    echo Possible issues:
    echo 1. Service not installed or not running
    echo 2. Service is busy processing data
    echo 3. Permission problems
    echo.
    echo You can also try:
    echo - Windows Services (services.msc)
    echo - Task Manager to end the process
    echo - Restart the computer if service is stuck
    echo.
)

pause 