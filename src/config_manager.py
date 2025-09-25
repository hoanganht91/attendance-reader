"""
Configuration Manager Module
Handles loading and validation of YAML configuration files
"""

import yaml
import os
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class DeviceConfig:
    """Configuration for a single attendance device"""
    name: str
    ip: str
    port: int
    device_id: str
    enabled: bool
    username: str = ""
    password: str = ""


@dataclass
class AppSettings:
    """Application settings configuration"""
    sync_interval: int
    max_retries: int
    timeout: int
    data_retention_days: int


class ConfigManager:
    """Manages application configuration from YAML files"""
    
    def __init__(self, config_path: str = "config/devices.yaml"):
        self.config_path = config_path
        self.settings: AppSettings = None
        self.devices: List[DeviceConfig] = []
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from YAML file"""
        try:
            if not os.path.exists(self.config_path):
                raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
            
            with open(self.config_path, 'r', encoding='utf-8') as file:
                config_data = yaml.safe_load(file)
            
            # Load settings
            settings_data = config_data.get('settings', {})
            self.settings = AppSettings(
                sync_interval=settings_data.get('sync_interval', 3600),
                max_retries=settings_data.get('max_retries', 3),
                timeout=settings_data.get('timeout', 30),
                data_retention_days=settings_data.get('data_retention_days', 30)
            )
            
            # Load devices
            devices_data = config_data.get('devices', [])
            self.devices = []
            
            for device_data in devices_data:
                device = DeviceConfig(
                    name=device_data.get('name', ''),
                    ip=device_data.get('ip', ''),
                    port=device_data.get('port', 4370),
                    device_id=device_data.get('device_id', ''),
                    enabled=device_data.get('enabled', True),
                    username=device_data.get('username', ''),
                    password=device_data.get('password', '')
                )
                self.devices.append(device)
            
            self._validate_config()
            
        except Exception as e:
            raise Exception(f"Error loading configuration: {str(e)}")
    
    def _validate_config(self) -> None:
        """Validate configuration data"""
        if not self.devices:
            raise ValueError("No devices configured")
        
        for device in self.devices:
            if not device.name:
                raise ValueError("Device name cannot be empty")
            if not device.ip:
                raise ValueError(f"IP address cannot be empty for device: {device.name}")
            if not device.device_id:
                raise ValueError(f"Device ID cannot be empty for device: {device.name}")
            if device.port <= 0 or device.port > 65535:
                raise ValueError(f"Invalid port number for device: {device.name}")
    
    def get_enabled_devices(self) -> List[DeviceConfig]:
        """Get list of enabled devices"""
        return [device for device in self.devices if device.enabled]
    
    def get_device_by_id(self, device_id: str) -> DeviceConfig:
        """Get device configuration by device ID"""
        for device in self.devices:
            if device.device_id == device_id:
                return device
        raise ValueError(f"Device with ID '{device_id}' not found")
    
    def reload_config(self) -> None:
        """Reload configuration from file"""
        self._load_config()
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary for logging"""
        return {
            'sync_interval': self.settings.sync_interval,
            'max_retries': self.settings.max_retries,
            'timeout': self.settings.timeout,
            'data_retention_days': self.settings.data_retention_days,
            'total_devices': len(self.devices),
            'enabled_devices': len(self.get_enabled_devices()),
            'device_names': [device.name for device in self.get_enabled_devices()]
        } 