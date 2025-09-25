"""
Logger Module
Provides centralized logging functionality for the attendance system
"""

import logging
import logging.handlers
import os
from datetime import datetime
from typing import Optional
from colorama import init, Fore, Back, Style

# Initialize colorama for Windows console colors
init(autoreset=True)


class ColoredFormatter(logging.Formatter):
    """Custom formatter to add colors to console output"""
    
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Back.YELLOW + Style.BRIGHT,
    }
    
    def format(self, record):
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{Style.RESET_ALL}"
        
        return super().format(record)


class AttendanceLogger:
    """Centralized logger for the attendance system"""
    
    def __init__(self, 
                 name: str = "AttendanceSystem",
                 log_file: str = "logs/app.log",
                 log_level: str = "INFO",
                 max_file_size: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5):
        
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, 
            maxBytes=max_file_size, 
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler with colors
        console_handler = logging.StreamHandler()
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message"""
        self.logger.debug(self._format_message(message, **kwargs))
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message"""
        self.logger.info(self._format_message(message, **kwargs))
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message"""
        self.logger.warning(self._format_message(message, **kwargs))
    
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs) -> None:
        """Log error message with optional exception details"""
        formatted_message = self._format_message(message, **kwargs)
        if exception:
            formatted_message += f" | Exception: {str(exception)}"
        self.logger.error(formatted_message)
    
    def critical(self, message: str, exception: Optional[Exception] = None, **kwargs) -> None:
        """Log critical message with optional exception details"""
        formatted_message = self._format_message(message, **kwargs)
        if exception:
            formatted_message += f" | Exception: {str(exception)}"
        self.logger.critical(formatted_message)
    
    def _format_message(self, message: str, **kwargs) -> str:
        """Format message with additional context"""
        if kwargs:
            context_parts = [f"{key}={value}" for key, value in kwargs.items()]
            return f"{message} | {' | '.join(context_parts)}"
        return message
    
    def log_system_start(self, version: str = "1.0.0") -> None:
        """Log system startup"""
        self.info("=" * 60)
        self.info(f"Attendance System Started - Version {version}")
        self.info(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.info("=" * 60)
    
    def log_system_stop(self) -> None:
        """Log system shutdown"""
        self.info("=" * 60)
        self.info("Attendance System Stopped")
        self.info(f"Stop Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.info("=" * 60)
    
    def log_device_connection(self, device_name: str, device_ip: str, success: bool, 
                            error_msg: str = None) -> None:
        """Log device connection attempt"""
        if success:
            self.info("Device connected successfully", 
                     device=device_name, ip=device_ip)
        else:
            self.error("Device connection failed", 
                      device=device_name, ip=device_ip, error=error_msg)
    
    def log_sync_operation(self, device_name: str, records_count: int, 
                          duration: float, success: bool, error_msg: str = None) -> None:
        """Log data synchronization operation"""
        if success:
            self.info("Data sync completed", 
                     device=device_name, records=records_count, 
                     duration_sec=round(duration, 2))
        else:
            self.error("Data sync failed", 
                      device=device_name, error=error_msg, 
                      duration_sec=round(duration, 2))
    
    def log_service_event(self, event: str, details: str = None) -> None:
        """Log Windows service events"""
        message = f"Service Event: {event}"
        if details:
            self.info(message, details=details)
        else:
            self.info(message)


# Global logger instance
_logger_instance: Optional[AttendanceLogger] = None


def get_logger() -> AttendanceLogger:
    """Get global logger instance (singleton pattern)"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = AttendanceLogger()
    return _logger_instance


def setup_logger(log_file: str = "logs/app.log", log_level: str = "INFO") -> AttendanceLogger:
    """Setup and configure global logger"""
    global _logger_instance
    _logger_instance = AttendanceLogger(log_file=log_file, log_level=log_level)
    return _logger_instance 