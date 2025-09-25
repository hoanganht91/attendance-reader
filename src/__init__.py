"""
Attendance Data Synchronization System
======================================

A comprehensive system for synchronizing attendance data from ZKTeco devices.

Main Components:
- config_manager: Configuration management
- logger: Centralized logging
- attendance_reader: ZKTeco device communication
- data_sync: Data storage and synchronization
- main: Main application coordinator
- windows_service: Windows service integration

Usage:
    from src.main import AttendanceSystem
    
    system = AttendanceSystem()
    system.run_once()  # Single sync
    # or
    system.run_scheduler()  # Continuous sync
"""

__version__ = "1.0.0"
__author__ = "Attendance System Team"
__description__ = "Attendance Data Synchronization System for ZKTeco Devices" 