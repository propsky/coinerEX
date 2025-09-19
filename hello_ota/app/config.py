"""
設定管理模組
"""
import json
import os
from pathlib import Path

class Config:
    def __init__(self, config_file="/etc/hello-ota/config.json"):
        self.config_file = Path(config_file)
        self.config = {}
        self.load_config()

    def load_config(self):
        """載入設定檔"""
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            self.create_default_config()

    def create_default_config(self):
        """建立預設設定檔"""
        self.config = {
            "app": {
                "name": "hello-ota",
                "port": 8080,
                "host": "0.0.0.0",
                "heartbeat_interval": 30,
                "log_level": "INFO"
            },
            "ota": {
                "enabled": True,
                "update_server": "http://localhost:9000",
                "check_interval": 300,
                "backup_count": 3,
                "auto_update": False
            },
            "system": {
                "data_dir": "/var/lib/hello-ota",
                "log_dir": "/var/log/hello-ota",
                "pid_file": "/var/run/hello-ota.pid"
            }
        }

        # 建立設定檔目錄
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.save_config()

    def save_config(self):
        """儲存設定檔"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def get(self, key, default=None):
        """取得設定值，支援點號分隔的巢狀鍵"""
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key, value):
        """設定值，支援點號分隔的巢狀鍵"""
        keys = key.split('.')
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value
        self.save_config()

# 全域設定實例
config = Config()