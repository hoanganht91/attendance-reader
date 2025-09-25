"""
Unit tests for ConfigManager module
"""

import unittest
import tempfile
import os
import yaml
from src.config_manager import ConfigManager, DeviceConfig, AppSettings


class TestConfigManager(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_config = {
            'settings': {
                'sync_interval': 1800,
                'max_retries': 5,
                'timeout': 45,
                'data_retention_days': 60
            },
            'devices': [
                {
                    'name': 'Test Device 1',
                    'ip': '192.168.1.100',
                    'port': 4370,
                    'device_id': 'TEST001',
                    'enabled': True,
                    'username': '',
                    'password': ''
                },
                {
                    'name': 'Test Device 2',
                    'ip': '192.168.1.101',
                    'port': 4370,
                    'device_id': 'TEST002',
                    'enabled': False,
                    'username': 'admin',
                    'password': 'password'
                }
            ]
        }
        
        # Create temporary config file
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        yaml.dump(self.test_config, self.temp_file, default_flow_style=False)
        self.temp_file.close()
    
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_load_config_success(self):
        """Test successful configuration loading"""
        config_manager = ConfigManager(self.temp_file.name)
        
        # Test settings
        self.assertIsInstance(config_manager.settings, AppSettings)
        self.assertEqual(config_manager.settings.sync_interval, 1800)
        self.assertEqual(config_manager.settings.max_retries, 5)
        self.assertEqual(config_manager.settings.timeout, 45)
        self.assertEqual(config_manager.settings.data_retention_days, 60)
        
        # Test devices
        self.assertEqual(len(config_manager.devices), 2)
        self.assertIsInstance(config_manager.devices[0], DeviceConfig)
        self.assertEqual(config_manager.devices[0].name, 'Test Device 1')
        self.assertEqual(config_manager.devices[0].ip, '192.168.1.100')
        self.assertEqual(config_manager.devices[0].device_id, 'TEST001')
        self.assertTrue(config_manager.devices[0].enabled)
    
    def test_get_enabled_devices(self):
        """Test getting only enabled devices"""
        config_manager = ConfigManager(self.temp_file.name)
        enabled_devices = config_manager.get_enabled_devices()
        
        self.assertEqual(len(enabled_devices), 1)
        self.assertEqual(enabled_devices[0].device_id, 'TEST001')
        self.assertTrue(enabled_devices[0].enabled)
    
    def test_get_device_by_id(self):
        """Test getting device by ID"""
        config_manager = ConfigManager(self.temp_file.name)
        
        device = config_manager.get_device_by_id('TEST001')
        self.assertEqual(device.name, 'Test Device 1')
        self.assertEqual(device.ip, '192.168.1.100')
        
        device2 = config_manager.get_device_by_id('TEST002')
        self.assertEqual(device2.name, 'Test Device 2')
        self.assertFalse(device2.enabled)
        
        # Test non-existent device
        with self.assertRaises(ValueError):
            config_manager.get_device_by_id('NONEXISTENT')
    
    def test_config_validation(self):
        """Test configuration validation"""
        # Test empty devices
        empty_config = {'settings': self.test_config['settings'], 'devices': []}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(empty_config, f)
            temp_path = f.name
        
        try:
            with self.assertRaises(Exception):
                ConfigManager(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_config_summary(self):
        """Test configuration summary generation"""
        config_manager = ConfigManager(self.temp_file.name)
        summary = config_manager.get_config_summary()
        
        self.assertIn('sync_interval', summary)
        self.assertIn('total_devices', summary)
        self.assertIn('enabled_devices', summary)
        self.assertIn('device_names', summary)
        
        self.assertEqual(summary['total_devices'], 2)
        self.assertEqual(summary['enabled_devices'], 1)
        self.assertEqual(summary['device_names'], ['Test Device 1'])


if __name__ == '__main__':
    unittest.main() 