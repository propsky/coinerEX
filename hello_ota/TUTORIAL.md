# Hello OTA 使用教學

這份教學將指導您如何使用Hello OTA學習Python應用程式的遠端更新技術。

## 目錄

1. [環境準備](#環境準備)
2. [安裝步驟](#安裝步驟)
3. [基本使用](#基本使用)
4. [OTA更新流程](#ota更新流程)
5. [建立更新包](#建立更新包)
6. [測試案例](#測試案例)
7. [整合到自己的應用程式](#整合到自己的應用程式)
8. [故障排除](#故障排除)
9. [進階配置](#進階配置)

## 環境準備

### 系統需求

- **作業系統**: Linux (Ubuntu 18.04+, CentOS 7+, Debian 9+)
- **Python**: 3.8或更高版本
- **記憶體**: 最少256MB可用記憶體
- **磁碟空間**: 100MB可用空間
- **網路**: 能夠存取網際網路或內部更新服務器

### 必要套件

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip curl wget systemctl

# CentOS/RHEL
sudo yum install python3 python3-pip curl wget systemd
```

## 安裝步驟

### 1. 下載專案

```bash
# 如果您有Git
git clone <repository_url>
cd hello_ota

# 或下載ZIP檔案並解壓縮
wget <zip_url>
unzip hello_ota.zip
cd hello_ota
```

### 2. 執行安裝腳本

```bash
# 設定執行權限
chmod +x scripts/install.sh

# 執行安裝（需要root權限）
sudo ./scripts/install.sh
```

安裝腳本會自動完成：
- 建立系統用戶`hello-ota`
- 建立必要目錄
- 安裝Python依賴套件
- 設定systemd服務
- 建立預設配置檔

### 3. 驗證安裝

```bash
# 檢查服務狀態
sudo systemctl status hello-ota

# 檢查應用程式是否回應
curl http://localhost:8080/health
```

預期回應：
```json
{
  "status": "healthy",
  "timestamp": "2025-01-20T10:30:00"
}
```

## 基本使用

### 啟動和停止服務

```bash
# 啟動服務
sudo systemctl start hello-ota

# 停止服務
sudo systemctl stop hello-ota

# 重啟服務
sudo systemctl restart hello-ota

# 開機自動啟動
sudo systemctl enable hello-ota
```

### 檢查應用程式狀態

```bash
# 檢查基本狀態
curl http://localhost:8080/

# 檢查版本資訊
curl http://localhost:8080/version

# 檢查OTA狀態
curl http://localhost:8080/ota/status
```

### 查看日誌

```bash
# 即時查看日誌
sudo journalctl -u hello-ota -f

# 查看最近的日誌
sudo journalctl -u hello-ota --since "1 hour ago"

# 查看檔案日誌
sudo tail -f /var/log/hello-ota/hello-ota.log
```

## OTA更新流程

### 理解更新流程

Hello OTA的更新流程包含以下步驟：

1. **觸發更新**：通過HTTP API或自動檢查觸發
2. **下載更新**：從指定URL下載更新包
3. **驗證檔案**：檢查檔案完整性（SHA256）
4. **備份當前版本**：建立當前版本的備份
5. **套用更新**：解壓縮並替換檔案
6. **重啟服務**：通過外部腳本重啟應用程式
7. **驗證更新**：確認新版本正常運行

### 手動觸發更新

```bash
# 觸發更新到指定版本
curl -X POST http://localhost:8080/trigger_update \
  -H "Content-Type: application/json" \
  -d '{
    "version": "1.1.0",
    "update_url": "http://localhost:9000/updates/v1.1.0.tar.gz",
    "checksum": "abc123..."
  }'
```

### 檢查可用更新

```bash
# 手動檢查更新
curl -X POST http://localhost:8080/ota/check
```

## 建立更新包

### 1. 建立新版本

首先修改版本號：

```python
# 編輯 app/version.py
__version__ = "1.1.0"
__build_date__ = "2025-01-20"
__description__ = "Hello OTA 示範應用程式 - 新功能版本"
```

### 2. 使用建立更新工具

```bash
cd updates
python3 create_update.py --version 1.1.0 --source ../app
```

這會建立：
- `v1.1.0/` 目錄包含新版本檔案
- `v1.1.0.tar.gz` 壓縮檔
- `update_info.json` 更新資訊檔案

### 3. 手動建立更新包

```bash
# 建立更新目錄
mkdir -p updates/v1.1.0/app

# 複製新版本檔案
cp -r app/* updates/v1.1.0/app/

# 建立壓縮檔
cd updates
tar -czf v1.1.0.tar.gz v1.1.0/

# 計算校驗和
sha256sum v1.1.0.tar.gz
```

## 測試案例

### 1. 基本功能測試

```bash
# 測試1: 檢查服務健康狀態
curl http://localhost:8080/health

# 測試2: 取得版本資訊
curl http://localhost:8080/version

# 測試3: 檢查OTA功能
curl http://localhost:8080/ota/status
```

### 2. 模擬更新服務器

```bash
# 啟動模擬服務器
cd tests
python3 mock_server.py

# 在另一個終端測試更新
curl -X POST http://localhost:8080/trigger_update \
  -H "Content-Type: application/json" \
  -d '{
    "version": "1.1.0",
    "update_url": "http://localhost:9000/updates/v1.1.0.tar.gz"
  }'
```

### 3. 完整更新測試

```bash
# 第一步：檢查當前版本
current_version=$(curl -s http://localhost:8080/version | jq -r '.version')
echo "當前版本: $current_version"

# 第二步：建立測試更新包
cd updates
python3 create_update.py --version 1.1.0

# 第三步：啟動模擬服務器
cd ../tests
python3 mock_server.py &
SERVER_PID=$!

# 第四步：觸發更新
curl -X POST http://localhost:8080/trigger_update \
  -H "Content-Type: application/json" \
  -d '{
    "version": "1.1.0",
    "update_url": "http://localhost:9000/updates/v1.1.0.tar.gz"
  }'

# 第五步：等待更新完成並驗證
sleep 10
new_version=$(curl -s http://localhost:8080/version | jq -r '.version')
echo "新版本: $new_version"

# 清理
kill $SERVER_PID
```

## 整合到自己的應用程式

這個章節將說明如何將Hello OTA的OTA功能整合到您自己開發的Python應用程式中。

### 快速整合方案

#### 1. 複製核心模組

將以下檔案複製到您的專案中：

```bash
# 從hello_ota專案複製核心檔案
cp hello_ota/app/ota_manager.py your_project/
cp hello_ota/app/config.py your_project/
cp hello_ota/app/version.py your_project/
```

#### 2. 修改您的主程式

在您的應用程式主程式中新增OTA功能：

```python
# your_app.py
import threading
import time
from ota_manager import OTAManager
from config import config

class YourApplication:
    def __init__(self):
        self.running = True
        self.ota_manager = OTAManager()

        # 您的應用程式初始化...

    def start(self):
        """啟動應用程式"""
        # 啟動OTA檢查線程（如果啟用）
        if config.get('ota.enabled', True):
            self._start_ota_checker()

        # 您的應用程式主邏輯...
        self.main_loop()

    def _start_ota_checker(self):
        """啟動OTA檢查線程"""
        def ota_check_loop():
            interval = config.get('ota.check_interval', 300)  # 5分鐘
            while self.running:
                try:
                    update_info = self.ota_manager.check_for_updates()
                    if update_info and config.get('ota.auto_update', False):
                        print("發現更新且已啟用自動更新")
                        self._perform_update(update_info)
                except Exception as e:
                    print(f"OTA檢查失敗: {e}")

                time.sleep(interval)

        ota_thread = threading.Thread(target=ota_check_loop)
        ota_thread.daemon = True
        ota_thread.start()

    def _perform_update(self, update_info):
        """執行OTA更新"""
        try:
            print(f"開始執行OTA更新到版本 {update_info['version']}")

            # 下載更新
            update_file = self.ota_manager.download_update(update_info)

            # 套用更新（這會導致程式退出）
            self.ota_manager.apply_update(update_file, update_info)

        except Exception as e:
            print(f"OTA更新失敗: {e}")

    def handle_ota_trigger(self, update_data):
        """處理手動觸發的OTA更新"""
        try:
            # 在背景執行更新
            update_thread = threading.Thread(
                target=self._perform_update,
                args=(update_data,)
            )
            update_thread.daemon = True
            update_thread.start()

            return {"status": "accepted", "message": "更新請求已接受"}

        except Exception as e:
            return {"status": "error", "message": str(e)}
```

#### 3. 設定版本管理

建立或修改版本檔案：

```python
# version.py
__version__ = "1.0.0"  # 您的應用程式版本
__build_date__ = "2025-01-20"
__description__ = "您的應用程式名稱"

def get_version_info():
    return {
        "version": __version__,
        "build_date": __build_date__,
        "description": __description__
    }
```

#### 4. 新增HTTP API端點（可選）

如果您的應用程式有HTTP服務器，可以新增OTA相關端點：

```python
# 新增到您的HTTP路由中
def handle_ota_status(self):
    """取得OTA狀態"""
    from version import __version__
    return {
        "current_version": __version__,
        "ota_enabled": config.get('ota.enabled', True),
        "update_history": self.ota_manager.get_update_history()[-5:]
    }

def handle_trigger_update(self, request_data):
    """處理觸發更新請求"""
    return self.handle_ota_trigger(request_data)

def handle_check_update(self):
    """手動檢查更新"""
    update_info = self.ota_manager.check_for_updates()
    if update_info:
        return update_info
    else:
        return {
            "has_update": False,
            "current_version": __version__,
            "message": "目前已是最新版本"
        }
```

### 針對特定應用類型的整合

#### 兌幣機IPC應用程式整合

針對您的兌幣機專案，特別推薦以下整合方式：

```python
# coiner_ipc_app.py
import time
from ota_manager import OTAManager
from mqtt_client import CoinerMQTTClient  # 您現有的MQTT客戶端

class CoinerIPCApp:
    def __init__(self):
        self.mqtt_client = CoinerMQTTClient()
        self.ota_manager = OTAManager()

        # 註冊OTA命令處理器
        self.mqtt_client.register_command_handler('ota_update', self.handle_ota_command)

    def handle_ota_command(self, command_data):
        """處理MQTT OTA命令"""
        try:
            # 驗證命令來源和權限
            if not self._verify_ota_permission(command_data):
                return {"status": "rejected", "reason": "權限不足"}

            # 執行OTA更新
            update_info = {
                "version": command_data["version"],
                "download_url": command_data["download_url"],
                "checksum": command_data.get("checksum", "")
            }

            result = self.handle_ota_trigger(update_info)

            # 通過MQTT回報結果
            self.mqtt_client.send_command_response(
                command_data["command_id"],
                result
            )

        except Exception as e:
            self.mqtt_client.send_command_response(
                command_data["command_id"],
                {"status": "error", "message": str(e)}
            )
```

#### 簡單守護程式整合

對於簡單的守護程式應用：

```python
# simple_daemon.py
import signal
import sys
from ota_manager import OTAManager

class SimpleDaemon:
    def __init__(self):
        self.running = True
        self.ota_manager = OTAManager()

        # 設定信號處理
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGUSR1, self._ota_signal_handler)  # 用於觸發OTA

    def _signal_handler(self, signum, frame):
        """處理停止信號"""
        self.running = False

    def _ota_signal_handler(self, signum, frame):
        """處理OTA觸發信號"""
        try:
            update_info = self.ota_manager.check_for_updates()
            if update_info:
                self._perform_update(update_info)
        except Exception as e:
            print(f"OTA更新失敗: {e}")

    def main_loop(self):
        """主要工作循環"""
        while self.running:
            # 您的應用程式邏輯
            time.sleep(1)
```

### 自訂OTA管理器

如果您需要更多客製化功能：

```python
# custom_ota_manager.py
from ota_manager import OTAManager

class CustomOTAManager(OTAManager):
    def __init__(self, app_config):
        super().__init__()
        self.app_config = app_config

        # 自訂路徑
        self.app_dir = app_config.get('app_dir')
        self.backup_dir = app_config.get('backup_dir')

    def check_for_updates(self):
        """自訂更新檢查邏輯"""
        # 可以整合您自己的更新服務器API
        from version import __version__

        # 呼叫您的更新API
        response = self._call_your_update_api(__version__)

        if response.get('has_update'):
            return {
                'has_update': True,
                'latest_version': response['latest_version'],
                'download_url': response['download_url'],
                'checksum': response['checksum']
            }
        return None

    def _call_your_update_api(self, current_version):
        """呼叫您自己的更新API"""
        # 實作您的更新檢查邏輯
        pass

    def _pre_update_hook(self):
        """更新前的自訂操作"""
        # 例如：停止特定服務、備份設定檔等
        pass

    def _post_update_hook(self):
        """更新後的自訂操作"""
        # 例如：遷移資料、更新設定等
        pass
```

### 設定檔整合

建立適合您應用程式的設定檔：

```json
{
  "app": {
    "name": "your-app-name",
    "version": "1.0.0",
    "environment": "production"
  },
  "ota": {
    "enabled": true,
    "update_server": "https://your-update-server.com",
    "check_interval": 3600,
    "auto_update": false,
    "backup_count": 5,
    "allowed_hours": [2, 3, 4],
    "maintenance_window": true
  },
  "security": {
    "require_signature": true,
    "trusted_sources": [
      "https://your-update-server.com"
    ]
  }
}
```

### systemd服務整合

為您的應用程式建立systemd服務檔案：

```ini
# /etc/systemd/system/your-app.service
[Unit]
Description=Your Application with OTA Support
After=network.target

[Service]
Type=simple
User=your-app-user
Group=your-app-group
WorkingDirectory=/opt/your-app
ExecStart=/usr/bin/python3 /opt/your-app/main.py
Restart=always
RestartSec=10

# OTA支援環境變數
Environment=OTA_ENABLED=true
Environment=OTA_CONFIG_FILE=/etc/your-app/config.json

[Install]
WantedBy=multi-user.target
```

### 測試整合

建立測試腳本驗證整合：

```python
# test_integration.py
import unittest
from your_app import YourApplication

class TestOTAIntegration(unittest.TestCase):
    def setUp(self):
        self.app = YourApplication()

    def test_ota_manager_initialization(self):
        """測試OTA管理器初始化"""
        self.assertIsNotNone(self.app.ota_manager)

    def test_ota_configuration(self):
        """測試OTA設定"""
        from config import config
        self.assertTrue(config.get('ota.enabled'))

    def test_version_info(self):
        """測試版本資訊"""
        from version import get_version_info
        info = get_version_info()
        self.assertIn('version', info)
        self.assertIn('build_date', info)

if __name__ == '__main__':
    unittest.main()
```

### 整合檢查清單

完成整合後，請檢查以下項目：

- [ ] **版本管理**：確保版本號正確設定
- [ ] **設定檔**：OTA相關設定正確配置
- [ ] **路徑設定**：應用程式、備份、日誌目錄正確
- [ ] **權限設定**：服務用戶有適當的讀寫權限
- [ ] **網路設定**：能夠連接到更新服務器
- [ ] **測試驗證**：手動觸發更新測試成功
- [ ] **服務整合**：systemd服務正常運作
- [ ] **日誌記錄**：OTA操作有完整日誌
- [ ] **回滾機制**：更新失敗時能正確回滾
- [ ] **安全性**：檔案校驗和權限控制正常

### 常見整合問題

#### 1. 模組導入錯誤

**問題**：`ModuleNotFoundError: No module named 'ota_manager'`

**解決方案**：
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from ota_manager import OTAManager
```

#### 2. 權限問題

**問題**：OTA更新時權限不足

**解決方案**：
```bash
# 確保服務用戶有適當權限
sudo chown -R your-app-user:your-app-group /opt/your-app
sudo chmod +x /opt/your-app/main.py
```

#### 3. 設定檔路徑問題

**問題**：找不到設定檔

**解決方案**：
```python
# 使用絕對路徑或環境變數
config_file = os.environ.get('OTA_CONFIG_FILE', '/etc/your-app/config.json')
config = Config(config_file)
```

通過以上步驟，您就可以將Hello OTA的功能成功整合到自己的Python應用程式中，實現安全可靠的遠端更新功能。

## 故障排除

### 常見問題

#### 1. 服務無法啟動

**症狀**：`systemctl start hello-ota` 失敗

**解決方案**：
```bash
# 檢查詳細錯誤
sudo journalctl -u hello-ota --no-pager

# 檢查權限
sudo ls -la /opt/hello-ota
sudo ls -la /var/log/hello-ota

# 手動測試
sudo -u hello-ota python3 /opt/hello-ota/main.py
```

#### 2. 更新下載失敗

**症狀**：更新觸發後出現下載錯誤

**解決方案**：
```bash
# 檢查網路連線
curl -I http://localhost:9000/updates/v1.1.0.tar.gz

# 檢查磁碟空間
df -h /tmp

# 檢查權限
sudo ls -la /tmp/hello-ota-update
```

#### 3. 更新失敗回滾

**症狀**：更新過程中失敗，需要回滾

**解決方案**：
```bash
# 檢查備份
sudo ls -la /var/backups/hello-ota

# 手動回滾（如果自動回滾失敗）
sudo systemctl stop hello-ota
sudo rm -rf /opt/hello-ota
sudo cp -r /var/backups/hello-ota/backup_1.0.0_* /opt/hello-ota
sudo chown -R hello-ota:hello-ota /opt/hello-ota
sudo systemctl start hello-ota
```

### 日誌分析

```bash
# 檢查應用程式日誌
sudo tail -f /var/log/hello-ota/hello-ota.log

# 檢查系統日誌
sudo journalctl -u hello-ota -f

# 篩選錯誤訊息
sudo journalctl -u hello-ota | grep ERROR

# 檢查OTA相關日誌
sudo grep "OTA" /var/log/hello-ota/hello-ota.log
```

## 進階配置

### 配置檔說明

編輯 `/etc/hello-ota/config.json`：

```json
{
  "app": {
    "name": "hello-ota",
    "port": 8080,                    // HTTP服務器埠號
    "host": "0.0.0.0",              // 綁定地址
    "heartbeat_interval": 30,        // 心跳間隔（秒）
    "log_level": "INFO"              // 日誌等級
  },
  "ota": {
    "enabled": true,                 // 啟用OTA功能
    "update_server": "http://localhost:9000",  // 更新服務器URL
    "check_interval": 300,           // 檢查更新間隔（秒）
    "backup_count": 3,               // 保留備份數量
    "auto_update": false             // 自動更新
  },
  "system": {
    "data_dir": "/var/lib/hello-ota",      // 資料目錄
    "log_dir": "/var/log/hello-ota",       // 日誌目錄
    "pid_file": "/var/run/hello-ota.pid"   // PID檔案
  }
}
```

### 啟用自動更新

```bash
# 編輯配置檔
sudo nano /etc/hello-ota/config.json

# 修改 ota.auto_update 為 true
"auto_update": true

# 重啟服務
sudo systemctl restart hello-ota
```

### 自訂更新服務器

```bash
# 修改更新服務器URL
sudo nano /etc/hello-ota/config.json

# 修改 ota.update_server
"update_server": "https://your-update-server.com"

# 重啟服務
sudo systemctl restart hello-ota
```

### 安全性設定

#### 1. 限制網路存取

```bash
# 使用iptables限制存取
sudo iptables -A INPUT -p tcp --dport 8080 -s 192.168.1.0/24 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8080 -j DROP
```

#### 2. 使用HTTPS

修改配置以支援HTTPS（需要額外實作）：

```json
{
  "app": {
    "ssl_enabled": true,
    "ssl_cert": "/etc/ssl/certs/hello-ota.crt",
    "ssl_key": "/etc/ssl/private/hello-ota.key"
  }
}
```

### 監控和警報

#### 1. 服務監控

```bash
# 建立監控腳本
cat > /usr/local/bin/hello-ota-monitor.sh << 'EOF'
#!/bin/bash
if ! systemctl is-active --quiet hello-ota; then
    echo "Hello OTA service is down!" | mail -s "Service Alert" admin@company.com
    systemctl restart hello-ota
fi
EOF

chmod +x /usr/local/bin/hello-ota-monitor.sh

# 建立cron作業
echo "*/5 * * * * /usr/local/bin/hello-ota-monitor.sh" | sudo crontab -
```

#### 2. 日誌監控

```bash
# 使用logwatch監控錯誤
sudo apt install logwatch
```

## 總結

Hello OTA提供了一個完整的Python應用程式OTA更新解決方案。通過這個教學，您應該能夠：

1. **理解OTA更新的基本概念和流程**
2. **安裝和配置Hello OTA應用程式**
3. **建立和部署更新包**
4. **監控和故障排除OTA更新**
5. **自訂配置以適應特定需求**

這個範例可以作為您實現自己的Python應用程式OTA更新系統的基礎。

如需更多協助，請參考：
- 專案README.md
- 原始碼註釋
- 日誌檔案
- 系統日誌