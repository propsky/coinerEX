# 兌幣機雲服務資料庫架構設計
*基於IOTCoinChanger介面分析的資料表結構*

## 核心資料表設計

### 1. 用戶管理表 (users)
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100),
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    phone VARCHAR(20),
    line_user_id VARCHAR(100) UNIQUE, -- LINE Bot User ID
    role VARCHAR(20) DEFAULT 'user', -- 'admin', 'user', 'operator'
    company_name VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_line_user_id ON users(line_user_id);
CREATE INDEX idx_users_role ON users(role);
```

### 2. 機台管理表 (machines)
```sql
CREATE TABLE machines (
    id SERIAL PRIMARY KEY,
    machine_code VARCHAR(20) UNIQUE NOT NULL, -- 如：MC001
    machine_name VARCHAR(100) NOT NULL, -- 如：店名01
    location VARCHAR(200), -- 機台放置地點
    owner_id INTEGER REFERENCES users(id),
    
    -- 硬體資訊
    ipc_serial VARCHAR(50), -- IPC序號 如：PQ1816161
    hardware_model VARCHAR(50), -- 硬體型號
    firmware_version VARCHAR(20), -- 韌體版本
    
    -- 網路設定
    ip_address INET,
    mac_address VARCHAR(17),
    mqtt_topic VARCHAR(100), -- MQTT主題前綴
    
    -- 運營設定
    coin_capacity INTEGER DEFAULT 500, -- 硬幣容量
    coin_warning_threshold INTEGER DEFAULT 100, -- 低量警告閾值
    
    -- 狀態
    current_status VARCHAR(20) DEFAULT 'offline', -- 'online', 'offline', 'error', 'maintenance'
    is_active BOOLEAN DEFAULT true,
    installed_at DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_machines_code ON machines(machine_code);
CREATE INDEX idx_machines_owner ON machines(owner_id);
CREATE INDEX idx_machines_status ON machines(current_status);
```

### 3. 機台即時狀態表 (machine_status)
```sql
CREATE TABLE machine_status (
    id SERIAL PRIMARY KEY,
    machine_id INTEGER REFERENCES machines(id) ON DELETE CASCADE,
    
    -- 基本狀態 (對應UI狀態列)
    status VARCHAR(20) NOT NULL, -- 'online', 'offline', 'error', 'maintenance'
    error_code VARCHAR(10), -- 錯誤代碼 如：E44
    error_message TEXT, -- 錯誤描述 如：通訊異常
    
    -- 硬幣狀態
    coin_count INTEGER DEFAULT 0, -- 當前硬幣數量
    coin_level VARCHAR(20), -- 'high', 'normal', 'low', 'empty'
    
    -- 感應器數據
    temperature DECIMAL(5,2), -- 溫度
    humidity DECIMAL(5,2), -- 濕度
    voltage DECIMAL(5,2), -- 電壓
    
    -- 通訊狀態
    last_heartbeat TIMESTAMP, -- 最後心跳時間
    connection_quality INTEGER, -- 連線品質 1-5
    uptime_seconds INTEGER, -- 運行時間(秒)
    
    -- 記錄時間
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 確保每個機台只有一筆最新狀態
    CONSTRAINT unique_machine_status UNIQUE (machine_id)
);

-- 索引
CREATE INDEX idx_machine_status_machine ON machine_status(machine_id);
CREATE INDEX idx_machine_status_recorded ON machine_status(recorded_at DESC);
CREATE INDEX idx_machine_status_status ON machine_status(status);
```

### 4. 機台歷史狀態表 (machine_status_history)
```sql
CREATE TABLE machine_status_history (
    id SERIAL PRIMARY KEY,
    machine_id INTEGER REFERENCES machines(id) ON DELETE CASCADE,
    
    -- 狀態變更記錄
    old_status VARCHAR(20),
    new_status VARCHAR(20) NOT NULL,
    error_code VARCHAR(10),
    error_message TEXT,
    
    -- 硬幣數量變化
    old_coin_count INTEGER,
    new_coin_count INTEGER,
    
    -- 感應器歷史數據
    temperature DECIMAL(5,2),
    humidity DECIMAL(5,2),
    voltage DECIMAL(5,2),
    
    -- 記錄時間
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引 (按時間降序，用於查詢歷史)
CREATE INDEX idx_status_history_machine_time ON machine_status_history(machine_id, recorded_at DESC);
CREATE INDEX idx_status_history_status ON machine_status_history(new_status);
```

### 5. 兌幣交易記錄表 (transactions)
```sql
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    transaction_no VARCHAR(50) UNIQUE NOT NULL, -- 交易編號
    machine_id INTEGER REFERENCES machines(id) ON DELETE CASCADE,
    
    -- 交易基本資訊
    transaction_type VARCHAR(20) NOT NULL, -- 'exchange', 'refund'
    coin_amount INTEGER NOT NULL, -- 兌幣數量
    cash_amount DECIMAL(10,2), -- 現金金額
    
    -- 交易前後狀態
    coin_before INTEGER, -- 交易前硬幣數量
    coin_after INTEGER, -- 交易後硬幣數量
    
    -- 用戶資訊 (如果有的話)
    customer_id VARCHAR(100), -- 客戶識別碼
    customer_phone VARCHAR(20), -- 客戶電話
    
    -- 交易狀態
    status VARCHAR(20) DEFAULT 'completed', -- 'pending', 'completed', 'failed', 'refunded'
    payment_method VARCHAR(20), -- 'cash', 'card', 'mobile'
    
    -- 時間記錄
    transaction_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- 備註
    notes TEXT
);

-- 索引
CREATE INDEX idx_transactions_machine_time ON transactions(machine_id, transaction_at DESC);
CREATE INDEX idx_transactions_no ON transactions(transaction_no);
CREATE INDEX idx_transactions_status ON transactions(status);
CREATE INDEX idx_transactions_date ON transactions(DATE(transaction_at));
```

### 6. 補幣記錄表 (refill_records)
```sql
CREATE TABLE refill_records (
    id SERIAL PRIMARY KEY,
    machine_id INTEGER REFERENCES machines(id) ON DELETE CASCADE,
    operator_id INTEGER REFERENCES users(id), -- 操作人員
    
    -- 補幣資訊
    refill_amount INTEGER NOT NULL, -- 補幣數量
    coin_before INTEGER, -- 補幣前數量
    coin_after INTEGER, -- 補幣後數量
    
    -- 操作方式
    refill_type VARCHAR(20) NOT NULL, -- 'remote', 'manual'
    command_id VARCHAR(50), -- 遠端指令ID
    
    -- 執行狀態
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'executing', 'completed', 'failed'
    execution_started_at TIMESTAMP,
    execution_completed_at TIMESTAMP,
    
    -- 錯誤資訊
    error_code VARCHAR(10),
    error_message TEXT,
    
    -- 記錄時間
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 備註
    notes TEXT
);

-- 索引
CREATE INDEX idx_refill_machine_time ON refill_records(machine_id, created_at DESC);
CREATE INDEX idx_refill_operator ON refill_records(operator_id);
CREATE INDEX idx_refill_status ON refill_records(status);
```

### 7. 系統設定表 (machine_settings)
```sql
CREATE TABLE machine_settings (
    id SERIAL PRIMARY KEY,
    machine_id INTEGER REFERENCES machines(id) ON DELETE CASCADE,
    
    -- 營運設定 (對應UI系統設定頁面)
    coin_price DECIMAL(10,2) DEFAULT 1.00, -- 單枚硬幣價格
    exchange_rate DECIMAL(10,4) DEFAULT 1.0000, -- 兌換匯率
    daily_limit INTEGER, -- 每日兌幣上限
    
    -- 警告設定
    low_coin_threshold INTEGER DEFAULT 100, -- 低硬幣警告閾值
    high_temp_threshold DECIMAL(5,2) DEFAULT 40.0, -- 高溫警告
    low_temp_threshold DECIMAL(5,2) DEFAULT 5.0, -- 低溫警告
    
    -- LINE Bot查詢設定
    enable_stats_query BOOLEAN DEFAULT true, -- 啟用統計查詢
    enable_status_query BOOLEAN DEFAULT true, -- 啟用狀態查詢
    enable_historical_query BOOLEAN DEFAULT true, -- 啟用歷史查詢
    query_rate_limit INTEGER DEFAULT 20, -- 查詢頻率限制(次/小時)
    
    -- 營業時間
    business_hours_start TIME DEFAULT '08:00:00',
    business_hours_end TIME DEFAULT '22:00:00',
    business_days INTEGER DEFAULT 127, -- 位元掩碼：1111111 (週日到週六)
    
    -- 記錄時間
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 確保每台機器只有一筆設定
    CONSTRAINT unique_machine_settings UNIQUE (machine_id)
);

-- 索引
CREATE INDEX idx_machine_settings_machine ON machine_settings(machine_id);
```

### 8. LINE Bot查詢記錄表 (linebot_queries)
```sql
CREATE TABLE linebot_queries (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    
    -- 查詢內容
    query_type VARCHAR(30) NOT NULL, -- 'today_stats', 'yesterday_stats', 'business_status', 'date_query'
    query_text TEXT NOT NULL, -- 用戶原始查詢文字
    query_date DATE, -- 特定日期查詢的日期
    
    -- 回應內容
    response_text TEXT, -- 回應內容
    response_data JSONB, -- 結構化回應數據
    
    -- 處理狀態
    status VARCHAR(20) DEFAULT 'completed', -- 'pending', 'completed', 'failed'
    processing_time_ms INTEGER, -- 處理時間(毫秒)
    
    -- 時間記錄
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- 錯誤資訊
    error_message TEXT,
    
    -- LINE Bot相關
    line_message_id VARCHAR(100), -- LINE訊息ID
    line_reply_token VARCHAR(255) -- LINE回覆Token
);

-- 索引
CREATE INDEX idx_linebot_queries_user_time ON linebot_queries(user_id, created_at DESC);
CREATE INDEX idx_linebot_queries_type ON linebot_queries(query_type);
CREATE INDEX idx_linebot_queries_date ON linebot_queries(query_date);
CREATE INDEX idx_linebot_queries_status ON linebot_queries(status);
```

### 9. MQTT訊息日誌表 (mqtt_logs)
```sql
CREATE TABLE mqtt_logs (
    id SERIAL PRIMARY KEY,
    machine_id INTEGER REFERENCES machines(id) ON DELETE CASCADE,
    
    -- MQTT資訊
    topic VARCHAR(200) NOT NULL,
    payload JSONB NOT NULL,
    qos INTEGER DEFAULT 0,
    retained BOOLEAN DEFAULT false,
    
    -- 訊息類型
    message_type VARCHAR(30), -- 'status', 'transaction', 'error', 'command_response'
    
    -- 處理狀態
    processed BOOLEAN DEFAULT false,
    processing_error TEXT,
    
    -- 時間記錄
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

-- 索引
CREATE INDEX idx_mqtt_logs_machine_time ON mqtt_logs(machine_id, received_at DESC);
CREATE INDEX idx_mqtt_logs_processed ON mqtt_logs(processed);
CREATE INDEX idx_mqtt_logs_type ON mqtt_logs(message_type);
CREATE INDEX idx_mqtt_logs_topic ON mqtt_logs(topic);

-- JSONB索引 (用於快速查詢payload內容)
CREATE INDEX idx_mqtt_logs_payload ON mqtt_logs USING GIN (payload);
```

### 10. 系統日誌表 (system_logs)
```sql
CREATE TABLE system_logs (
    id SERIAL PRIMARY KEY,
    
    -- 日誌基本資訊
    log_level VARCHAR(10) NOT NULL, -- 'DEBUG', 'INFO', 'WARN', 'ERROR', 'FATAL'
    category VARCHAR(50) NOT NULL, -- 'api', 'mqtt', 'notification', 'system'
    message TEXT NOT NULL,
    
    -- 相關資源
    machine_id INTEGER REFERENCES machines(id),
    user_id INTEGER REFERENCES users(id),
    
    -- 請求資訊
    request_id VARCHAR(50), -- 用於追蹤API請求
    ip_address INET,
    user_agent TEXT,
    
    -- 額外資料
    metadata JSONB, -- 額外的結構化資料
    
    -- 時間
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_system_logs_level_time ON system_logs(log_level, created_at DESC);
CREATE INDEX idx_system_logs_category_time ON system_logs(category, created_at DESC);
CREATE INDEX idx_system_logs_machine ON system_logs(machine_id);
CREATE INDEX idx_system_logs_user ON system_logs(user_id);
```

## 資料表關聯圖

```
users (用戶)
├── machines (機台) [owner_id]
│   ├── machine_status (即時狀態)
│   ├── machine_status_history (歷史狀態)
│   ├── transactions (交易記錄)
│   ├── refill_records (補幣記錄) [operator_id → users]
│   ├── machine_settings (系統設定)
│   ├── mqtt_logs (MQTT日誌)
│   └── system_logs (系統日誌)
└── linebot_queries (LINE Bot查詢記錄) [user_id]
```

## 初始化數據腳本

### 建立預設用戶角色
```sql
-- 插入系統管理員
INSERT INTO users (username, email, password_hash, full_name, role) VALUES
('admin', 'admin@coinerex.tw', '$2b$12$...', '系統管理員', 'admin');

-- 插入測試用戶
INSERT INTO users (username, email, password_hash, full_name, role, company_name, line_user_id) VALUES
('demo_user', 'demo@example.com', '$2b$12$...', '示範用戶', 'user', '示範公司', 'U1234567890abcdef');
```

### 建立範例機台
```sql
-- 插入測試機台
INSERT INTO machines (machine_code, machine_name, location, owner_id, ipc_serial) VALUES
('MC001', '店名01', '台北市中正區', 2, 'PQ1816161'),
('MC002', '店名02', '台北市大安區', 2, 'PQ1816162');

-- 插入機台設定
INSERT INTO machine_settings (machine_id) VALUES (1), (2);

-- 插入初始狀態
INSERT INTO machine_status (machine_id, status, coin_count) VALUES
(1, 'online', 350),
(2, 'offline', 200);
```

## 資料庫維護與優化

### 定期清理策略
```sql
-- 清理90天前的MQTT日誌
DELETE FROM mqtt_logs WHERE received_at < NOW() - INTERVAL '90 days';

-- 清理30天前的系統日誌 (非錯誤等級)
DELETE FROM system_logs 
WHERE created_at < NOW() - INTERVAL '30 days' 
AND log_level NOT IN ('ERROR', 'FATAL');

-- 清理1年前的狀態歷史 (保留錯誤記錄)
DELETE FROM machine_status_history 
WHERE recorded_at < NOW() - INTERVAL '1 year'
AND new_status NOT IN ('error', 'maintenance');
```

### 效能監控查詢
```sql
-- 查詢最活躍的機台
SELECT m.machine_code, m.machine_name, COUNT(t.id) as transaction_count
FROM machines m
LEFT JOIN transactions t ON m.id = t.machine_id
WHERE t.transaction_at >= NOW() - INTERVAL '7 days'
GROUP BY m.id, m.machine_code, m.machine_name
ORDER BY transaction_count DESC
LIMIT 10;

-- 查詢系統錯誤統計
SELECT error_code, COUNT(*) as error_count, MAX(recorded_at) as latest_error
FROM machine_status_history
WHERE new_status = 'error'
AND recorded_at >= NOW() - INTERVAL '7 days'
GROUP BY error_code
ORDER BY error_count DESC;
```

## 備份與安全策略

### 自動備份腳本
```sql
-- 每日備份重要資料表
pg_dump -t users -t machines -t machine_settings coinerex_db > backup_critical_$(date +%Y%m%d).sql

-- 每週完整備份
pg_dump coinerex_db > backup_full_$(date +%Y%m%d).sql
```

### 資料隱私保護
```sql
-- 敏感資料加密 (客戶電話)
UPDATE transactions SET customer_phone = 
CASE 
    WHEN customer_phone IS NOT NULL 
    THEN OVERLAY(customer_phone PLACING '****' FROM 4 FOR 4)
    ELSE NULL 
END;
```

這個資料庫架構完整對應了兌幣機UI的所有功能需求，並考慮了擴展性、效能和資料安全性。