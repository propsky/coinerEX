# IPC工程師MQTT協議實作指南

## 版本資訊
- **版本**: v1.0
- **建立日期**: 2025-09-18
- **適用對象**: IPC工程師
- **基於文件**: 飛絡力兌幣機MQTT通訊協定規範 v1.1

## 目錄
1. [概述](#概述)
2. [需要完成的協議清單](#需要完成的協議清單)
3. [建議完成順序](#建議完成順序)
4. [詳細實作指南](#詳細實作指南)
5. [測試流程](#測試流程)
6. [常見問題與解決方案](#常見問題與解決方案)
7. [參考代碼](#參考代碼)

## 概述

本文件為IPC工程師提供MQTT協議實作的完整指南，基於《飛絡力兌幣機MQTT通訊協定規範》，協助工程師有序地完成協議實作。

### 實作目標
- 建立穩定的MQTT通訊機制
- 實現完整的兌幣業務邏輯上報
- 支援遠端管理功能
- 確保系統可靠性和安全性

### 技術要求
- **作業系統**: Linux (Debian系統，如Nano Pi M1plus)
- **程式語言**: Python 3.7+
- **MQTT客戶端**: paho-mqtt
- **時間格式**: Unix timestamp (秒, UTC+8)
- **訊息格式**: JSON
- **QoS等級**: 統一使用QoS 0

### Linux環境注意事項

#### 系統需求
- **作業系統**: Debian Linux (Nano Pi M1plus主板)
- **Python版本**: 3.7+ (通常已預裝)
- **網路連線**: 透過擎天有限公司IPC網路
- **系統權限**: 需要讀寫權限訪問硬體接口

#### 必要套件安裝
```bash
# 更新套件清單
sudo apt update

# 安裝Python pip (如果未安裝)
sudo apt install python3-pip

# 安裝必要的Python套件
pip3 install paho-mqtt

# 安裝其他可能需要的套件
pip3 install pytz          # 時區處理
pip3 install schedule       # 定時任務
pip3 install psutil         # 系統監控
```

#### 系統服務設定
```bash
# 建立systemd服務檔案
sudo nano /etc/systemd/system/coiner-mqtt.service

# 服務檔案內容範例
[Unit]
Description=Coiner MQTT Client
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/coiner-mqtt
ExecStart=/usr/bin/python3 /home/pi/coiner-mqtt/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

# 啟用服務
sudo systemctl enable coiner-mqtt.service
sudo systemctl start coiner-mqtt.service
```

### Python開發注意事項

#### 虛擬環境建議
```bash
# 建立專案虛擬環境
python3 -m venv /home/pi/coiner-mqtt/venv

# 啟用虛擬環境
source /home/pi/coiner-mqtt/venv/bin/activate

# 安裝套件到虛擬環境
pip install paho-mqtt pytz schedule psutil

# 產生requirements.txt
pip freeze > requirements.txt
```

#### 時區處理最佳實務
```python
import pytz
from datetime import datetime

# 設定台灣時區
TAIWAN_TZ = pytz.timezone('Asia/Taipei')

# 正確的時間戳記生成
def get_taiwan_timestamp():
    """生成台灣時區的Unix時間戳記"""
    taiwan_time = datetime.now(TAIWAN_TZ)
    return int(taiwan_time.timestamp())

# 時間格式轉換
def timestamp_to_readable(timestamp):
    """將時間戳記轉換為可讀格式"""
    dt = datetime.fromtimestamp(timestamp, TAIWAN_TZ)
    return dt.strftime('%Y-%m-%d %H:%M:%S %Z')
```

#### 日誌管理
```python
import logging
import logging.handlers

# 設定日誌輪替
def setup_logging():
    logger = logging.getLogger('coiner_mqtt')
    logger.setLevel(logging.INFO)

    # 日誌檔案輪替 (每日輪替，保留7天)
    handler = logging.handlers.TimedRotatingFileHandler(
        '/var/log/coiner-mqtt.log',
        when='midnight',
        interval=1,
        backupCount=7
    )

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
```

#### 系統監控集成
```python
import psutil

def get_system_health():
    """獲取系統健康狀態"""
    return {
        "cpu_usage": psutil.cpu_percent(interval=1),
        "memory_usage": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage('/').percent,
        "temperature": get_cpu_temperature(),  # 需要實作
        "uptime": int(time.time() - psutil.boot_time())
    }

def get_cpu_temperature():
    """獲取CPU溫度 (Nano Pi專用)"""
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            temp = int(f.read().strip()) / 1000
        return temp
    except:
        return 0
```

#### 錯誤處理和恢復機制
```python
import traceback
import time

def robust_execution(func, max_retries=3, delay=5):
    """穩健的函數執行包裝器"""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            logger.error(f"執行失敗 (嘗試 {attempt + 1}/{max_retries}): {e}")
            logger.error(traceback.format_exc())

            if attempt < max_retries - 1:
                time.sleep(delay)
            else:
                raise e

# 使用範例
def send_heartbeat_robust():
    return robust_execution(lambda: client.send_heartbeat(get_system_health()))
```

#### 硬體接口集成
```python
# 硬體控制接口範例 (需依據實際硬體調整)
class HardwareInterface:
    def __init__(self):
        self.coin_acceptor = None
        self.bill_acceptor = None
        self.dispenser = None

    def get_machine_status(self):
        """獲取機台狀態"""
        # 實際實作需要依據飛絡力硬體接口
        pass

    def dispense_coins(self, count):
        """出幣功能"""
        # 實際實作需要依據飛絡力硬體接口
        pass

    def check_coin_inventory(self):
        """檢查硬幣庫存"""
        # 實際實作需要依據飛絡力硬體接口
        pass
```

#### 設定檔管理
```python
import configparser
import os

class Config:
    def __init__(self, config_file='/etc/coiner-mqtt/config.ini'):
        self.config = configparser.ConfigParser()
        self.config_file = config_file
        self.load_config()

    def load_config(self):
        """載入設定檔"""
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
        else:
            self.create_default_config()

    def create_default_config(self):
        """建立預設設定檔"""
        self.config['MQTT'] = {
            'broker_host': 'mqtt.coinerex.com',
            'broker_port': '1883',
            'device_id': 'CCM_001'
        }

        self.config['SYSTEM'] = {
            'heartbeat_interval': '300',  # 5分鐘
            'log_level': 'INFO'
        }

        # 建立設定檔目錄
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

        with open(self.config_file, 'w') as f:
            self.config.write(f)

# 使用範例
config = Config()
broker_host = config.config.get('MQTT', 'broker_host')
```

## 需要完成的協議清單

### A. 兌幣機發送協議 (📤 兌幣機 → 雲端)

| 編號 | 協議名稱 | MQTT主題 | 優先級 | 說明 |
|------|----------|----------|--------|------|
| 1 | 總帳回報 | `coinerex/accounting/{device_id}` | 高 | 兌幣後、定時上報總帳資料 |
| 2 | 交易事件 | `coinerex/transaction/{device_id}` | 高 | 每筆兌幣交易完成後立即上報 |
| 3 | 故障通知 | `coinerex/error/{device_id}` | 最高 | 機台故障時立即發送 |
| 4 | 警報通知 | `coinerex/alarm/{device_id}` | 中 | 警告狀態但仍可服務 |
| 5 | 心跳信號 | `coinerex/heartbeat/{device_id}` | 低 | 每5分鐘發送設備狀態 |

### B. 兌幣機接收協議 (📥 雲端 → 兌幣機)

| 編號 | 協議名稱 | MQTT主題 | 優先級 | 說明 |
|------|----------|----------|--------|------|
| 6 | ACK確認 | `coinerex/ack/{device_id}` | 高 | 接收雲端ACK確認回應 |
| 7 | 遠端出幣 | `coinerex/commands/{device_id}/coin_dispense` | 高 | 接收遠端出幣命令 |
| 8 | 機台重啟 | `coinerex/commands/{device_id}/restart` | 中 | 接收重啟命令 |
| 9 | 機台鎖定 | `coinerex/commands/{device_id}/lock` | 中 | 接收鎖定/解鎖命令 |
| 10 | 狀態查詢 | `coinerex/commands/{device_id}/query` | 低 | 接收狀態查詢命令 |

### C. 兌幣機回應協議 (📤 兌幣機 → 雲端)

| 編號 | 協議名稱 | MQTT主題 | 優先級 | 說明 |
|------|----------|----------|--------|------|
| 11 | 命令執行回應 | `coinerex/commands/{device_id}/ack` | 高 | 回應遠端命令執行結果 |

## 建議完成順序

### 🎯 第一階段：基礎通訊建立
**目標**: 建立基本MQTT連線和訊息格式
**預估時間**: 2-3天

#### 階段任務
1. **MQTT連線機制**
   - 實作MQTT客戶端連線到broker
   - 設備ID管理和主題訂閱
   - 連線斷線重連機制

2. **基礎訊息格式**
   - Unix timestamp (UTC+8) 時間戳記生成
   - message_id (UUID) 生成
   - 基礎JSON格式封裝

3. **心跳信號** (協議#5)
   - 每5分鐘發送心跳
   - 包含基本設備狀態

#### 階段產出
- 可正常連接MQTT broker
- 能發送標準格式的心跳訊息
- 具備基本的重連機制

### 🎯 第二階段：核心業務邏輯
**目標**: 實現核心兌幣功能通訊
**預估時間**: 3-4天

#### 階段任務
4. **交易事件上報** (協議#2)
   - 玩家兌幣完成後立即上報
   - transaction_id 生成邏輯
   - 支援100/500/1000元紙鈔和50元硬幣

5. **總帳回報** (協議#1)
   - 交易完成後上報最新總帳
   - 定時回報（每日23:59）

6. **ACK確認處理** (協議#6)
   - 接收並處理雲端ACK回應
   - 實現重傳機制（10秒→30秒→60秒）

#### 階段產出
- 完整的兌幣交易上報機制
- 可靠的ACK確認和重傳機制
- 準確的總帳統計功能

### 🎯 第三階段：故障處理機制
**目標**: 實現設備監控和故障上報
**預估時間**: 2-3天

#### 階段任務
7. **故障通知** (協議#3)
   - 硬幣用盡、投幣器異常等關鍵故障
   - 對照錯誤碼表實現

8. **警報通知** (協議#4)
   - 低幣量、前門開啟等警告狀態

#### 階段產出
- 完整的故障監控和上報機制
- 準確的警報分級處理

### 🎯 第四階段：遠端控制功能
**目標**: 實現雲端遠端管理功能
**預估時間**: 3-4天

#### 階段任務
9. **遠端出幣命令** (協議#7)
   - 接收並執行遠端出幣指令
   - 安全性驗證和執行結果回報

10. **其他遠端命令** (協議#8-10)
    - 重啟、鎖定、查詢狀態命令

11. **命令執行回應** (協議#11)
    - 統一的命令執行結果回報機制

#### 階段產出
- 完整的遠端控制功能
- 安全可靠的命令執行機制

## 詳細實作指南

### 1. MQTT客戶端初始化

```python
import paho.mqtt.client as mqtt
import json
import uuid
import time
from datetime import datetime, timezone, timedelta

class CoinerMQTTClient:
    def __init__(self, device_id: str, broker_host: str, broker_port: int = 1883):
        self.device_id = device_id
        self.broker_host = broker_host
        self.broker_port = broker_port

        # 設定UTC+8時區
        self.utc8_tz = timezone(timedelta(hours=8))

        # 初始化MQTT客戶端
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

        # ACK追蹤機制
        self.pending_acks = {}
        self.max_retries = 3
        self.retry_intervals = [10, 30, 60]

        # 交易ID計數器
        self.transaction_counters = {"TXN": 0, "REMOTE": 0}
        self.last_date = ""
```

### 2. 時間戳記生成

```python
def get_timestamp(self) -> int:
    """生成UTC+8時區的Unix時間戳記(秒)"""
    return int(datetime.now(self.utc8_tz).timestamp())

def generate_message_id(self) -> str:
    """生成唯一訊息ID"""
    return str(uuid.uuid4())
```

### 3. transaction_id 生成邏輯

```python
def generate_transaction_id(self, transaction_type: str) -> str:
    """生成交易ID
    格式: {TYPE}_{YYYYMMDD}_{HHMMSS}_{SEQ}
    """
    now = datetime.now(self.utc8_tz)
    current_date = now.strftime("%Y%m%d")
    current_time = now.strftime("%H%M%S")

    # 檢查日期變更，重置計數器
    if current_date != self.last_date:
        self.transaction_counters = {"TXN": 0, "REMOTE": 0}
        self.last_date = current_date

    # 選擇前綴
    type_mapping = {
        "exchange": "TXN",
        "remote_dispense": "REMOTE"
    }
    prefix = type_mapping.get(transaction_type, "TXN")

    # 遞增計數器
    self.transaction_counters[prefix] += 1
    seq = f"{self.transaction_counters[prefix]:03d}"

    return f"{prefix}_{current_date}_{current_time}_{seq}"
```

### 4. 基礎訊息發送

```python
def send_message(self, topic: str, data: dict, requires_ack: bool = False):
    """發送MQTT訊息"""
    message = {
        "timestamp": self.get_timestamp(),
        "device_id": self.device_id,
        "message_id": self.generate_message_id(),
        "message_type": topic.split('/')[-2],  # 從主題提取類型
        "version": "1.3.2",
        "data": data
    }

    payload = json.dumps(message)
    result = self.client.publish(topic, payload, qos=0)

    if requires_ack:
        # 加入ACK追蹤
        self.pending_acks[message["message_id"]] = {
            "timestamp": time.time(),
            "retry_count": 0,
            "topic": topic,
            "message": message
        }

    return result.is_published()
```

### 5. 核心業務協議實作

#### 5.1 交易事件上報

```python
def report_transaction(self, transaction_data: dict):
    """上報交易事件"""
    topic = f"coinerex/transaction/{self.device_id}"

    # 生成交易ID
    transaction_id = self.generate_transaction_id("exchange")

    data = {
        "transaction_type": "exchange",
        "transaction_id": transaction_id,
        "amounts": {
            "bills_inserted": transaction_data.get("bills_inserted", 0),
            "coins_inserted": transaction_data.get("coins_inserted", 0),
            "coins_dispensed": transaction_data.get("coins_dispensed", 0),
            "transaction_amount": transaction_data.get("transaction_amount", 0),
            "coin_value": 10  # 統一10元硬幣
        },
        "balance": {
            "before": transaction_data.get("balance_before", 0),
            "after": transaction_data.get("balance_after", 0)
        },
        "timing": {
            "start_time": transaction_data.get("start_time", self.get_timestamp()),
            "dispense_time": self.get_timestamp(),
            "duration_ms": transaction_data.get("duration_ms", 0)
        },
        "success": transaction_data.get("success", True)
    }

    return self.send_message(topic, data, requires_ack=True)
```

#### 5.2 總帳回報

```python
def report_accounting(self, accounting_data: dict):
    """上報總帳資料"""
    topic = f"coinerex/accounting/{self.device_id}"

    data = {
        "machine_status": accounting_data.get("machine_status", 1),
        "status_description": "待機",
        "counters": {
            "total_bills": accounting_data.get("total_bills", 0),
            "total_coins": accounting_data.get("total_coins", 0),
            "total_dispensed": accounting_data.get("total_dispensed", 0),
            "remote_dispensed": accounting_data.get("remote_dispensed", 0),
            "bonus_coins": accounting_data.get("bonus_coins", 0)
        },
        "current_state": {
            "debt_coins": accounting_data.get("debt_coins", 0),
            "balance": accounting_data.get("balance", 0)
        },
        "codes": {
            "alarm_code": accounting_data.get("alarm_code", 0),
            "error_code": accounting_data.get("error_code", 0)
        }
    }

    return self.send_message(topic, data, requires_ack=True)
```

#### 5.3 故障通知

```python
def report_error(self, error_code: int, description: str, context: dict = None):
    """上報故障事件"""
    topic = f"coinerex/error/{self.device_id}"

    # 錯誤嚴重程度映射
    severity_map = {
        1: "critical", 41: "critical", 42: "critical",
        2: "high", 11: "high", 12: "high", 13: "high",
        21: "high", 22: "high", 23: "high", 43: "high", 44: "high", 99: "high"
    }

    data = {
        "error_code": error_code,
        "error_description": description,
        "error_category": self._get_error_category(error_code),
        "severity": severity_map.get(error_code, "medium"),
        "suggested_action": self._get_suggested_action(error_code),
        "auto_recoverable": error_code not in [1, 41, 42],
        "affected_functions": self._get_affected_functions(error_code),
        "context": context or {},
        "impact": {
            "service_available": error_code not in [1, 41, 42],
            "estimated_downtime": "immediate_action_required" if error_code in [42] else "unknown"
        }
    }

    return self.send_message(topic, data, requires_ack=True)
```

#### 5.4 心跳信號

```python
def send_heartbeat(self, system_status: dict):
    """發送心跳信號"""
    topic = f"coinerex/heartbeat/{self.device_id}"

    data = {
        "status": system_status.get("status", "online"),
        "firmware_version": "1.3.2",
        "uptime_seconds": system_status.get("uptime_seconds", 0),
        "last_transaction": system_status.get("last_transaction", self.get_timestamp()),
        "network_quality": "excellent",
        "system_health": {
            "cpu_usage": system_status.get("cpu_usage", 0),
            "memory_usage": system_status.get("memory_usage", 0),
            "storage_usage": system_status.get("storage_usage", 0),
            "temperature": system_status.get("temperature", 0)
        },
        "service_status": {
            "coin_acceptor": "operational",
            "bill_acceptor": "operational",
            "dispenser": "operational",
            "display": "operational"
        },
        "statistics": {
            "transactions_today": system_status.get("transactions_today", 0),
            "coins_dispensed_today": system_status.get("coins_dispensed_today", 0),
            "error_count_today": system_status.get("error_count_today", 0),
            "last_maintenance": system_status.get("last_maintenance", self.get_timestamp())
        }
    }

    return self.send_message(topic, data, requires_ack=False)
```

### 6. 遠端命令處理

```python
def on_message(self, client, userdata, msg):
    """處理接收到的MQTT訊息"""
    try:
        topic_parts = msg.topic.split('/')
        payload = json.loads(msg.payload.decode())

        if topic_parts[-1] == "ack":
            # 處理ACK確認
            self._handle_ack(payload)
        elif "commands" in topic_parts:
            # 處理遠端命令
            self._handle_command(payload, msg.topic)

    except Exception as e:
        print(f"Error processing message: {e}")

def _handle_command(self, command: dict, topic: str):
    """處理遠端命令"""
    command_type = command.get("command_type")
    command_id = command.get("command_id")
    requires_ack = command.get("requires_ack", False)

    try:
        if command_type == "coin_dispense":
            result = self._execute_coin_dispense(command["data"])
        elif command_type == "restart":
            result = self._execute_restart(command["data"])
        elif command_type == "lock":
            result = self._execute_lock(command["data"])
        elif command_type == "query":
            result = self._execute_query(command["data"])
        else:
            raise ValueError(f"Unknown command type: {command_type}")

        if requires_ack:
            self._send_command_ack(command_id, "success", result)

    except Exception as e:
        if requires_ack:
            self._send_command_ack(command_id, "failed", {"error": str(e)})

def _execute_coin_dispense(self, data: dict) -> dict:
    """執行遠端出幣"""
    coins_to_dispense = data["coins_to_dispense"]

    # 檢查硬幣庫存
    if not self._check_coin_inventory(coins_to_dispense):
        raise Exception("硬幣庫存不足")

    # 執行出幣動作
    start_time = time.time()
    success = self._dispense_coins(coins_to_dispense)
    execution_time = int((time.time() - start_time) * 1000)

    if success:
        # 記錄遠端出幣交易
        self._record_remote_transaction(coins_to_dispense, data)

        return {
            "coins_dispensed": coins_to_dispense,
            "execution_time_ms": execution_time,
            "coins_remaining": self._get_coin_inventory(),
            "transaction_id": self.generate_transaction_id("remote_dispense")
        }
    else:
        raise Exception("出幣執行失敗")
```

## 測試流程

### 📋 測試檢查清單

#### 階段一：基礎通訊測試
- [ ] **MQTT連線測試**
  - [ ] 成功連接到MQTT broker
  - [ ] 正確訂閱所有必要主題
  - [ ] 斷線後能自動重連
  - [ ] 連線狀態監控正常

- [ ] **訊息格式測試**
  - [ ] timestamp格式正確 (Unix秒, UTC+8)
  - [ ] message_id唯一性驗證
  - [ ] JSON格式完整性檢查
  - [ ] version欄位正確

- [ ] **心跳信號測試**
  - [ ] 每5分鐘準時發送
  - [ ] 包含正確的設備狀態資訊
  - [ ] 系統健康狀態準確

#### 階段二：交易流程測試
- [ ] **兌幣交易測試**
  - [ ] 100元紙鈔 → 出幣10個 → 發送transaction
  - [ ] 50元硬幣 → 出幣5個 → 發送transaction
  - [ ] 500元紙鈔 → 出幣50個 → 發送transaction
  - [ ] 1000元紙鈔 → 出幣100個 → 發送transaction

- [ ] **transaction_id生成測試**
  - [ ] 格式正確: TXN_YYYYMMDD_HHMMSS_SEQ
  - [ ] 日期重置時序號歸零
  - [ ] 同秒內序號遞增
  - [ ] 不同交易類型前綴正確

- [ ] **總帳回報測試**
  - [ ] 交易後立即上報
  - [ ] 數據累計正確
  - [ ] 定時回報功能 (23:59)
  - [ ] 餘額計算準確

- [ ] **ACK機制測試**
  - [ ] 收到ACK後停止重傳
  - [ ] 未收到ACK時按時重傳 (10s→30s→60s)
  - [ ] 超過3次重傳後放棄
  - [ ] ACK訊息ID匹配正確

#### 階段三：故障處理測試
- [ ] **故障場景測試**
  - [ ] 硬幣用盡 (錯誤碼42) → 立即上報
  - [ ] 投幣器異常 (錯誤碼12) → 立即上報
  - [ ] 紙鈔機故障 (錯誤碼21) → 立即上報
  - [ ] 錯誤嚴重程度分級正確

- [ ] **警報場景測試**
  - [ ] 低幣量警報 (警告碼01) → 正常上報
  - [ ] 前門開啟警報 (警告碼02) → 正常上報
  - [ ] 警報不影響正常交易

- [ ] **故障恢復測試**
  - [ ] 故障解除後狀態正確回報
  - [ ] 警報清除後恢復正常運作
  - [ ] 錯誤碼清零正確

#### 階段四：遠端控制測試
- [ ] **遠端出幣測試**
  - [ ] 正確接收遠端出幣命令
  - [ ] 執行出幣動作成功
  - [ ] 執行結果準確回報
  - [ ] 安全性驗證有效

- [ ] **其他遠端命令測試**
  - [ ] 重啟命令正確執行
  - [ ] 鎖定/解鎖命令有效
  - [ ] 狀態查詢回應正確
  - [ ] 命令權限檢查

- [ ] **異常情況測試**
  - [ ] 硬幣不足時拒絕出幣
  - [ ] 機台故障時拒絕命令
  - [ ] 無效命令格式正確處理
  - [ ] 超時命令自動取消

#### 整合測試
- [ ] **離線場景測試**
  - [ ] 網路斷線時訊息正確快取
  - [ ] 重連後批次上傳成功
  - [ ] 重複訊息檢測有效
  - [ ] 離線期間最多快取100筆

- [ ] **壓力測試**
  - [ ] 連續交易處理穩定
  - [ ] 大量訊息傳輸無丟失
  - [ ] 長時間運行記憶體穩定
  - [ ] 高頻率命令處理正常

- [ ] **實際場景測試**
  - [ ] 完整兌幣流程順暢
  - [ ] 故障處理流程正確
  - [ ] 遠端管理流程有效
  - [ ] 多場景並發處理正常

### 🧪 測試工具建議

#### 1. MQTT測試工具
```bash
# 使用mosquitto客戶端模擬雲端
mosquitto_sub -h broker_host -t "coinerex/+/CCM_001" -v

# 發送測試命令
mosquitto_pub -h broker_host -t "coinerex/commands/CCM_001/coin_dispense" \
  -m '{"command_id":"TEST_001","command_type":"coin_dispense","data":{"coins_to_dispense":5}}'
```

#### 2. Python測試腳本
```python
# 建立簡單的測試腳本驗證各項功能
def test_transaction_flow():
    client = CoinerMQTTClient("CCM_001", "localhost")
    client.connect()

    # 模擬兌幣交易
    transaction_data = {
        "bills_inserted": 100,
        "coins_dispensed": 10,
        "transaction_amount": 100,
        "balance_before": 1000,
        "balance_after": 1100,
        "success": True
    }

    result = client.report_transaction(transaction_data)
    assert result == True

    print("交易流程測試通過")

if __name__ == "__main__":
    test_transaction_flow()
```

## 常見問題與解決方案

### Q1: MQTT連線不穩定怎麼辦？
**A**:
- 檢查網路連線品質
- 調整心跳間隔和重連機制
- 使用keep_alive參數
- 確認broker設定正確

### Q2: timestamp時區計算錯誤
**A**:
```python
# 正確的UTC+8時間戳記生成
utc8_tz = timezone(timedelta(hours=8))
timestamp = int(datetime.now(utc8_tz).timestamp())
```

### Q3: transaction_id重複問題
**A**:
- 確保日期變更時計數器重置
- 檢查系統時間準確性
- 使用持久化儲存保存計數器狀態

### Q4: ACK機制重傳過於頻繁
**A**:
- 檢查網路延遲狀況
- 調整重傳間隔時間
- 確認ACK訊息格式正確

### Q5: 遠端命令執行失敗
**A**:
- 檢查命令格式是否正確
- 驗證設備狀態是否允許執行
- 確認安全性驗證邏輯

## 參考代碼

### 完整的MQTT客戶端實作

請參考《飛絡力兌幣機MQTT通訊協定規範》文件中的Python範例代碼，該範例提供了完整的實作參考，包括：

- MQTT客戶端連線管理
- 訊息格式處理
- ACK機制實作
- 重傳邏輯
- 錯誤處理

### 建議的專案結構
```
mqtt_client/
├── main.py              # 主程式入口
├── mqtt_client.py       # MQTT客戶端核心類別
├── message_handler.py   # 訊息處理邏輯
├── config.py           # 設定檔
├── utils.py            # 工具函數
└── tests/              # 測試檔案
    ├── test_mqtt.py
    ├── test_transaction.py
    └── test_commands.py
```

## 總結

按照本指南的順序實作，可以確保：
1. **循序漸進**: 從簡單到複雜，降低實作難度
2. **重點優先**: 先完成核心功能，再擴展輔助功能
3. **可靠穩定**: 通過完整測試確保系統穩定性
4. **易於維護**: 模組化設計便於後續維護和擴展

建議工程師嚴格按照階段順序進行，每完成一個階段就進行充分測試，確保功能正確後再進入下一階段。

---

**文件維護**: 本文件會隨著協議規範更新而同步修正
**技術支援**: 如有實作問題請參考原始協議規範文件或聯絡開發團隊