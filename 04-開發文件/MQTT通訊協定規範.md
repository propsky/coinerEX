# 飛絡力兌幣機 MQTT 通訊協定規範

## 版本資訊
- **版本**: v1.1
- **建立日期**: 2025-09-12
- **修改日期**: 2025-09-12
- **適用設備**: 飛絡力兌幣機系列
- **基於協定**: 飛絡力雲端通訊協定 V1.3

## 目錄
1. [概述](#概述)
2. [MQTT 主題架構](#mqtt-主題架構)
3. [訊息格式規範](#訊息格式規範)
4. [回報機制](#回報機制)
5. [訊息類型定義](#訊息類型定義)
6. [錯誤碼對照表](#錯誤碼對照表)
7. [實作範例](#實作範例)
8. [注意事項](#注意事項)

## 概述

本協定定義了飛絡力兌幣機透過 MQTT 協定與雲端管理平台的通訊格式。系統採用事件驅動與定時回報相結合的機制，確保即時性與可靠性。

### 支援幣別規格
- **接受紙鈔**: 100元、500元、1000元
- **接受硬幣**: 50元
- **出幣硬幣**: 統一為10元硬幣

### 設計目標
- **即時監控**: 關鍵事件立即上報
- **成本控制**: 優化訊息傳輸，控制月訊息量在1000個以內
- **可靠性**: 透過握手確認機制確保重要訊息送達
- **簡化架構**: 統一使用QoS 0降低複雜度
- **可擴展性**: 支援未來功能擴展

## MQTT 主題架構

### 主題命名規範
```
coinerex/{message_type}/{device_id}
```

### 主題分類

#### 1. 設備上報主題 (Publish)
```
coinerex/
├── status/{device_id}          # 機台狀態資料
├── accounting/{device_id}      # 總帳回報
├── transaction/{device_id}     # 交易事件
├── alarm/{device_id}          # 警報通知
├── error/{device_id}          # 故障通知
└── heartbeat/{device_id}      # 心跳信號
```

#### 2. 雲端控制主題 (Subscribe)
```
coinerex/commands/
├── {device_id}/coin_dispense   # 遠端出幣命令
├── {device_id}/restart         # 重啟命令
├── {device_id}/lock           # 上鎖/解鎖命令
├── {device_id}/query          # 查詢命令
└── {device_id}/config         # 設定命令
```

### QoS 等級設定
**統一使用 QoS 0**: 所有訊息均使用 QoS 0 (Fire and Forget) 模式，透過應用層握手機制確保重要訊息的可靠性。

#### 握手確認主題
```
coinerex/ack/{device_id}     # 設備確認回應
coinerex/commands/{device_id}/ack  # 雲端命令確認
```

## 訊息格式規範

### 基礎訊息格式
所有 MQTT 訊息均採用 JSON 格式，包含以下基礎欄位：

```json
{
  "timestamp": "2025-09-12T10:30:00.000Z",
  "device_id": "string",
  "message_id": "string", 
  "message_type": "string",
  "version": "1.0",
  "data": {}
}
```

#### 基礎欄位說明
| 欄位 | 類型 | 必填 | 說明 |
|------|------|------|------|
| timestamp | string | ✓ | ISO 8601 格式時間戳記 |
| device_id | string | ✓ | 設備唯一識別碼 |
| message_id | string | ✓ | 訊息唯一識別碼 (UUID) |
| message_type | string | ✓ | 訊息類型 |
| version | string | ✓ | 協定版本號 |
| data | object | ✓ | 具體資料內容 |

#### ID 生成規則

##### transaction_id 生成邏輯
**格式**: `{TYPE}_{YYYYMMDD}_{HHMMSS}_{SEQ}`

**組成說明**:
- `TYPE`: 交易類型縮寫
  - `TXN`: 一般兌幣交易 (exchange)
  - `REMOTE`: 遠端出幣 (remote_dispense)
- `YYYYMMDD`: 交易日期 (8位數)
- `HHMMSS`: 交易時間 (6位數)
- `SEQ`: 當日流水序號 (3位數，從001開始)

**範例**:
- `TXN_20250912_103000_001` - 第1筆一般兌幣
- `REMOTE_20250912_164500_001` - 第1筆遠端出幣

**生成邏輯**:
1. **兌幣機端生成**: 所有 transaction_id 由兌幣機本地生成
2. **日期重置**: 每日00:00序號重置為001
3. **斷線處理**: 網路斷線期間照常生成，恢復後批次上傳
4. **重複避免**: 同一秒內多筆交易自動遞增序號
5. **時間校正**: 使用兌幣機本地時間，定期與雲端同步

**實作注意事項**:
- 兌幣機需維護每日交易計數器
- 重開機後需從持久化儲存中恢復計數器
- 確保即使在離線狀態下也能生成唯一ID

## 回報機制

### 事件觸發回報 (即時)
| 事件 | 觸發條件 | 優先級 | 需要ACK |
|------|----------|--------|--------|
| 交易完成 | 兌幣/遠端出幣完成 | 高 | ✓ |
| 故障發生 | Error Code > 0 | 最高 | ✓ |
| 警報狀態 | Alarm Code > 0 | 高 | ✓ |
| 狀態變更 | 機台狀態改變 | 中 | ✗ |

### 定時回報機制
| 類型 | 頻率 | 說明 | 需要ACK |
|------|------|------|--------|
| 心跳信號 | 5分鐘 | 確認設備在線狀態 | ✗ |
| 狀態輪詢 | 30分鐘 | 定期上報機台狀態 | ✗ |
| 完整總帳 | 每日23:59 | 日結總帳回報 | ✓ |

### 握手確認機制
#### 重要訊息確認流程
1. **設備發送訊息**: 使用QoS 0發送重要訊息
2. **雲端回應ACK**: 透過ACK主題回應確認
3. **超時重傳**: 未收到ACK則重傳，最多3次
4. **重傳間隔**: 10秒 → 30秒 → 60秒

#### ACK訊息格式
```json
{
  "timestamp": "2025-09-12T10:30:00.000Z",
  "ack_message_id": "原訊息的message_id",
  "status": "received|processed|error",
  "error_message": "錯誤描述 (如果有)"
}
```

### 離線處理機制
- **離線快取**: 網路斷線時暫存最多100筆重要訊息
- **批次上傳**: 網路恢復後依時間順序批次傳送
- **重複檢測**: 透過message_id避免重複處理

## 訊息類型定義

### 1. 總帳回報 (accounting)

主題: `coinerex/accounting/{device_id}`

#### 使用情境
**觸發時機**:
1. **兌幣完成後**: 玩家兌幣交易完成立即上報最新總帳
2. **遠端出幣後**: 雲端遠端控制出幣完成後上報
3. **定時回報**: 每日23:59自動上報完整總帳
4. **雲端主動查詢**: 收到雲端查詢命令時立即回報

**情境範例**: 玩家投入100元紙鈔兌換硬幣，機台出幣10個10元硬幣後，立即上報更新後的總帳資料。

```json
{
  "timestamp": "2025-09-12T10:30:00.000Z",
  "device_id": "CCM_001",
  "message_id": "uuid-001",
  "message_type": "accounting",
  "version": "1.1",
  "data": {
    "machine_status": 1,
    "status_description": "待機",
    "counters": {
      "total_bills": 1250100,      // 總紙鈔數增加100元
      "total_coins": 850050,       // 總投幣數增加50元硬幣
      "total_dispensed": 450010,   // 總出幣數增加10個硬幣
      "remote_dispensed": 1500,    // 遠端出幣數不變
      "bonus_coins": 200           // 贈幣數不變
    },
    "current_state": {
      "debt_coins": 0,             // 無欠幣
      "balance": 15080             // 兌換餘額更新
    },
    "codes": {
      "alarm_code": 0,             // 無警報
      "error_code": 0              // 無故障
    }
  }
}
```

**伺服器回應**: 
```json
{
  "timestamp": "2025-09-12T10:30:01.000Z",
  "ack_message_id": "uuid-001",
  "status": "processed",
  "error_message": null
}
```

#### 機台狀態對照
| 狀態碼 | 說明 | 情境 |
|--------|------|------|
| 0x00 | 詢問 | 機台查詢雲端指令時 |
| 0x01 | 待機 | 正常運作，等待玩家投幣 |
| 0x03 | 遠端 | 執行雲端遠端出幣指令 |
| 0x04 | 故障 | 機台發生故障無法服務 |

### 2. 交易事件 (transaction)

主題: `coinerex/transaction/{device_id}`

#### 使用情境

**觸發時機**:
1. **玩家兌幣**: 玩家投入紙鈔或硬幣，機台完成出幣後立即上報
2. **遠端出幣**: 雲端系統遠端控制出幣完成後上報

#### 情境範例 1: 玩家一般兌幣
**情境**: 玩家投入100元紙鈔，機台自動出幣10個10元硬幣
```json
{
  "timestamp": "2025-09-12T10:30:00.000Z",
  "device_id": "CCM_001",
  "message_id": "uuid-002", 
  "message_type": "transaction",
  "version": "1.1",
  "data": {
    "transaction_type": "exchange",
    "transaction_id": "TXN_20250912_103000_001",
    "amounts": {
      "bills_inserted": 100,       // 投入100元紙鈔
      "coins_inserted": 0,         // 未投入硬幣
      "coins_dispensed": 10,       // 出幣10個
      "transaction_amount": 100,   // 交易金額100元
      "coin_value": 10             // 每個硬幣10元
    },
    "balance": {
      "before": 14900,            // 交易前餘額
      "after": 15000              // 交易後餘額增加100元
    },
    "timing": {
      "start_time": "2025-09-12T10:29:45.000Z",  // 開始投幣時間
      "dispense_time": "2025-09-12T10:30:00.000Z", // 出幣完成時間
      "duration_ms": 15000        // 整個交易耗時15秒
    },
    "success": true
  }
}
```

#### 情境範例 2: 玩家投入50元硬幣兌幣
**情境**: 玩家投入50元硬幣，機台自動出幣5個10元硬幣
```json
{
  "timestamp": "2025-09-12T10:35:00.000Z",
  "device_id": "CCM_001",
  "message_id": "uuid-002b",
  "message_type": "transaction",
  "version": "1.1",
  "data": {
    "transaction_type": "exchange",
    "transaction_id": "TXN_20250912_103500_001",
    "amounts": {
      "bills_inserted": 0,         // 未投入紙鈔
      "coins_inserted": 50,        // 投入50元硬幣
      "coins_dispensed": 5,        // 出幣5個
      "transaction_amount": 50,    // 交易金額50元
      "coin_value": 10             // 每個硬幣10元
    },
    "balance": {
      "before": 15000,            // 交易前餘額
      "after": 15050              // 交易後餘額增加50元
    },
    "timing": {
      "start_time": "2025-09-12T10:34:45.000Z",
      "dispense_time": "2025-09-12T10:35:00.000Z",
      "duration_ms": 15000
    },
    "success": true
  }
}
```

#### 情境範例 3a: 玩家投入500元紙鈔兌幣
**情境**: 玩家投入500元紙鈔，機台自動出幣50個10元硬幣
```json
{
  "timestamp": "2025-09-12T11:15:00.000Z",
  "device_id": "CCM_001",
  "message_id": "uuid-002c",
  "message_type": "transaction",
  "version": "1.1",
  "data": {
    "transaction_type": "exchange",
    "transaction_id": "TXN_20250912_111500_001",
    "amounts": {
      "bills_inserted": 500,       // 投入500元紙鈔
      "coins_inserted": 0,         // 未投入硬幣
      "coins_dispensed": 50,       // 出幣50個
      "transaction_amount": 500,   // 交易金額500元
      "coin_value": 10             // 每個硬幣10元
    },
    "balance": {
      "before": 15050,            // 交易前餘額
      "after": 15550              // 交易後餘額增加500元
    },
    "timing": {
      "start_time": "2025-09-12T11:14:45.000Z",
      "dispense_time": "2025-09-12T11:15:00.000Z",
      "duration_ms": 15000
    },
    "success": true
  }
}
```

#### 情境範例 3b: 玩家投入1000元紙鈔兌幣
**情境**: 玩家投入1000元紙鈔，機台自動出幣100個10元硬幣
```json
{
  "timestamp": "2025-09-12T11:45:00.000Z",
  "device_id": "CCM_001",
  "message_id": "uuid-002d",
  "message_type": "transaction",
  "version": "1.1",
  "data": {
    "transaction_type": "exchange",
    "transaction_id": "TXN_20250912_114500_001",
    "amounts": {
      "bills_inserted": 1000,      // 投入1000元紙鈔
      "coins_inserted": 0,         // 未投入硬幣
      "coins_dispensed": 100,      // 出幣100個
      "transaction_amount": 1000,  // 交易金額1000元
      "coin_value": 10             // 每個硬幣10元
    },
    "balance": {
      "before": 15550,            // 交易前餘額
      "after": 16550              // 交易後餘額增加1000元
    },
    "timing": {
      "start_time": "2025-09-12T11:44:30.000Z",
      "dispense_time": "2025-09-12T11:45:00.000Z",
      "duration_ms": 30000        // 出幣較多，時間較長
    },
    "success": true
  }
}
```

#### 情境範例 4: 遠端出幣
**情境**: 雲端系統遠端控制機台出幣5個硬幣

### 遠端出幣完整流程說明

#### 角色定義
1. **玩家**: 使用兌幣機的一般用戶
2. **管理者**: 兌幣機營運管理人員
3. **管理者APP**: 雲端管理平台的手機/網頁應用程式
4. **雲端伺服器**: IOTCoinChanger雲端管理系統
5. **兌幣機**: 現場的飛絡力兌幣機設備

#### 遠端出幣觸發情境
**故障補償情境**
1. 玩家投幣後機台故障，未正常出幣
2. 玩家向現場管理者反映或透過LINE Bot客服
3. 管理者確認故障情況並執行遠端補償出幣

#### 完整操作流程

```
玩家 → 管理者 → 管理者APP → 雲端伺服器 → 兌幣機 → 玩家
```

**步驟1: 問題回報**
```
玩家 → 管理者
- 玩家向現場管理者反映：「我投了100元但機台卡住沒出幣」
- 或透過LINE Bot客服系統回報問題
```

**步驟2: 情況確認**
```
管理者 → 現場檢查
- 管理者到現場查看機台狀況
- 確認機台確實有故障或需要補償
- 決定補償數量（例如：投入100元 = 補償10個10元硬幣）
```

**步驟3: 遠端操作**
```
管理者 → 管理者APP
- 管理者登入IOTCoinChanger管理APP
- 選擇對應的兌幣機（CCM_001）
- 選擇「遠端出幣」功能
- 輸入出幣數量：5個硬幣
- 輸入補償原因：「機台故障補償」
- 確認執行
```

**步驟4: 雲端處理**
```
管理者APP → 雲端伺服器
- APP將遠端出幣請求傳送到雲端伺服器
- 雲端伺服器驗證管理者權限
- 雲端伺服器記錄操作日誌
- 產生遠端控制命令
```

**步驟5: MQTT命令傳送**
```
雲端伺服器 → 兌幣機 (透過MQTT)
- 雲端發送遠端出幣命令到兌幣機
- 主題: coinerex/commands/CCM_001/coin_dispense
- 內容包含：出幣數量、操作原因、命令ID等
```

**步驟6: 兌幣機執行**
```
兌幣機接收並執行
- 兌幣機收到MQTT命令
- 驗證命令格式和權限
- 執行出幣動作：出幣5個10元硬幣
- 更新內部總帳記錄
```

**步驟7: 結果回報**
```
兌幣機 → 雲端伺服器 (透過MQTT)
- 兌幣機發送命令執行結果確認
- 發送transaction事件記錄遠端出幣
- 更新最新的accounting總帳資料
```

**步驟8: 狀態更新**
```
雲端伺服器 → 管理者APP
- 雲端更新操作狀態為「執行成功」
- 管理者APP顯示出幣完成通知
- 記錄到操作歷史中
```

**步驟9: 現場確認**
```
管理者 → 玩家
- 管理者確認機台已出幣
- 告知玩家問題已解決
- 玩家取得補償硬幣
```

#### 技術實作細節

**安全控制**:
- 只有具權限的管理者可執行遠端出幣
- 每次操作都有完整的審計記錄
- 設定每日/每次出幣上限避免誤操作

**離線處理**:
- 如果兌幣機離線，命令會暫存在雲端
- 兌幣機重新連線後自動執行暫存命令
- 超時未執行的命令會自動取消

**錯誤處理**:
- 如果兌幣機硬幣不足，會回報錯誤
- 如果機台故障無法出幣，會回報故障狀態
- 管理者APP會顯示具體的錯誤原因

#### 實際MQTT訊息範例
```json
{
  "timestamp": "2025-09-12T16:45:00.000Z",
  "device_id": "CCM_001",
  "message_id": "uuid-004",
  "message_type": "transaction",
  "version": "1.1", 
  "data": {
    "transaction_type": "remote_dispense",
    "transaction_id": "REMOTE_20250912_164500_001",
    "command_id": "CMD_789",      // 關聯的遠端控制命令ID
    "amounts": {
      "bills_inserted": 0,
      "coins_inserted": 0,
      "coins_dispensed": 5,       // 遠端出幣5個
      "transaction_amount": 0,    // 遠端出幣不涉及投幣金額
      "coin_value": 10
    },
    "balance": {
      "before": 15000,
      "after": 15000             // 餘額不變
    },
    "remote_details": {
      "operator_account": "ADMIN_001",    // 操作管理員帳號
      "coins_dispensed": 5,               // 出幣數量
      "reason": "故障補償"                // 操作原因
    },
    "success": true
  }
}
```

**伺服器回應**: 
```json
{
  "timestamp": "2025-09-12T10:30:01.000Z",
  "ack_message_id": "uuid-002",
  "status": "processed",
  "result": {
    "transaction_recorded": true,
    "points_awarded": 100,        // 如果有積分系統
    "next_maintenance": "2025-09-15T02:00:00.000Z"
  }
}
```

#### 交易類型對照
| 類型 | 說明 | 觸發者 | 影響餘額 |
|------|------|--------|----------|
| exchange | 一般兌幣 | 玩家投幣 | ✓ |
| remote_dispense | 遠端出幣 | 雲端系統 | ✗ |

### 3. 故障通知 (error)

主題: `coinerex/error/{device_id}`

#### 使用情境

**觸發時機**: 機台偵測到任何故障狀況時立即發送

#### 情境範例 1: 硬幣用盡故障
**情境**: 機台在玩家兌幣過程中發現退幣器硬幣用盡，無法完成出幣
```json
{
  "timestamp": "2025-09-12T10:30:00.000Z",
  "device_id": "CCM_001",
  "message_id": "uuid-003",
  "message_type": "error", 
  "version": "1.1",
  "data": {
    "error_code": 42,
    "error_description": "退幣器已無硬幣",
    "error_category": "dispenser",
    "severity": "critical",
    "suggested_action": "立即補充硬幣",
    "auto_recoverable": false,
    "affected_functions": ["coin_dispense", "exchange"],
    "context": {
      "coins_remaining": 0,        // 剩餘硬幣數
      "last_transaction": "TXN_20250912_102959_001",
      "pending_dispense": 8        // 尚未出完的硬幣數
    },
    "impact": {
      "service_available": false,  // 無法提供服務
      "estimated_downtime": "immediate_action_required"
    }
  }
}
```

#### 情境範例 2: 投幣器異常故障
**情境**: 機台偵測到投幣器訊號異常，可能有釣魚攻擊
```json
{
  "timestamp": "2025-09-12T11:45:30.000Z",
  "device_id": "CCM_001", 
  "message_id": "uuid-004",
  "message_type": "error",
  "version": "1.1",
  "data": {
    "error_code": 12,
    "error_description": "投幣器訊號-脈衝異常",
    "error_category": "coin_acceptor",
    "severity": "high",
    "suggested_action": "防釣魚機制，進設定解除故障",
    "auto_recoverable": false,
    "affected_functions": ["coin_accept", "exchange"],
    "context": {
      "detection_count": 5,        // 異常檢測次數
      "last_valid_pulse": "2025-09-12T11:44:00.000Z",
      "anomaly_type": "pulse_frequency_abnormal"
    },
    "security": {
      "suspected_attack": true,    // 疑似攻擊
      "auto_locked": true          // 自動鎖定機台
    }
  }
}
```

#### 情境範例 3: 紙鈔機通訊故障
**情境**: 機台與紙鈔驗鈔機RS232通訊中斷
```json
{
  "timestamp": "2025-09-12T13:20:15.000Z",
  "device_id": "CCM_001",
  "message_id": "uuid-005", 
  "message_type": "error",
  "version": "1.1",
  "data": {
    "error_code": 21,
    "error_description": "紙鈔機異常(RS232)",
    "error_category": "bill_acceptor", 
    "severity": "high",
    "suggested_action": "檢查紙鈔機連線和電源",
    "auto_recoverable": true,
    "affected_functions": ["bill_accept"],
    "context": {
      "communication_status": "disconnected",
      "last_response": "2025-09-12T13:19:45.000Z",
      "retry_count": 3,
      "recovery_attempts": 2
    },
    "recovery": {
      "auto_retry_enabled": true,
      "next_retry_time": "2025-09-12T13:20:45.000Z",
      "fallback_mode": "coin_only"  // 僅接受硬幣
    }
  }
}
```

**伺服器回應**: 
```json
{
  "timestamp": "2025-09-12T10:30:01.000Z",
  "ack_message_id": "uuid-003",
  "status": "processed",
  "result": {
    "alert_sent": true,
    "technician_dispatched": true,
    "estimated_arrival": "2025-09-12T11:00:00.000Z",
    "remote_actions": ["disable_coin_acceptance"],
    "priority_level": "urgent"
  }
}
```

### 4. 警報通知 (alarm)

主題: `coinerex/alarm/{device_id}`

#### 使用情境

**觸發時機**: 機台偵測到警告狀況但仍可繼續服務時發送

#### 情境範例 1: 低幣量警報
**情境**: 機台硬幣庫存降至警戒線以下，但仍可提供服務
```json
{
  "timestamp": "2025-09-12T15:30:00.000Z",
  "device_id": "CCM_001",
  "message_id": "uuid-006",
  "message_type": "alarm",
  "version": "1.1", 
  "data": {
    "alarm_code": 1,
    "alarm_description": "低幣量警報",
    "severity": "warning",
    "current_level": "低",
    "recommended_action": "儘快補充硬幣",
    "details": {
      "coins_remaining": 50,       // 剩餘硬幣數
      "warning_threshold": 100,    // 警告門檻
      "critical_threshold": 20,    // 危險門檻
      "estimated_service_time": "2小時", // 預估可服務時間
      "daily_average_usage": 200   // 日平均用量
    },
    "impact": {
      "service_available": true,   // 仍可提供服務
      "performance_degraded": false
    }
  }
}
```

#### 情境範例 2: 前門開啟警報
**情境**: 管理員打開機台前門進行維護，但忘記關閉
```json
{
  "timestamp": "2025-09-12T09:15:00.000Z",
  "device_id": "CCM_001",
  "message_id": "uuid-007",
  "message_type": "alarm",
  "version": "1.1",
  "data": {
    "alarm_code": 2,
    "alarm_description": "前門開啟警報",
    "severity": "warning",
    "current_level": "中", 
    "recommended_action": "檢查並關閉機台前門",
    "details": {
      "door_open_duration": "00:15:00", // 已開啟15分鐘
      "last_maintenance": "2025-09-12T09:00:00.000Z",
      "security_status": "monitoring",  // 安全監控中
      "camera_recording": true          // 攝影機記錄中
    },
    "impact": {
      "service_available": false,       // 前門開啟時停止服務
      "security_risk": "medium"
    }
  }
}
```

#### 情境範例 3: 暫停兌幣警報
**情境**: 管理員透過設定暫停兌幣功能
```json
{
  "timestamp": "2025-09-12T20:00:00.000Z", 
  "device_id": "CCM_001",
  "message_id": "uuid-008",
  "message_type": "alarm",
  "version": "1.1",
  "data": {
    "alarm_code": 3,
    "alarm_description": "暫停兌幣模式",
    "severity": "info",
    "current_level": "暫停",
    "recommended_action": "檢查設定狀態或聯絡管理員",
    "details": {
      "pause_reason": "scheduled_maintenance", // 定期維護
      "paused_by": "ADMIN_001",                // 操作員
      "pause_start_time": "2025-09-12T20:00:00.000Z",
      "scheduled_resume_time": "2025-09-13T08:00:00.000Z",
      "manual_resume_required": false          // 自動恢復
    },
    "impact": {
      "service_available": false,
      "estimated_downtime": "12小時"
    }
  }
}
```

**伺服器回應**: 
```json
{
  "timestamp": "2025-09-12T15:30:01.000Z",
  "ack_message_id": "uuid-006", 
  "status": "processed",
  "result": {
    "alert_level": "medium",
    "notification_sent": ["LINE", "Telegram"],
    "maintenance_scheduled": true,
    "scheduled_time": "2025-09-12T17:00:00.000Z",
    "technician_assigned": "TECH_002"
  }
}
```

### 5. 心跳信號 (heartbeat)

主題: `coinerex/heartbeat/{device_id}`

#### 使用情境

**觸發時機**: 每5分鐘自動發送，確認機台在線狀態

#### 情境範例 1: 正常運作心跳
**情境**: 機台正常運作中，定期發送狀態心跳
```json
{
  "timestamp": "2025-09-12T10:30:00.000Z",
  "device_id": "CCM_001",
  "message_id": "uuid-009",
  "message_type": "heartbeat",
  "version": "1.1",
  "data": {
    "status": "online",
    "firmware_version": "1.3.2",
    "uptime_seconds": 86400,      // 運行24小時
    "last_transaction": "2025-09-12T10:25:00.000Z",
    "network_quality": "excellent",
    "system_health": {
      "cpu_usage": 25,            // CPU使用率25%
      "memory_usage": 45,         // 記憶體使用率45%
      "storage_usage": 60,        // 儲存空間使用率60%
      "temperature": 35           // 系統溫度35°C
    },
    "service_status": {
      "coin_acceptor": "operational",
      "bill_acceptor": "operational", 
      "dispenser": "operational",
      "display": "operational"
    },
    "statistics": {
      "transactions_today": 45,   // 今日交易筆數
      "coins_dispensed_today": 890, // 今日出幣數
      "error_count_today": 0,     // 今日錯誤次數
      "last_maintenance": "2025-09-10T08:00:00.000Z"
    }
  }
}
```

#### 情境範例 2: 異常狀態心跳
**情境**: 機台運作中但有部分功能異常
```json
{
  "timestamp": "2025-09-12T14:30:00.000Z",
  "device_id": "CCM_001", 
  "message_id": "uuid-010",
  "message_type": "heartbeat",
  "version": "1.1",
  "data": {
    "status": "degraded",         // 降級運作
    "firmware_version": "1.3.2",
    "uptime_seconds": 100800,
    "last_transaction": "2025-09-12T14:20:00.000Z", 
    "network_quality": "good",
    "system_health": {
      "cpu_usage": 45,
      "memory_usage": 70,         // 記憶體使用率較高
      "storage_usage": 85,        // 儲存空間不足警告
      "temperature": 42           // 溫度偏高
    },
    "service_status": {
      "coin_acceptor": "operational",
      "bill_acceptor": "offline",  // 紙鈔機離線
      "dispenser": "operational",
      "display": "operational"
    },
    "active_issues": [
      {
        "issue_type": "bill_acceptor_offline",
        "since": "2025-09-12T13:15:00.000Z",
        "impact": "only_coins_accepted"
      }
    ],
    "statistics": {
      "transactions_today": 32,
      "coins_dispensed_today": 640,
      "error_count_today": 2,
      "last_maintenance": "2025-09-10T08:00:00.000Z"
    }
  }
}
```

**伺服器回應**: 心跳信號通常不需要ACK回應，但伺服器可選擇性回應
```json
{
  "timestamp": "2025-09-12T10:30:02.000Z",
  "device_id": "CCM_001",
  "message_type": "heartbeat_response",
  "data": {
    "server_time": "2025-09-12T10:30:02.000Z",
    "next_maintenance": "2025-09-15T02:00:00.000Z",
    "config_version": "2.1.0",
    "update_available": false
  }
}
```

### 6. 遠端控制命令

#### 使用情境

**觸發時機**: 雲端管理系統需要遠端控制機台時發送

#### 遠端出幣命令

主題: `coinerex/commands/{device_id}/coin_dispense`

**情境範例**: 客戶投訴機台故障未出幣，客服人員遠端補償出幣

**步驟1 - 雲端發送命令**:
```json
{
  "timestamp": "2025-09-12T16:30:00.000Z",
  "command_id": "CMD_20250912_001",
  "command_type": "coin_dispense",
  "requires_ack": true,
  "priority": "high",
  "data": {
    "coins_to_dispense": 5,      // 出幣5個
    "coin_value": 10,            // 10元硬幣
    "timeout_seconds": 30,       // 30秒超時
    "reason": "故障補償",           // 操作原因
    "operator_account": "STAFF_001"  // 操作員帳號
  }
}
```

**步驟2 - 機台執行並回應**:
```json
{
  "timestamp": "2025-09-12T16:30:15.000Z",
  "ack_command_id": "CMD_20250912_001",
  "status": "success",
  "result": {
    "coins_dispensed": 5,        // 實際出幣數
    "execution_time_ms": 12500,  // 執行時間12.5秒
    "coins_remaining": 195,      // 剩餘硬幣庫存
    "transaction_id": "REMOTE_20250912_163015_001" // 新交易ID
  }
}
```

#### 機台重啟命令

主題: `coinerex/commands/{device_id}/restart`

**情境範例**: 機台軟體異常，需要遠端重啟恢復正常

**步驟1 - 雲端發送命令**:
```json
{
  "timestamp": "2025-09-12T02:30:00.000Z",
  "command_id": "CMD_20250912_002", 
  "command_type": "restart",
  "requires_ack": true,
  "priority": "medium",
  "data": {
    "restart_type": "soft",      // 軟重啟
    "delay_seconds": 60,         // 延遲60秒執行
    "reason": "system_recovery", // 系統恢復
    "maintenance_window": true,  // 維護時段
    "operator_id": "SYSTEM_AUTO" // 自動操作
  }
}
```

**步驟2 - 機台執行並回應**:
```json
{
  "timestamp": "2025-09-12T02:31:00.000Z",
  "ack_command_id": "CMD_20250912_002",
  "status": "success", 
  "result": {
    "restart_initiated": true,
    "shutdown_time": "2025-09-12T02:31:00.000Z",
    "expected_boot_time": "2025-09-12T02:33:00.000Z",
    "data_backup_completed": true,
    "active_transactions": 0     // 無進行中交易
  }
}
```

#### 機台鎖定/解鎖命令

主題: `coinerex/commands/{device_id}/lock`

**情境範例**: 發現機台異常行為，緊急鎖定機台停止服務

**步驟1 - 雲端發送鎖定命令**:
```json
{
  "timestamp": "2025-09-12T11:45:00.000Z",
  "command_id": "CMD_20250912_003",
  "command_type": "lock",
  "requires_ack": true,
  "priority": "urgent",
  "data": {
    "action": "lock",            // 鎖定機台
    "reason": "security_incident", // 安全事件
    "duration_minutes": 120,     // 鎖定120分鐘
    "operator_id": "SECURITY_001",
    "message_display": "機台維護中，暫停服務",
    "allow_emergency_unlock": false // 不允許緊急解鎖
  }
}
```

**步驟2 - 機台執行並回應**:
```json
{
  "timestamp": "2025-09-12T11:45:02.000Z",
  "ack_command_id": "CMD_20250912_003",
  "status": "success",
  "result": {
    "action_completed": "locked",
    "lock_start_time": "2025-09-12T11:45:02.000Z",
    "lock_end_time": "2025-09-12T13:45:02.000Z",
    "display_message_set": true,
    "services_disabled": ["coin_accept", "bill_accept", "dispense"],
    "monitoring_active": true    // 監控功能仍運作
  }
}
```

**步驟3 - 解鎖命令**:
```json
{
  "timestamp": "2025-09-12T13:00:00.000Z",
  "command_id": "CMD_20250912_004",
  "command_type": "lock", 
  "requires_ack": true,
  "data": {
    "action": "unlock",          // 解鎖機台
    "reason": "issue_resolved",  // 問題已解決
    "operator_id": "TECH_002",
    "verification_required": true // 需要技術員現場驗證
  }
}
```

#### 查詢狀態命令

主題: `coinerex/commands/{device_id}/query`

**情境範例**: 客服需要即時查詢機台當前狀態

```json
{
  "timestamp": "2025-09-12T14:15:00.000Z",
  "command_id": "CMD_20250912_005",
  "command_type": "query",
  "requires_ack": false,       // 查詢不需ACK
  "data": {
    "query_type": "full_status", // 完整狀態查詢
    "include_diagnostics": true, // 包含診斷資訊
    "operator_id": "SUPPORT_003"
  }
}
```

**機台回應**: 立即透過相應主題發送最新狀態資訊（總帳、心跳等）

## 錯誤碼對照表

### Error Code (故障碼)

| 代碼 | 故障原因 | 對策 | 嚴重程度 |
|------|----------|------|----------|
| 01 | 記憶異常 | 送修 | Critical |
| 02 | 碼錶異常 | 檢查碼錶是否異常或配線 | High |
| 06 | 兌幣設定異常 | 檢查出幣設定，設定後重開 | Medium |
| 07 | 入幣設定異常 | 檢查入幣設定，設定後重開 | Medium |
| 08 | 紙鈔設定異常(RS232) | 檢查紙鈔設定，設定後重開 | Medium |
| 09 | 紙鈔設定異常(Pulse) | 檢查紙鈔設定，設定後重開 | Medium |
| 11 | 投幣器訊號間隔過短 | 防電擊機制，進設定解除故障 | High |
| 12 | 投幣器訊號-脈衝異常 | 防釣魚機制，進設定解除故障 | High |
| 13 | 投幣器訊號常駐 | 沒接投幣器或配線/未扳NO | High |
| 21 | 紙鈔機異常(RS232) | 檢查紙鈔機 | High |
| 22 | 紙鈔機訊號-脈衝異常 | 防釣魚機制，進設定解除故障 | High |
| 23 | 紙鈔器訊號常駐 | 沒接紙鈔機或配線/未扳NC | High |
| 41 | 退幣器故障 | 檢查退幣機有無異常 | Critical |
| 42 | 退幣器已無硬幣 | 補充硬幣 | Critical |
| 43 | 退幣機異常出幣 | 防電擊機制，進設定解除故障 | High |
| 44 | 退幣器達低水位 | 補充硬幣 | High |
| 51 | 兌幣紀錄異常 | 進設定清除上一筆交易內容 | Medium |
| 52 | 達出幣上限 | 進後台結算功能歸0 | Medium |
| 99 | 遠端預警異常鎖機 | 進設定解除故障 | High |

### Alarm Code (警告碼)

| 代碼 | 警告原因 | 處理方式 |
|------|----------|----------|
| 01 | 低幣量 | 儘快補充硬幣 |
| 02 | 前門開啟 | 檢查門鎖狀態 |
| 03 | 暫停兌幣 | 檢查設定狀態 |

## 實作範例

### Python MQTT 客戶端範例

```python
import json
import uuid
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional
import paho.mqtt.client as mqtt

class CoinerMQTTClient:
    def __init__(self, device_id: str, broker_host: str, broker_port: int = 1883):
        self.device_id = device_id
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        # ACK 追蹤
        self.pending_acks: Dict[str, Dict] = {}  # message_id -> {"timestamp": ..., "retry_count": ...}
        self.ack_timeout = 10  # 首次超時時間（秒）
        self.max_retries = 3
        self.retry_intervals = [10, 30, 60]  # 重試間隔

        # 離線訊息快取
        self.offline_cache = []
        self.max_cache_size = 100

        # 交易ID計數器
        self.transaction_counters = {
            "TXN": 0,
            "REMOTE": 0
        }
        self.last_date = ""  # 追蹤日期變更
        
        # 啟動ACK監控執行緒
        self.ack_monitor_thread = threading.Thread(target=self._monitor_acks, daemon=True)
        self.ack_monitor_thread.start()
        
    def connect(self, broker_host: str, broker_port: int):
        self.client.connect(broker_host, broker_port, 60)
        
    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected with result code {rc}")
        # 訂閱控制命令和ACK回應
        client.subscribe(f"coinerex/commands/{self.device_id}/+")
        client.subscribe(f"coinerex/ack/{self.device_id}")
        
        # 連線後發送離線快取訊息
        self._send_cached_messages()
        
    def on_message(self, client, userdata, msg):
        try:
            topic_parts = msg.topic.split('/')
            
            if topic_parts[-1] == "ack" and topic_parts[-2] == self.device_id:
                # 處理ACK回應
                ack_data = json.loads(msg.payload.decode())
                self._handle_ack(ack_data)
            else:
                # 處理控制命令
                command = json.loads(msg.payload.decode())
                self.handle_command(command)
        except Exception as e:
            print(f"Error processing message: {e}")
    
    def _publish_with_ack(self, topic: str, message: Dict[str, Any], requires_ack: bool = False):
        """發布訊息，如需要ACK則加入追蹤列表"""
        message_json = json.dumps(message)
        
        try:
            # 統一使用 QoS 0
            result = self.client.publish(topic, message_json, qos=0)
            
            if requires_ack:
                # 加入ACK追蹤列表
                self.pending_acks[message["message_id"]] = {
                    "timestamp": time.time(),
                    "retry_count": 0,
                    "topic": topic,
                    "message": message,
                    "requires_ack": requires_ack
                }
                
            return True
        except Exception as e:
            print(f"Failed to publish message: {e}")
            # 如果是重要訊息，加入離線快取
            if requires_ack:
                self._cache_message(topic, message)
            return False
    
    def _handle_ack(self, ack_data: Dict[str, Any]):
        """處理收到的ACK確認"""
        ack_message_id = ack_data.get("ack_message_id")
        
        if ack_message_id in self.pending_acks:
            status = ack_data.get("status", "received")
            if status in ["received", "processed"]:
                # 收到正確的ACK，移除追蹤
                del self.pending_acks[ack_message_id]
                print(f"ACK confirmed for message: {ack_message_id}")
            else:
                print(f"ACK error for message {ack_message_id}: {ack_data.get('error_message', 'Unknown error')}")
    
    def _monitor_acks(self):
        """監控ACK超時並處理重傳"""
        while True:
            current_time = time.time()
            messages_to_retry = []
            
            for message_id, ack_info in list(self.pending_acks.items()):
                time_elapsed = current_time - ack_info["timestamp"]
                retry_count = ack_info["retry_count"]
                
                if retry_count < self.max_retries:
                    expected_timeout = self.retry_intervals[retry_count]
                    if time_elapsed >= expected_timeout:
                        messages_to_retry.append((message_id, ack_info))
                else:
                    # 超過最大重試次數，放棄
                    print(f"Message {message_id} failed after {self.max_retries} retries")
                    del self.pending_acks[message_id]
            
            # 執行重傳
            for message_id, ack_info in messages_to_retry:
                self._retry_message(message_id, ack_info)
            
            time.sleep(5)  # 每5秒檢查一次
    
    def _retry_message(self, message_id: str, ack_info: Dict):
        """重傳訊息"""
        ack_info["retry_count"] += 1
        ack_info["timestamp"] = time.time()
        
        topic = ack_info["topic"]
        message = ack_info["message"]
        
        print(f"Retrying message {message_id}, attempt {ack_info['retry_count']}")
        
        try:
            self.client.publish(topic, json.dumps(message), qos=0)
        except Exception as e:
            print(f"Failed to retry message {message_id}: {e}")
    
    def _cache_message(self, topic: str, message: Dict[str, Any]):
        """快取離線訊息"""
        if len(self.offline_cache) >= self.max_cache_size:
            self.offline_cache.pop(0)  # 移除最舊的訊息
            
        self.offline_cache.append({
            "topic": topic,
            "message": message,
            "timestamp": time.time()
        })
    
    def _send_cached_messages(self):
        """發送離線快取的訊息"""
        for cached in self.offline_cache:
            topic = cached["topic"]
            message = cached["message"]
            
            # 重新生成訊息ID避免重複
            message["message_id"] = str(uuid.uuid4())
            message["timestamp"] = datetime.utcnow().isoformat() + "Z"
            
            self._publish_with_ack(topic, message, requires_ack=True)
        
        self.offline_cache.clear()

    def generate_transaction_id(self, transaction_type: str) -> str:
        """生成交易ID"""
        now = datetime.now()
        current_date = now.strftime("%Y%m%d")
        current_time = now.strftime("%H%M%S")

        # 檢查日期是否變更，如果是則重置計數器
        if current_date != self.last_date:
            self.transaction_counters = {"TXN": 0, "REMOTE": 0}
            self.last_date = current_date

        # 根據交易類型選擇前綴
        type_mapping = {
            "exchange": "TXN",
            "remote_dispense": "REMOTE"
        }

        prefix = type_mapping.get(transaction_type, "TXN")

        # 遞增計數器
        self.transaction_counters[prefix] += 1
        seq = f"{self.transaction_counters[prefix]:03d}"

        return f"{prefix}_{current_date}_{current_time}_{seq}"

    def publish_accounting(self, accounting_data: Dict[str, Any]):
        """發布總帳資料"""
        message = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "device_id": self.device_id,
            "message_id": str(uuid.uuid4()),
            "message_type": "accounting",
            "version": "1.1",
            "data": accounting_data
        }
        
        topic = f"coinerex/accounting/{self.device_id}"
        return self._publish_with_ack(topic, message, requires_ack=True)
        
    def publish_transaction(self, transaction_data: Dict[str, Any]):
        """發布交易事件"""
        message = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "device_id": self.device_id,
            "message_id": str(uuid.uuid4()),
            "message_type": "transaction", 
            "version": "1.1",
            "data": transaction_data
        }
        
        topic = f"coinerex/transaction/{self.device_id}"
        return self._publish_with_ack(topic, message, requires_ack=True)
        
    def publish_error(self, error_code: int, description: str):
        """發布故障通知"""
        message = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "device_id": self.device_id,
            "message_id": str(uuid.uuid4()),
            "message_type": "error",
            "version": "1.1", 
            "data": {
                "error_code": error_code,
                "error_description": description,
                "severity": self.get_error_severity(error_code),
                "error_category": self.get_error_category(error_code),
                "suggested_action": self.get_suggested_action(error_code)
            }
        }
        
        topic = f"coinerex/error/{self.device_id}"
        return self._publish_with_ack(topic, message, requires_ack=True)
        
    def publish_heartbeat(self, heartbeat_data: Dict[str, Any]):
        """發布心跳訊息"""
        message = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "device_id": self.device_id,
            "message_id": str(uuid.uuid4()),
            "message_type": "heartbeat",
            "version": "1.1",
            "data": heartbeat_data
        }
        
        topic = f"coinerex/heartbeat/{self.device_id}"
        return self._publish_with_ack(topic, message, requires_ack=False)
        
    def handle_command(self, command: Dict[str, Any]):
        """處理雲端控制命令"""
        command_type = command.get("command_type")
        command_id = command.get("command_id")
        requires_ack = command.get("requires_ack", False)
        
        try:
            if command_type == "coin_dispense":
                coins = command["data"]["coins_to_dispense"] 
                result = self.dispense_coins(coins)
                if requires_ack:
                    self.send_command_ack(command_id, "success", result)
                    
            elif command_type == "restart":
                restart_type = command["data"].get("restart_type", "soft")
                result = self.restart_device(restart_type)
                if requires_ack:
                    self.send_command_ack(command_id, "success", result)
                    
            elif command_type == "lock":
                action = command["data"]["action"]
                result = self.lock_device(action)
                if requires_ack:
                    self.send_command_ack(command_id, "success", result)
                    
        except Exception as e:
            if requires_ack:
                self.send_command_ack(command_id, "failed", {"error": str(e)})
    
    def send_command_ack(self, command_id: str, status: str, result: Dict[str, Any]):
        """發送命令執行結果確認"""
        ack_message = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "ack_command_id": command_id,
            "status": status,
            "result": result
        }
        
        topic = f"coinerex/commands/{self.device_id}/ack"
        self.client.publish(topic, json.dumps(ack_message), qos=0)
            
    def get_error_severity(self, error_code: int) -> str:
        """根據錯誤碼判斷嚴重程度"""
        critical_codes = [1, 41, 42]
        high_codes = [2, 11, 12, 13, 21, 22, 23, 43, 44, 99]
        
        if error_code in critical_codes:
            return "critical"
        elif error_code in high_codes:
            return "high" 
        else:
            return "medium"
    
    def get_error_category(self, error_code: int) -> str:
        """根據錯誤碼分類"""
        if error_code in [1]:
            return "system"
        elif error_code in [2]:
            return "counter"
        elif error_code in [11, 12, 13]:
            return "coin_acceptor"
        elif error_code in [21, 22, 23]:
            return "bill_acceptor"
        elif error_code in [41, 42, 43, 44]:
            return "dispenser"
        else:
            return "general"
    
    def get_suggested_action(self, error_code: int) -> str:
        """根據錯誤碼提供建議處理方式"""
        actions = {
            1: "送修",
            2: "檢查碼錶是否異常或配線",
            42: "補充硬幣",
            44: "補充硬幣"
        }
        return actions.get(error_code, "檢查設備狀態")
    
    # 這些方法需要根據實際硬體介面實作
    def dispense_coins(self, coins: int) -> Dict[str, Any]:
        """執行出幣操作"""
        # 實際硬體控制邏輯
        return {"coins_dispensed": coins, "execution_time_ms": 1500}
    
    def restart_device(self, restart_type: str) -> Dict[str, Any]:
        """執行設備重啟"""
        # 實際重啟邏輯
        return {"restart_type": restart_type, "status": "completed"}
    
    def lock_device(self, action: str) -> Dict[str, Any]:
        """執行設備鎖定/解鎖"""
        # 實際鎖定邏輯
        return {"action": action, "status": "completed"}
```

### 使用範例

```python
# 初始化客戶端
client = CoinerMQTTClient("CCM_001", "mqtt.coinerex.com")
client.connect("mqtt.coinerex.com", 1883)

# 發布交易事件（需要ACK確認）
transaction_data = {
    "transaction_type": "exchange",
    "transaction_id": client.generate_transaction_id("exchange"),  # 自動生成交易ID
    "amounts": {
        "bills_inserted": 100,
        "coins_inserted": 0,
        "coins_dispensed": 10,
        "transaction_amount": 100
    },
    "balance": {
        "before": 14900,
        "after": 15000
    },
    "success": True
}

success = client.publish_transaction(transaction_data)
if success:
    print("Transaction message sent, waiting for ACK...")

# 發布故障通知（需要ACK確認）
client.publish_error(42, "退幣器已無硬幣")

# 發布心跳訊息（不需要ACK）
heartbeat_data = {
    "status": "online",
    "firmware_version": "1.3",
    "uptime_seconds": 86400,
    "last_transaction": "2025-09-12T09:45:00.000Z",
    "network_quality": "good",
    "memory_usage": 45
}

client.publish_heartbeat(heartbeat_data)

# 啟動訊息循環
client.client.loop_forever()
```

### 雲端ACK回應範例

雲端收到重要訊息後，應該透過ACK主題回應確認：

```python
def send_ack_response(device_id: str, message_id: str, status: str = "received"):
    """雲端發送ACK確認"""
    ack_response = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "ack_message_id": message_id,
        "status": status,  # "received", "processed", "error"
        "error_message": None  # 如果status是error時填入
    }
    
    topic = f"coinerex/ack/{device_id}"
    mqtt_client.publish(topic, json.dumps(ack_response), qos=0)
```

## 注意事項

### 安全性考量
1. **認證機制**: 使用用戶名/密碼或證書進行MQTT認證
2. **資料加密**: 敏感資料建議使用TLS加密傳輸
3. **存取控制**: 設定適當的主題發布/訂閱權限

### 效能優化
1. **訊息批次**: 非緊急訊息可考慮批次傳送
2. **壓縮**: 大量資料可使用JSON壓縮
3. **連線保持**: 使用Keep Alive機制維持連線
4. **QoS 0優化**: 統一使用QoS 0減少網路負擔

### 握手機制最佳實務
1. **ACK響應時間**: 雲端應在收到訊息後5秒內回應ACK
2. **重傳策略**: 使用指數退避避免網路擁塞
3. **訊息去重**: 透過message_id進行重複訊息檢測
4. **離線處理**: 妥善處理網路斷線期間的訊息快取

### 監控與維運
1. **日誌記錄**: 記錄所有MQTT訊息與錯誤
2. **監控指標**: 監控訊息發送成功率、ACK確認率、重傳次數等
3. **告警機制**: 設定關鍵指標告警
4. **ACK統計**: 監控ACK確認成功率和延遲

### 版本相容性
1. **向下相容**: 新版本需支援舊版本訊息格式
2. **漸進升級**: 支援設備分批升級協定版本
3. **版本識別**: 透過version欄位識別協定版本

---

**文件維護**: 本文件隨著系統演進持續更新，請確保使用最新版本。
**聯絡資訊**: 如有疑問請聯絡開發團隊。