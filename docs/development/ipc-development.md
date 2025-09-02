# IPC程式開發工作清單
*基於Nano Pi M1plus + Debian系統的兌幣機控制程式*

## 硬體環境規格

### 目標平台
- **主板**: Nano Pi M1plus
- **作業系統**: Debian Linux
- **程式語言**: Python 3.8+
- **連網方式**: 擎天有限公司IPC上網
- **通訊協定**: MQTT + HTTP API

## 第一階段：環境分析與架構設計 (第1週)

### 1. 分析現有IPC硬體環境與Python介面
```python
任務內容：
- 調查Nano Pi M1plus GPIO腳位配置
- 測試現有Python環境與套件
- 分析兌幣機硬體介面規格
- 確認感應器連接方式
- 檢查網路連線能力

技術需求：
- RPi.GPIO或類似套件
- pySerial (串列埠通訊)
- 硬體介面文檔

預估時間：8小時
```

### 2. 設計MQTT客戶端連線架構
```python
任務內容：
- 設計MQTT連線管理類
- 規劃主題結構與訊息格式
- 設計重連與錯誤處理機制
- 規劃QoS等級策略

技術規格：
- MQTT Broker: 現有服務
- Python套件: paho-mqtt
- 連線保持: Keep-alive 60秒
- 重連策略: 指數退避

預估時間：6小時
```

## 第二階段：核心通訊模組開發 (第2-3週)

### 3. 開發兌幣機硬體通訊模組
```python
任務內容：
- 實作兌幣機控制器通訊協定
- 開發硬幣投入檢測功能
- 實作硬幣輸出控制
- 建立設備狀態查詢功能

關鍵模組：
class CoinChangerController:
    def __init__(self, port='/dev/ttyUSB0')
    def get_status(self) -> dict
    def dispense_coins(self, amount: int) -> bool
    def get_coin_count(self) -> int
    def reset_device(self) -> bool

預估時間：16小時
```

### 4. 開發感應器資料收集模組
```python
任務內容：
- 溫度感應器資料讀取
- 濕度感應器資料讀取  
- 電壓監控功能
- 硬幣計數感應器整合

感應器模組：
class SensorManager:
    def __init__(self)
    def read_temperature(self) -> float
    def read_humidity(self) -> float
    def read_voltage(self) -> float
    def get_all_readings(self) -> dict

預估時間：12小時
```

### 5. 開發MQTT訊息發送與接收模組
```python
任務內容：
- 實作MQTT連線管理
- 設計訊息發送佇列
- 開發訂閱主題處理器
- 建立訊息確認機制

MQTT管理器：
class MQTTManager:
    def __init__(self, broker_host, machine_id)
    def connect(self) -> bool
    def publish_status(self, data: dict)
    def publish_transaction(self, transaction: dict)
    def subscribe_commands(self)
    def on_command_received(self, command: dict)

預估時間：14小時
```

## 第三階段：控制功能實作 (第3-4週)

### 6. 實作遠端補幣指令處理
```python
任務內容：
- MQTT指令接收處理
- 補幣操作執行邏輯
- 操作結果回報機制
- 安全驗證與權限控制

指令處理器：
class CommandProcessor:
    def process_refill_command(self, cmd: dict) -> dict
    def validate_command(self, cmd: dict) -> bool  
    def execute_refill(self, amount: int) -> bool
    def report_result(self, result: dict)

預估時間：12小時
```

### 7. 建立系統狀態監控與心跳機制
```python
任務內容：
- 系統健康檢查
- 定期心跳發送
- 設備狀態監控
- 異常狀況檢測

監控系統：
class SystemMonitor:
    def __init__(self, interval=30)
    def start_monitoring(self)
    def check_system_health(self) -> dict
    def send_heartbeat(self)
    def detect_anomalies(self) -> list

預估時間：10小時
```

### 8. 開發錯誤處理與重連機制
```python
任務內容：
- 網路連線錯誤處理
- MQTT重連策略
- 硬體通訊錯誤恢復
- 系統重啟機制

錯誤處理：
class ErrorHandler:
    def handle_network_error(self, error)
    def handle_hardware_error(self, error)  
    def reconnect_mqtt(self) -> bool
    def restart_system_if_needed(self)

預估時間：14小時
```

## 第四階段：使用者介面與維護 (第4-5週)

### 9. 設計網路參數設定介面
```python
任務內容：
- Web介面或CLI設定工具
- WiFi網路設定
- MQTT連線參數設定
- 機台基本資訊設定

設定介面選項：
1. Web介面 (Flask + HTML)
2. CLI工具 (argparse)  
3. 設定檔編輯器

預估時間：16小時
```

### 10. 建立日誌記錄與除錯系統
```python
任務內容：
- 結構化日誌記錄
- 不同等級日誌分類
- 日誌輪替與清理
- 遠端日誌上傳功能

日誌系統：
class LogManager:
    def setup_logging(self, level='INFO')
    def log_transaction(self, data: dict)
    def log_error(self, error: Exception)
    def upload_logs(self) -> bool
    def cleanup_old_logs(self)

預估時間：8小時
```

### 11. 開發自動更新與維護功能
```python
任務內容：
- 程式版本檢查
- 自動下載更新
- 安全更新安裝
- 設定檔備份恢復

更新系統：
class UpdateManager:
    def check_updates(self) -> dict
    def download_update(self, version: str) -> bool
    def install_update(self) -> bool
    def backup_config(self) -> bool
    def rollback_if_failed(self) -> bool

預估時間：12小時
```

## 第五階段：測試與部署 (第5-6週)

### 12. 進行硬體整合測試
```python
測試範圍：
- 兌幣機硬體控制測試
- 感應器讀取準確性測試
- MQTT通訊穩定性測試
- 長時間運行測試
- 異常狀況模擬測試

測試工具：
- unittest框架
- 硬體模擬器
- 網路中斷模擬
- 負載測試工具

預估時間：20小時
```

### 13. 現場部署與調校
```bash
部署任務：
- 現場環境評估
- 程式安裝與設定
- 網路連線配置
- 硬體連接檢查
- 功能驗證測試
- 使用者培訓

部署檢查清單：
□ 硬體連接正常
□ 網路連線穩定  
□ MQTT通訊正常
□ 兌幣功能正常
□ 感應器讀取正常
□ 錯誤處理正常

預估時間：16小時
```

## 開發環境設定

### Python環境需求
```bash
# 基礎套件安裝
sudo apt update
sudo apt install python3-pip python3-dev python3-venv

# 建立虛擬環境
python3 -m venv coiner_env
source coiner_env/bin/activate

# 安裝必要套件
pip install paho-mqtt
pip install pyserial
pip install RPi.GPIO  # 或適用於Nano Pi的套件
pip install requests
pip install flask
pip install schedule
```

### 專案目錄結構
```
coiner_ipc/
├── main.py                 # 主程式入口
├── config/
│   ├── settings.py         # 設定管理
│   └── machine_config.json # 機台設定檔
├── hardware/
│   ├── coin_changer.py     # 兌幣機控制
│   ├── sensors.py          # 感應器管理
│   └── gpio_manager.py     # GPIO控制
├── communication/
│   ├── mqtt_client.py      # MQTT客戶端
│   ├── message_handler.py  # 訊息處理
│   └── command_processor.py # 指令處理
├── monitoring/
│   ├── system_monitor.py   # 系統監控
│   ├── error_handler.py    # 錯誤處理
│   └── logger.py           # 日誌管理
├── web_interface/
│   ├── app.py             # Web設定介面
│   └── templates/         # HTML模板
├── tests/
│   ├── test_hardware.py   # 硬體測試
│   ├── test_mqtt.py       # MQTT測試
│   └── test_integration.py # 整合測試
├── scripts/
│   ├── install.sh         # 安裝腳本
│   ├── start.sh           # 啟動腳本  
│   └── update.sh          # 更新腳本
└── requirements.txt       # Python套件需求
```

## 開發時程總覽

| 階段 | 週數 | 主要工作 | 預估工時 |
|-----|------|---------|----------|
| 第一階段 | 第1週 | 環境分析與架構設計 | 14小時 |
| 第二階段 | 第2-3週 | 核心通訊模組開發 | 42小時 |
| 第三階段 | 第3-4週 | 控制功能實作 | 36小時 |
| 第四階段 | 第4-5週 | 使用者介面與維護 | 36小時 |
| 第五階段 | 第5-6週 | 測試與部署 | 36小時 |
| **總計** | **6週** |  | **164小時** |

## 關鍵技術挑戰

### 硬體通訊穩定性
- **挑戰**: 序列埠通訊可能不穩定
- **解決方案**: 實作重試機制與錯誤恢復

### 網路連線可靠性  
- **挑戰**: 網路中斷影響MQTT通訊
- **解決方案**: 離線緩存與自動重連

### 系統資源管理
- **挑戰**: Nano Pi資源有限
- **解決方案**: 優化記憶體使用與CPU負載

### 安全性考量
- **挑戰**: 遠端控制安全風險
- **解決方案**: 指令驗證與加密通訊

## 部署準備清單

### 硬體準備
- [ ] Nano Pi M1plus主板
- [ ] microSD卡 (32GB以上)
- [ ] 電源供應器 (5V 3A)
- [ ] 網路連接設備
- [ ] 兌幣機連接線材

### 軟體準備  
- [ ] Debian系統映像檔
- [ ] Python程式碼
- [ ] 設定檔模板
- [ ] 安裝腳本
- [ ] 測試工具

### 現場準備
- [ ] 網路環境確認
- [ ] 電力供應確認  
- [ ] 安裝位置規劃
- [ ] 測試設備準備
- [ ] 備用硬體準備

此開發清單涵蓋了IPC程式開發的所有面向，確保能夠穩定控制兌幣機並與雲端服務完美整合。