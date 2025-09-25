@echo off
echo ========================================
echo Attendance System Service Status
echo ========================================

:: Navigate to project directory
cd /d "%~dp0.."

:: Activate virtual environment
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo Warning: Virtual environment not found!
    echo Status check may not work properly.
    echo.
)

:: Get service status
echo Checking service status...
echo.
python -c "
from src.windows_service import get_service_status
import json
status = get_service_status()
if 'error' in status:
    print(f'Error: {status[\"error\"]}')
    print('Service may not be installed.')
else:
    print(f'Service State: {status[\"state\"]}')
    if status.get('pid', 0) > 0:
        print(f'Process ID: {status[\"pid\"]}')
    print(f'Controls Accepted: {status.get(\"controls_accepted\", \"N/A\")}')
"

echo.
echo ========================================
echo System Information
echo ========================================

:: Check if log files exist and show recent entries
if exist "logs\service.log" (
    echo Recent service log entries:
    echo.
    powershell -Command "Get-Content 'logs\service.log' -Tail 5"
    echo.
) else (
    echo No service log file found.
    echo.
)

if exist "logs\app.log" (
    echo Recent application log entries:
    echo.
    powershell -Command "Get-Content 'logs\app.log' -Tail 5"
    echo.
) else (
    echo No application log file found.
    echo.
)

:: Check data files
if exist "data\attendance_records.txt" (
    echo Data file status:
    for %%I in ("data\attendance_records.txt") do echo File size: %%~zI bytes
    echo.
) else (
    echo No data file found.
    echo.
)

if exist "data\last_sync.json" (
    echo Last sync information:
    type "data\last_sync.json"
    echo.
) else (
    echo No sync tracking file found.
    echo.
)

echo ========================================
echo Service Management Commands
echo ========================================
echo.
echo Available commands:
echo - scripts\start_service.bat    - Start the service
echo - scripts\stop_service.bat     - Stop the service
echo - scripts\install_service.bat  - Install the service
echo - scripts\uninstall_service.bat - Remove the service
echo - scripts\manual_sync.bat      - Run manual sync
echo.
echo You can also use Windows Services (services.msc) to manage the service.
echo.

pause 