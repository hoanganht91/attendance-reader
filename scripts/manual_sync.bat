@echo off
echo ========================================
echo Manual Attendance Data Synchronization
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
echo Starting manual synchronization...
echo This will connect to all enabled devices and sync attendance data.
echo.

:: Run manual sync
python -c "
import sys
sys.path.append('.')
from src.main import AttendanceSystem

system = AttendanceSystem()
print('Initializing system...')
success = system.run_once()

if success:
    print('\\n========================================')
    print('Manual synchronization completed successfully!')
    print('========================================')
    
    # Show sync statistics
    try:
        stats = system.data_sync.get_sync_statistics()
        print(f'\\nSynchronization Statistics:')
        print(f'- Total records: {stats.get(\"total_records\", 0)}')
        print(f'- Recent records (24h): {stats.get(\"recent_records_24h\", 0)}')
        print(f'- Devices synced: {stats.get(\"devices_synced\", 0)}')
        print(f'- Data file size: {stats.get(\"data_file_size_mb\", 0)} MB')
        
        if stats.get('last_sync_time'):
            print(f'- Last sync: {stats[\"last_sync_time\"]}')
    except Exception as e:
        print(f'Could not retrieve statistics: {e}')
    
    print('\\nData saved to: data\\\\attendance_records.txt')
    print('Logs available in: logs\\\\app.log')
else:
    print('\\n========================================')
    print('Manual synchronization failed!')
    print('========================================')
    print('\\nPlease check:')
    print('1. Device configuration in config\\\\devices.yaml')
    print('2. Network connectivity to devices')
    print('3. Log files in logs\\\\ directory for error details')
    sys.exit(1)
"

if %errorLevel% equ 0 (
    echo.
    echo ========================================
    echo Synchronization Summary
    echo ========================================
    echo.
    echo Manual sync completed successfully!
    echo.
    echo Next steps:
    echo 1. Review data in: data\attendance_records.txt
    echo 2. Check logs in: logs\app.log
    echo 3. Set up automatic sync: scripts\install_service.bat
    echo.
    echo You can run this script again anytime to sync manually.
    echo.
) else (
    echo.
    echo ========================================
    echo Synchronization Failed
    echo ========================================
    echo.
    echo Please check the error messages above and:
    echo 1. Verify device IP addresses and ports in config\devices.yaml
    echo 2. Test network connectivity to devices
    echo 3. Check logs\app.log for detailed error information
    echo 4. Run scripts\test_connections.bat to test individual devices
    echo.
)

pause 