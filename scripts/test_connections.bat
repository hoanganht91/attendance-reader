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
sys.path.append('.')
from src.main import AttendanceSystem

system = AttendanceSystem()
print('Initializing system...')

try:
    # Initialize system components
    if not system.initialize():
        print('Failed to initialize system!')
        sys.exit(1)
    
    print('\\n========================================')
    print('Device Connection Test Results')
    print('========================================\\n')
    
    enabled_devices = system.config_manager.get_enabled_devices()
    
    if not enabled_devices:
        print('No enabled devices found in configuration.')
        sys.exit(1)
    
    success_count = 0
    total_count = len(enabled_devices)
    
    for i, device in enumerate(enabled_devices, 1):
        print(f'[{i}/{total_count}] Testing device: {device.name}')
        print(f'    IP: {device.ip}:{device.port}')
        print(f'    Device ID: {device.device_id}')
        
        # Test connection
        success, message = system.attendance_reader.test_connection(device)
        
        if success:
            print(f'    Status: ✓ CONNECTED')
            print(f'    Details: {message}')
            success_count += 1
            
            # Get additional device info
            try:
                info = system.attendance_reader.get_device_info(device)
                if info.get('connected'):
                    print(f'    Firmware: {info.get(\"firmware_version\", \"N/A\")}')
                    print(f'    Serial: {info.get(\"serialnumber\", \"N/A\")}')
                    print(f'    Users: {info.get(\"user_count\", 0)}')
                    print(f'    Records: {info.get(\"attendance_count\", 0)}')
            except Exception as e:
                print(f'    Warning: Could not get detailed info: {e}')
        else:
            print(f'    Status: ✗ FAILED')
            print(f'    Error: {message}')
        
        print()  # Empty line between devices
    
    print('========================================')
    print('Connection Test Summary')
    print('========================================')
    print(f'Successful connections: {success_count}/{total_count}')
    print(f'Failed connections: {total_count - success_count}/{total_count}')
    
    if success_count == total_count:
        print('\\n✓ All devices connected successfully!')
        print('You can now run manual sync or install the service.')
    elif success_count > 0:
        print(f'\\n⚠ {success_count} device(s) connected, {total_count - success_count} failed.')
        print('Please check the failed devices and fix connectivity issues.')
    else:
        print('\\n✗ No devices could be connected!')
        print('Please check your network configuration and device settings.')
        sys.exit(1)

except Exception as e:
    print(f'\\nError during connection test: {e}')
    print('\\nPlease check:')
    print('1. Configuration file: config\\\\devices.yaml')
    print('2. Network connectivity')
    print('3. Device IP addresses and ports')
    print('4. Log files: logs\\\\app.log')
    sys.exit(1)

finally:
    if system.attendance_reader:
        system.attendance_reader.disconnect_all()
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