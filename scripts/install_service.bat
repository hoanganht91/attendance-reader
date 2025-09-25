@echo off
echo ========================================
echo Installing Attendance System Service
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
    echo Error: Virtual environment not found!
    echo Please run setup_environment.bat first.
    pause
    exit /b 1
)

:: Install the service
echo Installing Windows service...
python -c "from src.windows_service import install_service; install_service()"

if %errorLevel% equ 0 (
    echo.
    echo ========================================
    echo Service installed successfully!
    echo ========================================
    echo.
    echo Service Name: AttendanceSystem
    echo Display Name: Attendance Data Synchronization Service
    echo.
    echo Next steps:
    echo 1. Configure devices in config\devices.yaml
    echo 2. Run scripts\start_service.bat to start the service
    echo 3. Check logs in logs\service.log for service status
    echo.
    echo You can also manage the service using:
    echo - Windows Services (services.msc)
    echo - scripts\start_service.bat
    echo - scripts\stop_service.bat
    echo - scripts\uninstall_service.bat
    echo.
) else (
    echo.
    echo ========================================
    echo Service installation failed!
    echo ========================================
    echo.
    echo Please check:
    echo 1. You are running as Administrator
    echo 2. Python virtual environment is properly set up
    echo 3. All dependencies are installed
    echo.
)

pause 