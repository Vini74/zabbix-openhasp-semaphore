#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
semafor_config.py

Configuration module for zabbix-openhasp-semaphore project.
Handles loading settings from environment variables with default values.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class SemaforConfig:
    """Configuration class for zabbix-openhasp-semaphore"""

    def __init__(self):
        # Zabbix API Configuration
        self.ZABBIX_URL = os.environ.get('ZABBIX_URL', 'http://127.0.0.1:8080/api_jsonrpc.php')
        self.ZABBIX_API_TOKEN = os.environ.get('ZABBIX_API_TOKEN', 'YOUR_ZABBIX_API_TOKEN')

        # MQTT Configuration
        self.MQTT_BROKER = os.environ.get('MQTT_BROKER', 'mqtt.example.com')
        self.MQTT_USER = os.environ.get('MQTT_USER', 'mqtt_user')
        self.MQTT_PASS = os.environ.get('MQTT_PASS', 'mqtt_pass')

        # openHASP Devices
        devices_str = os.environ.get('OPENHASP_DEVICES', 'semaphore_01,semaphore_02,semaphore_03')
        self.OPENHASP_DEVICES = [device.strip() for device in devices_str.split(',')]

        # Ignore acknowledged problems
        self.IGNORE_ACKNOWLEDGED = os.environ.get(
            'IGNORE_ACKNOWLEDGED', 'True'
        ).lower() == 'true'

        # Debug mode
        self.DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

    def log(self, msg):
        """Debug logging"""
        if self.DEBUG:
            import sys
            print(f"[DEBUG] {msg}", file=sys.stderr)


# Global configuration instance
semafor_config = SemaforConfig()