"""
Windows Service Module
Provides Windows Service functionality for the attendance system
"""

import sys
import time
import servicemanager
import win32event
import win32service
import win32serviceutil
from src.main import AttendanceSystem
from src.logger import setup_logger


class AttendanceWindowsService(win32serviceutil.ServiceFramework):
    """Windows Service wrapper for the Attendance System"""
    
    _svc_name_ = "AttendanceSystem"
    _svc_display_name_ = "Attendance Data Synchronization Service"
    _svc_description_ = "Automatically synchronizes attendance data from ZKTeco devices"
    _svc_deps_ = None  # Dependencies
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.attendance_system = None
        self.logger = None
    
    def SvcStop(self):
        """Handle service stop request"""
        try:
            if self.logger:
                self.logger.log_service_event("STOP", "Service stop requested")
            
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            
            # Stop the attendance system
            if self.attendance_system:
                self.attendance_system.stop()
            
            # Signal the main thread to stop
            win32event.SetEvent(self.hWaitStop)
            
            if self.logger:
                self.logger.log_service_event("STOP", "Service stopped successfully")
                
        except Exception as e:
            if self.logger:
                self.logger.error("Error stopping service", exception=e)
            # Log to Windows Event Log as fallback
            servicemanager.LogErrorMsg(f"Error stopping service: {str(e)}")
    
    def SvcDoRun(self):
        """Main service execution"""
        try:
            # Setup logging for service
            self.logger = setup_logger(log_file="logs/service.log", log_level="INFO")
            self.logger.log_service_event("START", "Service starting")
            
            # Log service start to Windows Event Log
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_, '')
            )
            
            # Initialize attendance system
            self.attendance_system = AttendanceSystem()
            
            # Start the system in a separate thread-like manner
            self._run_attendance_system()
            
        except Exception as e:
            error_msg = f"Service execution error: {str(e)}"
            if self.logger:
                self.logger.critical("Service execution failed", exception=e)
            
            # Log to Windows Event Log
            servicemanager.LogErrorMsg(error_msg)
            
            # Stop the service
            self.SvcStop()
    
    def _run_attendance_system(self):
        """Run the attendance system with service integration"""
        try:
            # Initialize the system
            if not self.attendance_system.initialize():
                raise Exception("Failed to initialize attendance system")
            
            self.logger.log_service_event("INITIALIZED", "System initialized successfully")
            
            # Setup scheduler
            import schedule
            from datetime import datetime
            
            sync_interval_minutes = self.attendance_system.config_manager.settings.sync_interval // 60
            schedule.every(sync_interval_minutes).minutes.do(self.attendance_system.sync_all_devices)
            schedule.every().day.at("00:00").do(self._daily_maintenance)
            
            self.logger.log_service_event("SCHEDULER", f"Scheduler configured with {sync_interval_minutes} minute intervals")
            
            # Run initial sync
            self.attendance_system.sync_all_devices()
            
            # Main service loop
            while True:
                # Check if service should stop
                if win32event.WaitForSingleObject(self.hWaitStop, 0) == win32event.WAIT_OBJECT_0:
                    break
                
                # Run scheduled tasks
                schedule.run_pending()
                
                # Wait for 60 seconds or until stop signal
                if win32event.WaitForSingleObject(self.hWaitStop, 60000) == win32event.WAIT_OBJECT_0:
                    break
            
            self.logger.log_service_event("STOP", "Service main loop ended")
            
        except Exception as e:
            error_msg = f"Error in service main loop: {str(e)}"
            if self.logger:
                self.logger.critical("Service main loop error", exception=e)
            servicemanager.LogErrorMsg(error_msg)
            raise
        
        finally:
            # Cleanup
            if self.attendance_system:
                self.attendance_system.cleanup()
    
    def _daily_maintenance(self):
        """Perform daily maintenance tasks"""
        try:
            if self.attendance_system:
                self.attendance_system._daily_maintenance()
            self.logger.log_service_event("MAINTENANCE", "Daily maintenance completed")
        except Exception as e:
            self.logger.error("Error during daily maintenance", exception=e)


def install_service():
    """Install the Windows service"""
    try:
        win32serviceutil.InstallService(
            AttendanceWindowsService,
            AttendanceWindowsService._svc_name_,
            AttendanceWindowsService._svc_display_name_,
            description=AttendanceWindowsService._svc_description_
        )
        print(f"Service '{AttendanceWindowsService._svc_display_name_}' installed successfully")
        
        # Set service to start automatically
        import win32service
        import win32con
        
        hscm = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ALL_ACCESS)
        try:
            hs = win32service.OpenService(hscm, AttendanceWindowsService._svc_name_, win32service.SERVICE_ALL_ACCESS)
            try:
                win32service.ChangeServiceConfig(
                    hs,
                    win32service.SERVICE_NO_CHANGE,
                    win32service.SERVICE_AUTO_START,  # Auto start
                    win32service.SERVICE_NO_CHANGE,
                    None, None, None, None, None, None, None
                )
                print("Service configured for automatic startup")
            finally:
                win32service.CloseServiceHandle(hs)
        finally:
            win32service.CloseServiceHandle(hscm)
            
    except Exception as e:
        print(f"Error installing service: {e}")
        return False
    
    return True


def uninstall_service():
    """Uninstall the Windows service"""
    try:
        win32serviceutil.RemoveService(AttendanceWindowsService._svc_name_)
        print(f"Service '{AttendanceWindowsService._svc_display_name_}' uninstalled successfully")
    except Exception as e:
        print(f"Error uninstalling service: {e}")
        return False
    
    return True


def start_service():
    """Start the Windows service"""
    try:
        win32serviceutil.StartService(AttendanceWindowsService._svc_name_)
        print(f"Service '{AttendanceWindowsService._svc_display_name_}' started successfully")
    except Exception as e:
        print(f"Error starting service: {e}")
        return False
    
    return True


def stop_service():
    """Stop the Windows service"""
    try:
        win32serviceutil.StopService(AttendanceWindowsService._svc_name_)
        print(f"Service '{AttendanceWindowsService._svc_display_name_}' stopped successfully")
    except Exception as e:
        print(f"Error stopping service: {e}")
        return False
    
    return True


def restart_service():
    """Restart the Windows service"""
    try:
        win32serviceutil.RestartService(AttendanceWindowsService._svc_name_)
        print(f"Service '{AttendanceWindowsService._svc_display_name_}' restarted successfully")
    except Exception as e:
        print(f"Error restarting service: {e}")
        return False
    
    return True


def get_service_status():
    """Get current service status"""
    try:
        import win32service
        
        hscm = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_CONNECT)
        try:
            hs = win32service.OpenService(hscm, AttendanceWindowsService._svc_name_, win32service.SERVICE_QUERY_STATUS)
            try:
                status = win32service.QueryServiceStatusEx(hs)
                
                state_names = {
                    win32service.SERVICE_STOPPED: "Stopped",
                    win32service.SERVICE_START_PENDING: "Start Pending",
                    win32service.SERVICE_STOP_PENDING: "Stop Pending",
                    win32service.SERVICE_RUNNING: "Running",
                    win32service.SERVICE_CONTINUE_PENDING: "Continue Pending",
                    win32service.SERVICE_PAUSE_PENDING: "Pause Pending",
                    win32service.SERVICE_PAUSED: "Paused"
                }
                
                return {
                    'state': state_names.get(status['CurrentState'], f"Unknown ({status['CurrentState']})"),
                    'pid': status.get('ProcessId', 0),
                    'controls_accepted': status.get('ControlsAccepted', 0)
                }
            finally:
                win32service.CloseServiceHandle(hs)
        finally:
            win32service.CloseServiceHandle(hscm)
            
    except Exception as e:
        return {'error': str(e)}


if __name__ == '__main__':
    if len(sys.argv) == 1:
        # Run as service
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(AttendanceWindowsService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        # Handle command line arguments
        win32serviceutil.HandleCommandLine(AttendanceWindowsService) 