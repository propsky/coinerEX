# 兌幣機管理系統規劃書

## 1. 專案概述

### 1.1 專案背景
飛絡力兌幣機系統目前使用擎天有限公司設計的IPC上網架構，透過LINE OA帳號登入並使用LINE Frontend (LIFF)架構。由於LINE Message API每月費用過高（800元/3000訊息），需要遷移至成本更低的Telegram推播系統。

### 1.2 專案目標
- 建立新的兌幣機雲端管理平台
- 整合MQTT資料傳輸至新資料庫
- 遷移推播系統從LINE到Telegram
- 確保與舊系統UI的相容性
- 提供使用者友善的網路參數設定介面

### 1.3 專案範圍
- 約100台兌幣機設備管理
- 每台每月約1000個推播訊息
- 推播內容：故障通知、兌幣通知
- 硬體：Nano Pi M1plus主板 + Debian系統 + Python介面

## 2. 現有系統分析

### 2.1 現有架構
```
兌幣機硬體 → IPC控制器 → 擎天管理系統 → LINE LIFF → 使用者
```

### 2.2 現有功能
- 使用者透過LINE OA登入
- 機台狀態即時監控
- 故障通知推播
- 兌幣紀錄查詢
- 遠端補幣功能
- 系統參數設定

### 2.3 現有問題
- LINE推播成本過高（每月約2.6萬元）
- 硬體設定介面複雜
- 缺乏統一的資料管理平台
- MQTT資料未有效整合

## 3. 新系統架構設計

### 3.1 整體系統架構
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   兌幣機硬體     │    │    IPC控制器      │    │    雲端管理平台      │
│                 │◄──►│                  │◄──►│                     │
│ • 兌幣機制      │    │ • Nano Pi M1+    │    │ • Web應用伺服器     │
│ • 感應器        │    │ • Debian系統     │    │ • 資料庫伺服器      │
│ • 狀態指示      │    │ • Python介面     │    │ • MQTT Broker       │
└─────────────────┘    │ • MQTT Client    │    │ • Telegram Bot      │
                       └──────────────────┘    └─────────────────────┘
                                                           │
                                                           ▼
                                               ┌─────────────────────┐
                                               │   使用者介面        │
                                               │                     │
                                               │ • Web管理介面       │
                                               │ • Telegram通知      │
                                               │ • 行動裝置支援       │
                                               └─────────────────────┘
```

### 3.2 技術架構

#### 3.2.1 後端技術堆疊
- **應用框架**: Node.js + Express.js / Python + FastAPI
- **資料庫**: PostgreSQL（主資料庫） + Redis（快取）
- **訊息佇列**: MQTT Broker（Eclipse Mosquitto）
- **推播服務**: Telegram Bot API
- **認證系統**: JWT + OAuth 2.0

#### 3.2.2 前端技術堆疊
- **框架**: React.js + TypeScript
- **UI庫**: Ant Design / Material-UI
- **狀態管理**: Redux Toolkit
- **圖表庫**: Chart.js / ECharts
- **行動支援**: PWA（Progressive Web App）

#### 3.2.3 基礎設施
- **雲端平台**: AWS / Google Cloud / Azure
- **容器化**: Docker + Docker Compose
- **反向代理**: Nginx
- **SSL憑證**: Let's Encrypt
- **監控**: Prometheus + Grafana

### 3.3 資料庫設計

#### 3.3.1 核心資料表

```sql
-- 使用者管理
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    telegram_chat_id BIGINT,
    role VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 機台管理
CREATE TABLE machines (
    id SERIAL PRIMARY KEY,
    machine_code VARCHAR(20) UNIQUE NOT NULL,
    machine_name VARCHAR(100) NOT NULL,
    location VARCHAR(200),
    ipc_serial VARCHAR(50),
    status VARCHAR(20) DEFAULT 'online',
    owner_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 機台狀態記錄
CREATE TABLE machine_status (
    id SERIAL PRIMARY KEY,
    machine_id INTEGER REFERENCES machines(id),
    status VARCHAR(20) NOT NULL,
    error_code VARCHAR(10),
    error_message TEXT,
    coin_count INTEGER DEFAULT 0,
    temperature DECIMAL(5,2),
    humidity DECIMAL(5,2),
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 兌幣交易記錄
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    machine_id INTEGER REFERENCES machines(id),
    transaction_type VARCHAR(20) NOT NULL, -- 'exchange', 'refill'
    coin_amount INTEGER NOT NULL,
    cash_amount DECIMAL(10,2),
    user_identifier VARCHAR(100),
    status VARCHAR(20) DEFAULT 'completed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 推播記錄
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    machine_id INTEGER REFERENCES machines(id),
    user_id INTEGER REFERENCES users(id),
    notification_type VARCHAR(30) NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    channel VARCHAR(20) DEFAULT 'telegram',
    status VARCHAR(20) DEFAULT 'pending',
    sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- MQTT訊息日誌
CREATE TABLE mqtt_logs (
    id SERIAL PRIMARY KEY,
    machine_id INTEGER REFERENCES machines(id),
    topic VARCHAR(200) NOT NULL,
    payload JSONB NOT NULL,
    qos INTEGER DEFAULT 0,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3.3.2 索引優化
```sql
-- 查詢效能優化索引
CREATE INDEX idx_machine_status_machine_recorded ON machine_status(machine_id, recorded_at DESC);
CREATE INDEX idx_transactions_machine_created ON transactions(machine_id, created_at DESC);
CREATE INDEX idx_notifications_user_status ON notifications(user_id, status);
CREATE INDEX idx_mqtt_logs_machine_received ON mqtt_logs(machine_id, received_at DESC);
```

## 4. 功能模組規劃

### 4.1 前端頁面設計

#### 4.1.1 主要頁面結構
```
├── 登入系統
│   ├── 登入頁面（支援多種登入方式）
│   └── 使用者條款確認
├── 儀表板
│   ├── 總覽統計
│   ├── 機台狀態總覽
│   └── 即時通知
├── 機台管理
│   ├── 機台列表
│   ├── 機台狀態詳情
│   ├── 機台設定編輯
│   └── 遠端補幣功能
├── 交易記錄
│   ├── 兌幣記錄查詢
│   ├── 補幣記錄查詢
│   └── 收益統計圖表
├── 系統設定
│   ├── 個人資料設定
│   ├── 通知設定
│   └── 系統參數設定
└── 側邊導航
    ├── 機台狀態
    ├── 交易記錄
    ├── 系統設定
    └── 說明文件
```

#### 4.1.2 響應式設計規格
- **桌面版**: >= 1200px（完整功能）
- **平板版**: 768px - 1199px（適配佈局）
- **手機版**: < 768px（精簡介面）
- **PWA支援**: 離線快取、推播通知

### 4.2 核心功能模組

#### 4.2.1 機台狀態管理
```javascript
// 功能清單
- 即時狀態顯示（線上/離線/故障）
- 故障代碼解析與說明
- 硬體參數監控（溫度、濕度、幣量）
- 歷史狀態趨勢圖表
- 預測性維護提醒
```

#### 4.2.2 遠端補幣系統
```javascript
// 補幣流程
1. 驗證使用者權限
2. 檢查機台狀態
3. 發送補幣指令（MQTT）
4. 確認補幣結果
5. 記錄操作日誌
6. 發送完成通知
```

#### 4.2.3 通知推播系統
```javascript
// 推播規則設定
- 故障通知：立即推播
- 兌幣通知：每小時彙整
- 維護提醒：每日/每週
- 自定義推播條件
```

## 5. API設計與MQTT整合

### 5.1 RESTful API設計

#### 5.1.1 API端點規劃
```yaml
# 認證相關
POST /api/auth/login          # 使用者登入
POST /api/auth/logout         # 使用者登出
POST /api/auth/refresh        # Token刷新

# 機台管理
GET    /api/machines          # 取得機台列表
GET    /api/machines/:id      # 取得特定機台資訊
PUT    /api/machines/:id      # 更新機台設定
POST   /api/machines/:id/refill # 執行遠端補幣

# 狀態監控
GET    /api/machines/:id/status    # 取得機台即時狀態
GET    /api/machines/:id/history   # 取得歷史狀態記錄

# 交易記錄
GET    /api/transactions      # 取得交易記錄
GET    /api/transactions/stats # 取得統計資料

# 通知系統
GET    /api/notifications     # 取得通知列表
POST   /api/notifications     # 發送自定義通知
PUT    /api/notifications/:id # 標記通知已讀
```

#### 5.1.2 API資料格式
```json
// 機台狀態API回應格式
{
  "success": true,
  "data": {
    "machineId": "MC001",
    "status": "online",
    "lastUpdate": "2024-01-15T10:30:00Z",
    "sensors": {
      "temperature": 25.6,
      "humidity": 60.2,
      "coinCount": 450
    },
    "errors": [],
    "uptime": 86400
  },
  "timestamp": "2024-01-15T10:35:00Z"
}
```

### 5.2 MQTT整合方案

#### 5.2.1 主題結構設計
```
coinchanger/
├── machines/
│   ├── {machine_id}/
│   │   ├── status          # 機台狀態更新
│   │   ├── transactions    # 兌幣交易資料
│   │   ├── errors          # 錯誤訊息
│   │   ├── sensors         # 感應器資料
│   │   └── commands/       # 控制指令
│   │       ├── refill      # 補幣指令
│   │       ├── reset       # 重置指令
│   │       └── config      # 設定更新
└── system/
    ├── heartbeat          # 系統心跳
    ├── broadcasts         # 廣播訊息
    └── maintenance        # 維護通知
```

#### 5.2.2 MQTT訊息格式
```json
// 機台狀態更新訊息
{
  "machineId": "MC001",
  "timestamp": "2024-01-15T10:30:00Z",
  "status": "online",
  "data": {
    "coinCount": 450,
    "temperature": 25.6,
    "humidity": 60.2,
    "errorCode": null
  }
}

// 補幣指令訊息
{
  "commandId": "cmd_001",
  "machineId": "MC001",
  "command": "refill",
  "parameters": {
    "coinAmount": 100
  },
  "timestamp": "2024-01-15T10:35:00Z",
  "userId": "admin001"
}
```

## 6. 推播系統遷移計畫

### 6.1 Telegram整合規劃

#### 6.1.1 Bot功能設計
```javascript
// Telegram Bot指令
/start     - 開始使用並綁定帳號
/status    - 查詢機台狀態
/history   - 查詢交易記錄
/settings  - 通知設定
/help      - 使用說明
```

#### 6.1.2 通知模板設計
```markdown
🔴 【故障通知】
機台：MC001 - 店名01
狀態：通訊異常 (錯誤代碼: E44)
時間：2024-01-15 10:30
請儘速檢查機台狀況

🟢 【兌幣通知】
機台：MC001 - 店名01  
兌幣：100枚 (剩餘: 350枚)
時間：2024-01-15 10:35

🔵 【補幣完成】
機台：MC001 - 店名01
補幣：100枚 (總計: 450枚)
時間：2024-01-15 10:40
操作者：管理員
```

### 6.2 遷移時程規劃

#### 6.2.1 階段性遷移
```
階段1 (月1-2): 建立Telegram Bot，並行運作
階段2 (月3-4): 使用者逐步切換，雙系統運作
階段3 (月5-6): 完全遷移至Telegram，關閉LINE系統
```

#### 6.2.2 風險控制
- 保留LINE系統作為備援（3個月）
- 提供詳細的切換說明文件
- 設置客服支援協助使用者轉換

## 7. 開發階段與時程規劃

### 7.1 開發階段劃分

#### Phase 1: 基礎設施建置 (4週)
- [ ] 雲端環境設置
- [ ] 資料庫建立與初始化
- [ ] MQTT Broker部署
- [ ] 基礎API框架建立

#### Phase 2: 核心功能開發 (6週)
- [ ] 使用者認證系統
- [ ] 機台管理介面
- [ ] MQTT資料接收處理
- [ ] 基礎前端頁面

#### Phase 3: 推播系統整合 (4週)
- [ ] Telegram Bot開發
- [ ] 通知規則引擎
- [ ] 推播模板設計
- [ ] 使用者綁定機制

#### Phase 4: 進階功能開發 (6週)
- [ ] 遠端補幣功能
- [ ] 交易記錄查詢
- [ ] 統計圖表展示
- [ ] 行動裝置優化

#### Phase 5: 測試與上線 (4週)
- [ ] 系統整合測試
- [ ] 效能壓力測試
- [ ] 安全性檢測
- [ ] 使用者接受度測試

### 7.2 詳細時程甘特圖

```
週次 │ 1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17 18 19 20 21 22 23 24
────┼────────────────────────────────────────────────────────────────────────
P1  │ ████████████████
P2  │             ████████████████████████
P3  │                                 ████████████████
P4  │                                             ████████████████████████
P5  │                                                                 ████████████████
測試│                         ████    ████    ████              ████
文檔│     ████         ████         ████              ████              ████
```

### 7.3 關鍵里程碑

| 里程碑 | 預計完成日期 | 交付內容 |
|-------|-------------|----------|
| M1: 基礎設施完成 | 第4週 | 雲端環境、資料庫、MQTT |
| M2: MVP版本 | 第10週 | 基本功能可運作 |
| M3: Beta版本 | 第16週 | 完整功能測試 |
| M4: 正式上線 | 第24週 | 生產環境部署 |

## 8. 風險評估與應對策略

### 8.1 技術風險

| 風險項目 | 影響等級 | 發生機率 | 應對策略 |
|---------|---------|---------|----------|
| MQTT連線不穩定 | 高 | 中 | 建立重連機制、訊息佇列緩存 |
| 資料庫效能問題 | 中 | 低 | 資料庫優化、讀寫分離 |
| 第三方服務中斷 | 中 | 低 | 多重備援方案、降級機制 |

### 8.2 業務風險

| 風險項目 | 影響等級 | 發生機率 | 應對策略 |
|---------|---------|---------|----------|
| 使用者接受度低 | 高 | 中 | 段階性遷移、教育訓練 |
| 競爭對手搶佔市場 | 中 | 中 | 加速開發進度、差異化功能 |
| 法規遵循問題 | 低 | 低 | 法務諮詢、合規性檢查 |

## 9. 預期效益

### 9.1 成本節約
- **推播成本降低90%**: 從每月2.6萬元降至近乎免費
- **維護成本降低30%**: 自動化監控減少人工巡檢
- **客服成本降低50%**: 自助服務功能完善

### 9.2 效率提升
- **故障響應時間縮短60%**: 即時推播通知
- **報表產製效率提升80%**: 自動化統計分析
- **設定變更效率提升70%**: 遠端批次操作

### 9.3 使用者體驗改善
- **通知送達率提升95%**: Telegram高送達率
- **介面使用滿意度提升40%**: 響應式設計
- **功能使用率提升50%**: 直觀的操作介面

## 10. 結論與建議

### 10.1 專案可行性評估
本系統規劃在技術架構、成本效益、市場需求三個面向都具有高度可行性：

1. **技術可行性**: 採用成熟的技術堆疊，風險可控
2. **經濟可行性**: 大幅降低營運成本，提升盈利能力  
3. **市場可行性**: 解決現有痛點，提供差異化價值

### 10.2 成功關鍵因素
1. **使用者體驗優先**: 簡化操作流程，提高易用性
2. **穩定性保證**: 確保系統高可用性（99.9%+）
3. **段階性部署**: 降低遷移風險，確保業務連續性
4. **持續優化**: 根據使用回饋不斷改進

### 10.3 下一步行動建議
1. **立即啟動**: 基礎設施建置刻不容緩
2. **團隊組建**: 招募關鍵技術人才
3. **合作夥伴**: 與硬體供應商建立更緊密合作
4. **市場推廣**: 準備新系統的行銷策略

此系統規劃將為兌幣機管理帶來革命性的改善，建議立即執行。