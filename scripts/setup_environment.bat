@echo off
echo ========================================
echo Attendance System - Environment Setup
echo ========================================

:: Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Error: This script must be run as Administrator!
    echo Right-click and select "Run as administrator"
    pause
    exit /b 1
)

:: Check if Python is installed
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Python not found. Installing Python 3.11...
    :: Download and install Python (you may need to update this URL)
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.6/python-3.11.6-amd64.exe' -OutFile 'python-installer.exe'"
    python-installer.exe /quiet InstallAllUsers=1 PrependPath=1
    del python-installer.exe
    echo Python installation completed. Please restart this script.
    pause
    exit /b 0
)

echo Python found: 
python --version

:: Create virtual environment
echo Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo Virtual environment created successfully.
) else (
    echo Virtual environment already exists.
)

:: Activate virtual environment and install requirements
echo Activating virtual environment and installing dependencies...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ========================================
echo Environment setup completed successfully!
echo ========================================
echo.
echo Next steps:
echo 1. Configure devices in config\devices.yaml
echo 2. Run scripts\install_service.bat to install Windows service
echo 3. Run scripts\start_service.bat to start the service
echo.
pause 