"""
Main Application Module
Coordinates attendance data synchronization with scheduling functionality
Ensures thread-safe sequential processing of devices on main thread
"""

import time
import signal
import sys
import schedule
import threading
from datetime import datetime
from typing import List
from src.config_manager import ConfigManager
from src.attendance_reader import AttendanceReader
from src.data_sync import DataSync
from src.logger import get_logger, setup_logger


class AttendanceSystem:
    """Main attendance synchronization system - thread-safe sequential processing"""
    
    def __init__(self):
        self.logger = setup_logger()
        self.config_manager = None
        self.attendance_reader = None
        self.data_sync = None
        self.running = False
        self._shutdown_requested = False
        self._keyboard_interrupt = False
        self._main_thread_id = threading.get_ident()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        current_thread_id = threading.get_ident()
        
        if signum == signal.SIGINT:
            self._keyboard_interrupt = True
            if hasattr(self, '_signal_count'):
                self._signal_count += 1
                if self._signal_count == 1:
                    self.logger.info("Received Ctrl+C (SIGINT), initiating graceful shutdown...")
                    self.logger.info("Press Ctrl+C again within 3 seconds to force exit")
                elif self._signal_count >= 2:
                    self.logger.warning("Multiple Ctrl+C received, forcing immediate exit...")
                    # Force cleanup and exit immediately
                    try:
                        if self.attendance_reader:
                            self.attendance_reader.disconnect_all()
                    except:
                        pass
                    sys.exit(1)
            else:
                self._signal_count = 1
                self.logger.info("Received Ctrl+C (SIGINT), initiating graceful shutdown...")
                self.logger.info("Press Ctrl+C again within 3 seconds to force exit")
                
                # Set a timer to force exit if shutdown takes too long
                def force_exit():
                    time.sleep(3)
                    if self._shutdown_requested and self.running:
                        self.logger.warning("Graceful shutdown taking too long, forcing exit...")
                        sys.exit(1)
                
                timer_thread = threading.Thread(target=force_exit, daemon=True)
                timer_thread.start()
        else:
            self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        
        self._shutdown_requested = True
        self.running = False
    
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
                               device=device.name, details=message)
            else:
                self.logger.error(f"Connection test failed", 
                                device=device.name, error=message)
        
        self.logger.info(f"Connection tests completed", 
                        successful=successful_connections,
                        total=len(enabled_devices))
    
    def sync_all_devices(self) -> bool:
        """
        Synchronize data from all enabled devices sequentially on main thread
        Each device is processed one by one to ensure thread safety and proper resource management
        """
        if not self.config_manager:
            self.logger.error("System not initialized")
            return False
        
        # Check for shutdown request before starting
        if self._shutdown_requested or self._keyboard_interrupt:
            self.logger.info("Shutdown requested, skipping sync operation")
            return False
        
        enabled_devices = self.config_manager.get_enabled_devices()
        if not enabled_devices:
            self.logger.warning("No enabled devices to sync")
            return True
        
        self.logger.info(f"Starting sequential sync operation for {len(enabled_devices)} devices")
        sync_start_time = time.time()
        
        total_new_records = 0
        successful_syncs = 0
        failed_devices = []
        
        # Process each device sequentially on main thread
        for device_index, device in enumerate(enabled_devices, 1):
            # Check for shutdown request before each device
            if self._shutdown_requested or self._keyboard_interrupt:
                self.logger.info(f"Shutdown requested during sync, stopping at device {device_index}/{len(enabled_devices)}")
                break
            
            device_start_time = time.time()
            
            self.logger.info(f"Processing device {device_index}/{len(enabled_devices)}", 
                           device=device.name,
                           device_id=device.device_id,
                           ip=device.ip)
            
            try:
                # Check shutdown request again before expensive operations
                if self._shutdown_requested or self._keyboard_interrupt:
                    self.logger.info("Shutdown requested, skipping current device")
                    break
                
                # Get last sync time for this device
                last_sync_time = self.data_sync.get_device_last_sync_time(device.device_id)
                
                self.logger.info(f"Starting sync for device", 
                               device=device.name,
                               last_sync=last_sync_time.isoformat() if last_sync_time else "Never")
                
                # Ensure clean connection state before sync (with interrupt check)
                if not self._ensure_clean_device_connection(device):
                    if self._shutdown_requested or self._keyboard_interrupt:
                        break
                    # Continue to next device if connection fails
                    continue
                
                # Check again before getting records
                if self._shutdown_requested or self._keyboard_interrupt:
                    break
                
                # Get attendance records from device
                records = self.attendance_reader.get_attendance_records(device, last_sync_time)
                
                # Check again before saving
                if self._shutdown_requested or self._keyboard_interrupt:
                    break
                
                if records:
                    # Save records to local storage
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
                else:
                    device_duration = time.time() - device_start_time
                    self.logger.info(f"No new records found for device", 
                                   device=device.name,
                                   duration_sec=round(device_duration, 2))
                    successful_syncs += 1
                
                # Cleanup device connection after sync to free resources
                self._cleanup_device_connection(device)
                
            except KeyboardInterrupt:
                # Handle Ctrl+C explicitly
                self.logger.info("Keyboard interrupt received during device sync")
                self._keyboard_interrupt = True
                self._shutdown_requested = True
                break
                
            except Exception as e:
                device_duration = time.time() - device_start_time
                failed_devices.append({
                    'device': device.name,
                    'error': str(e)
                })
                
                self.logger.log_sync_operation(
                    device.name,
                    0,
                    device_duration,
                    success=False,
                    error_msg=str(e)
                )
                
                # Ensure cleanup even on error
                try:
                    self._cleanup_device_connection(device)
                except Exception as cleanup_error:
                    self.logger.warning(f"Error during device cleanup", 
                                      device=device.name, 
                                      exception=cleanup_error)
            
            # Check for shutdown before delay
            if self._shutdown_requested or self._keyboard_interrupt:
                break
            
            # Small delay between devices to prevent resource conflicts
            if device_index < len(enabled_devices):
                # Use interruptible sleep
                for _ in range(5):  # 5 * 0.1 = 0.5 seconds
                    if self._shutdown_requested or self._keyboard_interrupt:
                        break
                    time.sleep(0.1)
        
        # Skip cleanup if shutdown requested
        if not (self._shutdown_requested or self._keyboard_interrupt):
            # Perform data cleanup based on retention policy
            self._perform_data_cleanup()
        
        total_duration = time.time() - sync_start_time
        
        # Log comprehensive sync summary
        if self._shutdown_requested or self._keyboard_interrupt:
            self.logger.info(f"Sync operation interrupted",
                            processed_devices=device_index if 'device_index' in locals() else 0,
                            successful_devices=successful_syncs,
                            total_devices=len(enabled_devices),
                            new_records=total_new_records,
                            duration_sec=round(total_duration, 2))
        else:
            self.logger.info(f"Sequential sync operation completed",
                            successful_devices=successful_syncs,
                            failed_devices=len(failed_devices),
                            total_devices=len(enabled_devices),
                            new_records=total_new_records,
                            duration_sec=round(total_duration, 2))
        
        # Log failed devices if any
        if failed_devices:
            self.logger.warning(f"Failed to sync {len(failed_devices)} devices", 
                              failed_devices=[f"{d['device']}: {d['error']}" for d in failed_devices])
        
        return successful_syncs > 0
    
    def _ensure_clean_device_connection(self, device) -> bool:
        """Ensure device has a clean connection state before sync"""
        try:
            # Check for shutdown request
            if self._shutdown_requested or self._keyboard_interrupt:
                return False
            
            # Test connection first
            success, message = self.attendance_reader.test_connection(device)
            if not success:
                self.logger.warning(f"Device connection test failed, will retry during sync", 
                                  device=device.name, details=message)
            return success
        except KeyboardInterrupt:
            self._keyboard_interrupt = True
            self._shutdown_requested = True
            return False
        except Exception as e:
            self.logger.warning(f"Error testing device connection", 
                              device=device.name, exception=e)
            return False
    
    def _cleanup_device_connection(self, device) -> None:
        """Clean up device connection to free resources"""
        try:
            if hasattr(self.attendance_reader, 'disconnect_device'):
                self.attendance_reader.disconnect_device(device.device_id)
            self.logger.debug(f"Cleaned up connection for device", device=device.name)
        except Exception as e:
            self.logger.debug(f"Error cleaning up device connection", 
                            device=device.name, exception=e)
    
    def _perform_data_cleanup(self) -> None:
        """Perform data cleanup based on retention policy"""
        try:
            retention_days = self.config_manager.settings.data_retention_days
            removed_records = self.data_sync.cleanup_old_records(retention_days)
            if removed_records > 0:
                self.logger.info(f"Cleaned up old records", 
                               removed=removed_records,
                               retention_days=retention_days)
        except Exception as e:
            self.logger.error("Error during data cleanup", exception=e)
    
    def run_once(self) -> bool:
        """Run synchronization once with keyboard interrupt support"""
        try:
            if not self.initialize():
                return False
            
            # Check for early shutdown
            if self._shutdown_requested or self._keyboard_interrupt:
                self.logger.info("Shutdown requested before sync")
                return False
            
            success = self.sync_all_devices()
            return success
            
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received in run_once")
            self._keyboard_interrupt = True
            return False
        except Exception as e:
            self.logger.error("Unexpected error in run_once", exception=e)
            return False
        finally:
            self.cleanup()
    
    def run_scheduler(self) -> None:
        """Run with scheduler for periodic synchronization on main thread"""
        try:
            if not self.initialize():
                sys.exit(1)
            
            # Schedule sync operations
            sync_interval_minutes = self.config_manager.settings.sync_interval // 60
            
            # Wrap sync method to handle exceptions in scheduler
            def safe_sync_all_devices():
                """Thread-safe wrapper for sync operation"""
                try:
                    # Check for shutdown before sync
                    if self._shutdown_requested or self._keyboard_interrupt:
                        self.logger.info("Shutdown requested, skipping scheduled sync")
                        return
                    
                    self.logger.info("Starting scheduled sync operation")
                    success = self.sync_all_devices()
                    if success:
                        self.logger.info("Scheduled sync completed successfully")
                    else:
                        self.logger.warning("Scheduled sync completed with some failures")
                except KeyboardInterrupt:
                    self.logger.info("Keyboard interrupt during scheduled sync")
                    self._keyboard_interrupt = True
                    self._shutdown_requested = True
                except Exception as e:
                    self.logger.error("Error during scheduled sync operation", exception=e)
                    # Ensure connections are cleaned up on error
                    try:
                        if self.attendance_reader:
                            self.attendance_reader.disconnect_all()
                    except Exception as cleanup_error:
                        self.logger.warning("Error cleaning up connections after sync failure", 
                                          exception=cleanup_error)
            
            # Wrap daily maintenance to handle exceptions
            def safe_daily_maintenance():
                """Thread-safe wrapper for daily maintenance"""
                try:
                    if self._shutdown_requested or self._keyboard_interrupt:
                        return
                    self._daily_maintenance()
                except KeyboardInterrupt:
                    self.logger.info("Keyboard interrupt during daily maintenance")
                    self._keyboard_interrupt = True
                    self._shutdown_requested = True
                except Exception as e:
                    self.logger.error("Error during scheduled daily maintenance", exception=e)
            
            # Schedule operations with safe wrappers
            schedule.every(sync_interval_minutes).minutes.do(safe_sync_all_devices)
            schedule.every().day.at("00:00").do(safe_daily_maintenance)
            
            self.logger.info(f"Scheduler started on main thread",
                            sync_interval_minutes=sync_interval_minutes,
                            next_sync=schedule.jobs[0].next_run.isoformat() if schedule.jobs else "Unknown")
            
            self.running = True
            
            # Run initial sync
            try:
                self.logger.info("Performing initial sync on startup")
                safe_sync_all_devices()
            except KeyboardInterrupt:
                self.logger.info("Keyboard interrupt during initial sync")
                self._keyboard_interrupt = True
                self.running = False
            except Exception as e:
                self.logger.error("Error during initial sync", exception=e)
            
            # Main scheduler loop - runs on main thread
            try:
                while self.running and not self._shutdown_requested and not self._keyboard_interrupt:
                    # Check and run pending scheduled jobs
                    schedule.run_pending()
                    
                    # Sleep for 30 seconds to reduce CPU usage while maintaining responsiveness
                    # Use shorter sleep intervals to check for shutdown more frequently
                    for _ in range(6):  # 6 * 5 = 30 seconds total
                        if self._shutdown_requested or self._keyboard_interrupt:
                            break
                        time.sleep(5)
                    
                    # Log scheduler status every hour
                    if hasattr(self, '_last_status_log'):
                        if time.time() - self._last_status_log > 3600:  # 1 hour
                            self._log_scheduler_status()
                            self._last_status_log = time.time()
                    else:
                        self._last_status_log = time.time()
                        
            except KeyboardInterrupt:
                self.logger.info("Received keyboard interrupt, shutting down gracefully")
                self._keyboard_interrupt = True
            except Exception as e:
                self.logger.critical("Critical error in scheduler main loop", exception=e)
            
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received during initialization")
            self._keyboard_interrupt = True
        except Exception as e:
            self.logger.critical("Critical error in run_scheduler", exception=e)
        finally:
            self.stop()
    
    def _log_scheduler_status(self) -> None:
        """Log current scheduler status and system health"""
        try:
            active_jobs = len(schedule.jobs)
            next_run = schedule.jobs[0].next_run.isoformat() if schedule.jobs else "No jobs scheduled"
            
            # Get connection status
            connection_status = {}
            if self.attendance_reader:
                connection_status = self.attendance_reader.get_connection_status()
            
            self.logger.info("Scheduler status update",
                           active_jobs=active_jobs,
                           next_run=next_run,
                           running=self.running,
                           active_connections=len([k for k, v in connection_status.items() if v]))
            
        except Exception as e:
            self.logger.warning("Error logging scheduler status", exception=e)

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
        """Clean up resources and ensure proper shutdown"""
        cleanup_start_time = time.time()
        self.logger.info("Starting system cleanup")
        
        try:
            # Clear any pending scheduled jobs to prevent execution during shutdown
            if schedule.jobs:
                schedule.clear()
                self.logger.debug("Cleared scheduled jobs")
            
            # Disconnect from all devices with timeout
            if self.attendance_reader:
                try:
                    self.attendance_reader.disconnect_all()
                    self.logger.info("Disconnected from all attendance devices")
                except Exception as e:
                    self.logger.warning("Error disconnecting from devices during cleanup", exception=e)
            
            # Perform final data cleanup if needed
            if self.data_sync and self.config_manager:
                try:
                    # Get final statistics before shutdown
                    stats = self.data_sync.get_sync_statistics()
                    self.logger.info("Final system statistics", **stats)
                except Exception as e:
                    self.logger.warning("Error getting final statistics", exception=e)
            
            cleanup_duration = time.time() - cleanup_start_time
            self.logger.info(f"System cleanup completed", 
                           duration_sec=round(cleanup_duration, 2))
            
        except Exception as e:
            self.logger.error("Error during system cleanup", exception=e)
        
        finally:
            # Ensure all resources are released
            self.attendance_reader = None
            self.data_sync = None
            self.config_manager = None
    
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