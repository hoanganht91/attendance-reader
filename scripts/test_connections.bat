@echo off
echo ========================================
echo Testing Device Connections
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

:: Check if configuration exists
if not exist "config\devices.yaml" (
    echo Error: Configuration file not found!
    echo Please configure devices in config\devices.yaml
    pause
    exit /b 1
)

echo.
echo Testing connections to all configured devices...
echo This will attempt to connect to each device and retrieve basic information.
echo.

:: Run connection tests
python -c "
import sys
import os
sys.path.insert(0, '.')
from src.main import AttendanceSystem

system = AttendanceSystem()
if system.initialize():
    system._test_device_connections()
else:
    print('Failed to initialize system')
    sys.exit(1)
"

echo.
echo ========================================
echo Connection Test Complete
echo ========================================
echo.

if %errorLevel% equ 0 (
    echo Connection tests completed successfully!
    echo.
    echo Next steps:
    echo 1. If all devices connected: Run scripts\manual_sync.bat
    echo 2. For automatic sync: Run scripts\install_service.bat
    echo 3. Check logs in: logs\app.log for detailed information
) else (
    echo Connection tests failed!
    echo.
    echo Troubleshooting steps:
    echo 1. Verify device IP addresses in config\devices.yaml
    echo 2. Check network connectivity (ping devices)
    echo 3. Ensure devices are powered on and accessible
    echo 4. Check firewall settings
    echo 5. Verify device ports (default: 4370)
    echo.
    echo For detailed error information, check logs\app.log
)

echo.
pause 