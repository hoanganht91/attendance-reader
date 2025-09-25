@echo off
echo ========================================
echo Starting Attendance System Service
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
    echo The service may not start properly without proper environment.
)

:: Start the service
echo Starting Windows service...
python -c "from src.windows_service import start_service; start_service()"

if %errorLevel% equ 0 (
    echo.
    echo ========================================
    echo Service started successfully!
    echo ========================================
    echo.
    echo The Attendance System service is now running.
    echo.
    echo You can:
    echo - Check service status: scripts\service_status.bat
    echo - View logs: logs\service.log and logs\app.log
    echo - Stop service: scripts\stop_service.bat
    echo - Monitor in Windows Services (services.msc)
    echo.
    echo The service will automatically sync attendance data
    echo according to the schedule configured in config\devices.yaml
    echo.
) else (
    echo.
    echo ========================================
    echo Failed to start service!
    echo ========================================
    echo.
    echo Possible issues:
    echo 1. Service not installed - run scripts\install_service.bat
    echo 2. Configuration error - check config\devices.yaml
    echo 3. Network connectivity issues
    echo 4. Permission problems
    echo.
    echo Check the following logs for details:
    echo - logs\service.log
    echo - logs\app.log
    echo - Windows Event Viewer (Application logs)
    echo.
)

pause 