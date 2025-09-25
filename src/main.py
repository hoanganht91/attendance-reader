"""
Main Application Module
Coordinates attendance data synchronization with scheduling functionality
"""

import time
import signal
import sys
import schedule
from datetime import datetime
from typing import List
from .config_manager import ConfigManager
from .attendance_reader import AttendanceReader
from .data_sync import DataSync
from .logger import get_logger, setup_logger


class AttendanceSystem:
    """Main attendance synchronization system"""
    
    def __init__(self):
        self.logger = setup_logger()
        self.config_manager = None
        self.attendance_reader = None
        self.data_sync = None
        self.running = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, initiating shutdown...")
        self.stop()
    
    def initialize(self) -> bool:
        """Initialize system components"""
        try:
            self.logger.log_system_start()
            
            # Load configuration
            self.config_manager = ConfigManager()
            config_summary = self.config_manager.get_config_summary()
            self.logger.info("Configuration loaded successfully", **config_summary)
            
            # Initialize components
            self.attendance_reader = AttendanceReader()
            self.data_sync = DataSync()
            
            # Test device connections
            self._test_device_connections()
            
            return True
            
        except Exception as e:
            self.logger.critical("Failed to initialize system", exception=e)
            return False
    
    def _test_device_connections(self) -> None:
        """Test connections to all enabled devices"""
        enabled_devices = self.config_manager.get_enabled_devices()
        
        if not enabled_devices:
            self.logger.warning("No enabled devices found in configuration")
            return
        
        self.logger.info(f"Testing connections to {len(enabled_devices)} devices...")
        
        successful_connections = 0
        for device in enabled_devices:
            success, message = self.attendance_reader.test_connection(device)
            if success:
                successful_connections += 1
                self.logger.info(f"Connection test passed", 
                               device=device.name, message=message)
            else:
                self.logger.error(f"Connection test failed", 
                                device=device.name, error=message)
        
        self.logger.info(f"Connection tests completed", 
                        successful=successful_connections,
                        total=len(enabled_devices))
    
    def sync_all_devices(self) -> bool:
        """Synchronize data from all enabled devices"""
        if not self.config_manager:
            self.logger.error("System not initialized")
            return False
        
        enabled_devices = self.config_manager.get_enabled_devices()
        if not enabled_devices:
            self.logger.warning("No enabled devices to sync")
            return True
        
        self.logger.info(f"Starting sync operation for {len(enabled_devices)} devices")
        sync_start_time = time.time()
        
        total_new_records = 0
        successful_syncs = 0
        
        for device in enabled_devices:
            try:
                # Get last sync time for this device
                last_sync_time = self.data_sync.get_device_last_sync_time(device.device_id)
                
                device_start_time = time.time()
                self.logger.info(f"Syncing device", 
                               device=device.name,
                               last_sync=last_sync_time.isoformat() if last_sync_time else "Never")
                
                # Get attendance records
                records = self.attendance_reader.get_attendance_records(device, last_sync_time)
                
                # Save records
                new_records_count = self.data_sync.save_records(records, device.device_id)
                total_new_records += new_records_count
                
                device_duration = time.time() - device_start_time
                
                self.logger.log_sync_operation(
                    device.name,
                    new_records_count,
                    device_duration,
                    success=True
                )
                
                successful_syncs += 1
                
            except Exception as e:
                device_duration = time.time() - device_start_time
                self.logger.log_sync_operation(
                    device.name,
                    0,
                    device_duration,
                    success=False,
                    error_msg=str(e)
                )
        
        # Cleanup old records based on retention policy
        try:
            retention_days = self.config_manager.settings.data_retention_days
            removed_records = self.data_sync.cleanup_old_records(retention_days)
            if removed_records > 0:
                self.logger.info(f"Cleaned up old records", 
                               removed=removed_records,
                               retention_days=retention_days)
        except Exception as e:
            self.logger.error("Error during cleanup", exception=e)
        
        total_duration = time.time() - sync_start_time
        
        self.logger.info(f"Sync operation completed",
                        successful_devices=successful_syncs,
                        total_devices=len(enabled_devices),
                        new_records=total_new_records,
                        duration_sec=round(total_duration, 2))
        
        return successful_syncs > 0
    
    def run_once(self) -> bool:
        """Run synchronization once"""
        if not self.initialize():
            return False
        
        success = self.sync_all_devices()
        self.cleanup()
        return success
    
    def run_scheduler(self) -> None:
        """Run with scheduler for periodic synchronization"""
        if not self.initialize():
            sys.exit(1)
        
        # Schedule sync operations
        sync_interval_minutes = self.config_manager.settings.sync_interval // 60
        schedule.every(sync_interval_minutes).minutes.do(self.sync_all_devices)
        
        # Schedule daily cleanup at midnight
        schedule.every().day.at("00:00").do(self._daily_maintenance)
        
        self.logger.info(f"Scheduler started",
                        sync_interval_minutes=sync_interval_minutes)
        
        self.running = True
        
        # Run initial sync
        self.sync_all_devices()
        
        # Main scheduler loop
        try:
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
        except Exception as e:
            self.logger.critical("Scheduler error", exception=e)
        finally:
            self.stop()
    
    def _daily_maintenance(self) -> None:
        """Perform daily maintenance tasks"""
        self.logger.info("Starting daily maintenance")
        
        try:
            # Log system statistics
            stats = self.data_sync.get_sync_statistics()
            self.logger.info("System statistics", **stats)
            
            # Reload configuration (in case it was updated)
            self.config_manager.reload_config()
            self.logger.info("Configuration reloaded")
            
        except Exception as e:
            self.logger.error("Error during daily maintenance", exception=e)
    
    def stop(self) -> None:
        """Stop the system gracefully"""
        self.logger.info("Stopping attendance system...")
        self.running = False
        self.cleanup()
        self.logger.log_system_stop()
    
    def cleanup(self) -> None:
        """Clean up resources"""
        try:
            if self.attendance_reader:
                self.attendance_reader.disconnect_all()
                self.logger.debug("Disconnected from all devices")
        except Exception as e:
            self.logger.error("Error during cleanup", exception=e)
    
    def get_system_status(self) -> dict:
        """Get current system status"""
        try:
            status = {
                'running': self.running,
                'initialized': self.config_manager is not None,
                'timestamp': datetime.now().isoformat()
            }
            
            if self.config_manager:
                status['config'] = self.config_manager.get_config_summary()
            
            if self.data_sync:
                status['sync_stats'] = self.data_sync.get_sync_statistics()
            
            return status
            
        except Exception as e:
            self.logger.error("Error getting system status", exception=e)
            return {'error': str(e)}


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Attendance Data Synchronization System')
    parser.add_argument('--once', action='store_true', 
                       help='Run sync once and exit')
    parser.add_argument('--test', action='store_true',
                       help='Test device connections and exit')
    parser.add_argument('--status', action='store_true',
                       help='Show system status and exit')
    parser.add_argument('--config', type=str, default='config/devices.yaml',
                       help='Configuration file path')
    parser.add_argument('--log-level', type=str, default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                       help='Logging level')
    
    args = parser.parse_args()
    
    # Setup logging with specified level
    setup_logger(log_level=args.log_level)
    
    system = AttendanceSystem()
    
    try:
        if args.test:
            # Test mode
            if system.initialize():
                system._test_device_connections()
                return 0
            else:
                return 1
                
        elif args.status:
            # Status mode
            if system.initialize():
                status = system.get_system_status()
                print("System Status:")
                for key, value in status.items():
                    print(f"  {key}: {value}")
                return 0
            else:
                return 1
                
        elif args.once:
            # Run once mode
            success = system.run_once()
            return 0 if success else 1
            
        else:
            # Scheduler mode (default)
            system.run_scheduler()
            return 0
            
    except Exception as e:
        if system.logger:
            system.logger.critical("Unhandled exception", exception=e)
        else:
            print(f"Critical error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 