"""
Attendance Reader Module
Handles communication with ZKTeco attendance devices using pyzk library
"""

import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from zk import ZK
from zk.exception import ZKError, ZKErrorConnection, ZKErrorResponse
from .config_manager import DeviceConfig
from .logger import get_logger


@dataclass
class AttendanceRecord:
    """Represents a single attendance record"""
    device_id: str
    device_name: str
    user_id: str
    user_name: str
    timestamp: datetime
    punch_type: int  # 0=Check-in, 1=Check-out, 2=Break-out, 3=Break-in, 4=OT-in, 5=OT-out
    verify_type: int  # 1=Fingerprint, 15=Face, 0=Password
    work_code: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'device_id': self.device_id,
            'device_name': self.device_name,
            'user_id': self.user_id,
            'user_name': self.user_name,
            'timestamp': self.timestamp.isoformat(),
            'punch_type': self.punch_type,
            'verify_type': self.verify_type,
            'work_code': self.work_code
        }


@dataclass
class UserInfo:
    """Represents user information from device"""
    user_id: str
    name: str
    privilege: int
    password: str = ""
    group_id: str = ""
    user_id_num: int = 0


class AttendanceReader:
    """Handles reading attendance data from ZKTeco devices"""
    
    PUNCH_TYPE_NAMES = {
        0: "Check-in",
        1: "Check-out", 
        2: "Break-out",
        3: "Break-in",
        4: "OT-in",
        5: "OT-out"
    }
    
    VERIFY_TYPE_NAMES = {
        0: "Password",
        1: "Fingerprint",
        15: "Face",
        4: "Card"
    }
    
    def __init__(self):
        self.logger = get_logger()
        self._connections = {}  # Cache connections
    
    def connect_device(self, device_config: DeviceConfig, timeout: int = 30) -> bool:
        """
        Connect to a ZKTeco device
        
        Args:
            device_config: Device configuration
            timeout: Connection timeout in seconds
            
        Returns:
            bool: True if connection successful
        """
        try:
            self.logger.info(f"Connecting to device", 
                           device=device_config.name, 
                           ip=device_config.ip, 
                           port=device_config.port)
            
            # Create ZK connection
            zk = ZK(device_config.ip, port=device_config.port, timeout=timeout)
            conn = zk.connect()
            
            if conn:
                # Test connection with a simple command
                conn.get_time()
                
                # Store connection
                self._connections[device_config.device_id] = conn
                
                self.logger.log_device_connection(
                    device_config.name, 
                    device_config.ip, 
                    success=True
                )
                return True
            else:
                raise ZKErrorConnection("Failed to establish connection")
                
        except Exception as e:
            self.logger.log_device_connection(
                device_config.name, 
                device_config.ip, 
                success=False, 
                error_msg=str(e)
            )
            return False
    
    def disconnect_device(self, device_id: str) -> None:
        """Disconnect from device"""
        try:
            if device_id in self._connections:
                conn = self._connections[device_id]
                conn.disconnect()
                del self._connections[device_id]
                self.logger.debug(f"Disconnected from device", device_id=device_id)
        except Exception as e:
            self.logger.error(f"Error disconnecting from device", 
                            device_id=device_id, exception=e)
    
    def disconnect_all(self) -> None:
        """Disconnect from all devices"""
        device_ids = list(self._connections.keys())
        for device_id in device_ids:
            self.disconnect_device(device_id)
    
    def get_users(self, device_config: DeviceConfig) -> List[UserInfo]:
        """
        Get all users from device
        
        Args:
            device_config: Device configuration
            
        Returns:
            List of UserInfo objects
        """
        users = []
        
        try:
            conn = self._connections.get(device_config.device_id)
            if not conn:
                if not self.connect_device(device_config):
                    return users
                conn = self._connections[device_config.device_id]
            
            # Get users from device
            device_users = conn.get_users()
            
            for user in device_users:
                user_info = UserInfo(
                    user_id=str(user.user_id),
                    name=user.name or f"User_{user.user_id}",
                    privilege=user.privilege,
                    password=user.password or "",
                    group_id=str(user.group_id) if user.group_id else "",
                    user_id_num=user.user_id
                )
                users.append(user_info)
            
            self.logger.info(f"Retrieved users from device", 
                           device=device_config.name, 
                           user_count=len(users))
            
        except Exception as e:
            self.logger.error(f"Error getting users from device", 
                            device=device_config.name, exception=e)
        
        return users
    
    def get_attendance_records(self, device_config: DeviceConfig, 
                             last_sync_time: Optional[datetime] = None) -> List[AttendanceRecord]:
        """
        Get attendance records from device
        
        Args:
            device_config: Device configuration
            last_sync_time: Only get records after this time
            
        Returns:
            List of AttendanceRecord objects
        """
        records = []
        
        try:
            conn = self._connections.get(device_config.device_id)
            if not conn:
                if not self.connect_device(device_config):
                    return records
                conn = self._connections[device_config.device_id]
            
            # Get attendance records
            attendances = conn.get_attendance()
            
            # Get user information for name mapping
            users_dict = {}
            try:
                users = self.get_users(device_config)
                users_dict = {user.user_id: user.name for user in users}
            except Exception as e:
                self.logger.warning(f"Could not get user names", 
                                  device=device_config.name, exception=e)
            
            # Process attendance records
            for attendance in attendances:
                # Skip records before last sync time if specified
                if last_sync_time and attendance.timestamp <= last_sync_time:
                    continue
                
                # Get user name from users dict or use user_id
                user_name = users_dict.get(str(attendance.user_id), f"User_{attendance.user_id}")
                
                record = AttendanceRecord(
                    device_id=device_config.device_id,
                    device_name=device_config.name,
                    user_id=str(attendance.user_id),
                    user_name=user_name,
                    timestamp=attendance.timestamp,
                    punch_type=attendance.punch,
                    verify_type=attendance.status,
                    work_code=getattr(attendance, 'work_code', 0)
                )
                records.append(record)
            
            self.logger.info(f"Retrieved attendance records", 
                           device=device_config.name, 
                           total_records=len(attendances),
                           new_records=len(records))
            
        except Exception as e:
            self.logger.error(f"Error getting attendance records", 
                            device=device_config.name, exception=e)
        
        return records
    
    def get_device_info(self, device_config: DeviceConfig) -> Dict[str, Any]:
        """
        Get device information and status
        
        Args:
            device_config: Device configuration
            
        Returns:
            Dictionary with device information
        """
        info = {
            'device_id': device_config.device_id,
            'name': device_config.name,
            'ip': device_config.ip,
            'port': device_config.port,
            'connected': False,
            'error': None
        }
        
        try:
            conn = self._connections.get(device_config.device_id)
            if not conn:
                if not self.connect_device(device_config):
                    info['error'] = "Connection failed"
                    return info
                conn = self._connections[device_config.device_id]
            
            info['connected'] = True
            
            # Get device information
            info['firmware_version'] = conn.get_firmware_version()
            info['serialnumber'] = conn.get_serialnumber()
            info['platform'] = conn.get_platform()
            info['device_name'] = conn.get_device_name()
            info['current_time'] = conn.get_time()
            
            # Get counts
            info['user_count'] = len(conn.get_users())
            info['attendance_count'] = len(conn.get_attendance())
            
        except Exception as e:
            info['error'] = str(e)
            self.logger.error(f"Error getting device info", 
                            device=device_config.name, exception=e)
        
        return info
    
    def test_connection(self, device_config: DeviceConfig) -> Tuple[bool, str]:
        """
        Test connection to device
        
        Args:
            device_config: Device configuration
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Try to connect
            if not self.connect_device(device_config):
                return False, "Connection failed"
            
            # Get connection
            conn = self._connections[device_config.device_id]
            
            # Test basic operations
            device_time = conn.get_time()
            user_count = len(conn.get_users())
            attendance_count = len(conn.get_attendance())
            
            message = (f"Connection successful. "
                      f"Device time: {device_time}, "
                      f"Users: {user_count}, "
                      f"Records: {attendance_count}")
            
            return True, message
            
        except Exception as e:
            return False, f"Connection test failed: {str(e)}"
        
        finally:
            # Clean up test connection
            self.disconnect_device(device_config.device_id) 