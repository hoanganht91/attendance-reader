@echo off
echo ========================================
echo Attendance System Statistics
echo ========================================

:: Navigate to project directory
cd /d "%~dp0.."

:: Activate virtual environment
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo Warning: Virtual environment not found!
    echo Some features may not work properly.
    echo.
)

echo Loading system statistics...
echo.

:: Run statistics display
python -c "
import sys
import os
import json
from datetime import datetime, timedelta
sys.path.append('.')

try:
    from src.data_sync import DataSync
    from src.config_manager import ConfigManager
    
    print('========================================')
    print('System Overview')
    print('========================================')
    
    # Configuration info
    try:
        config = ConfigManager()
        config_summary = config.get_config_summary()
        print(f'Sync Interval: {config_summary[\"sync_interval\"]} seconds ({config_summary[\"sync_interval\"]//60} minutes)')
        print(f'Total Devices: {config_summary[\"total_devices\"]}')
        print(f'Enabled Devices: {config_summary[\"enabled_devices\"]}')
        print(f'Device Names: {', '.join(config_summary[\"device_names\"])}')
    except Exception as e:
        print(f'Configuration: Error loading - {e}')
    
    print()
    
    # Data sync statistics
    try:
        data_sync = DataSync()
        stats = data_sync.get_sync_statistics()
        
        print('========================================')
        print('Data Synchronization Statistics')
        print('========================================')
        print(f'Total Records: {stats.get(\"total_records\", 0):,}')
        print(f'Recent Records (24h): {stats.get(\"recent_records_24h\", 0):,}')
        print(f'Devices Synced: {stats.get(\"devices_synced\", 0)}')
        print(f'Data File Size: {stats.get(\"data_file_size_mb\", 0)} MB')
        print(f'Cache Size: {stats.get(\"cache_size\", 0):,} records')
        
        if stats.get('last_sync_time'):
            last_sync = datetime.fromisoformat(stats['last_sync_time'])
            time_diff = datetime.now() - last_sync
            print(f'Last Sync: {last_sync.strftime(\"%Y-%m-%d %H:%M:%S\")} ({time_diff} ago)')
        else:
            print('Last Sync: Never')
        
        print()
        
        # Last sync info per device
        sync_info = data_sync.get_last_sync_info()
        device_sync = sync_info.get('device_last_sync', {})
        
        if device_sync:
            print('========================================')
            print('Per-Device Sync Status')
            print('========================================')
            for device_id, last_sync_str in device_sync.items():
                try:
                    last_sync = datetime.fromisoformat(last_sync_str)
                    time_diff = datetime.now() - last_sync
                    print(f'{device_id}: {last_sync.strftime(\"%Y-%m-%d %H:%M:%S\")} ({time_diff} ago)')
                except:
                    print(f'{device_id}: {last_sync_str}')
            print()
        
        # Recent activity
        recent_records = data_sync.get_recent_records(24)
        if recent_records:
            print('========================================')
            print('Recent Activity (Last 24 Hours)')
            print('========================================')
            
            # Group by device
            device_activity = {}
            for record in recent_records:
                device_name = record.get('device_name', 'Unknown')
                if device_name not in device_activity:
                    device_activity[device_name] = 0
                device_activity[device_name] += 1
            
            for device_name, count in device_activity.items():
                print(f'{device_name}: {count} records')
            
            print()
            print('Latest 5 Records:')
            print('-' * 80)
            for record in recent_records[-5:]:
                timestamp = datetime.fromisoformat(record['timestamp']).strftime('%m-%d %H:%M')
                device_name = record['device_name'][:15]
                user_name = record['user_name'][:20]
                punch_type = ['In', 'Out', 'Break-Out', 'Break-In', 'OT-In', 'OT-Out'][record.get('punch_type', 0)]
                print(f'{timestamp} | {device_name:<15} | {user_name:<20} | {punch_type}')
        else:
            print('No recent activity found.')
        
        print()
        
    except Exception as e:
        print(f'Data Statistics: Error loading - {e}')
    
    # File system info
    print('========================================')
    print('File System Information')
    print('========================================')
    
    files_to_check = [
        ('Configuration', 'config/devices.yaml'),
        ('Data Records', 'data/attendance_records.txt'),
        ('Sync Tracking', 'data/last_sync.json'),
        ('Application Log', 'logs/app.log'),
        ('Service Log', 'logs/service.log')
    ]
    
    for name, filepath in files_to_check:
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            if size > 1024*1024:
                size_str = f'{size/(1024*1024):.1f} MB'
            elif size > 1024:
                size_str = f'{size/1024:.1f} KB'
            else:
                size_str = f'{size} bytes'
            
            mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
            print(f'{name}: {size_str} (modified: {mtime.strftime(\"%Y-%m-%d %H:%M:%S\")})')
        else:
            print(f'{name}: Not found')
    
    print()
    
except Exception as e:
    print(f'Error generating statistics: {e}')
    print('\\nPlease ensure:')
    print('1. System is properly initialized')
    print('2. Configuration files exist')
    print('3. Virtual environment is activated')
"

echo ========================================
echo System Management
echo ========================================
echo.
echo Available commands:
echo - scripts\test_connections.bat  - Test device connections
echo - scripts\manual_sync.bat       - Run manual synchronization
echo - scripts\service_status.bat    - Check service status
echo - scripts\start_service.bat     - Start automatic service
echo - scripts\stop_service.bat      - Stop automatic service
echo.

pause 