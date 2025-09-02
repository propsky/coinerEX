# 兌幣機雲服務MVP產品規格書
*2週快速上線的最小可行性產品*

## 🎯 產品主要訴求

### 核心價值主張
**「保留現有LINE Bot習慣，升級至雲端資料管理」**

立即解決客戶痛點：
- ✅ **保持用戶習慣**：現有LINE Bot快速回覆功能完全保留
- ✅ **提升管理效率**：專業Web管理介面，即時監控機台狀態
- ✅ **資料統一管理**：所有幣量、交易、狀態資料集中雲端儲存
- ✅ **零學習成本**：延用現有深色UI風格，操作邏輯一致

### 商業效益
- 🎯 **快速驗證商業模式** - 2週內可展示給客戶
- 🎯 **降低客戶抗拒** - 不改變現有使用習慣
- 🎯 **建立技術基礎** - 為完整版系統奠定架構

---

## 📋 MVP功能範圍

### ✅ 核心功能 (Must Have)

#### 1. LINE Bot快速回覆功能 (保留現有)
```
📊 今日幣量 - 查詢當日所有機台幣量統計
📊 昨日幣量 - 查詢昨日幣量與對比分析  
🏪 營業狀態 - 顯示所有機台開機/故障狀態
📅 查詢特定日期幣量 - 輸入日期查詢歷史幣量
❓ 功能說明 - 指令使用說明
```

#### 2. Web管理介面 (UniApp)
**機台狀態監控頁面** (參考現有PDF設計)
- 機台列表顯示 (在線/離線/故障狀態)
- 機台詳情展開檢視
- 即時狀態更新
- 異常狀態告警顯示

**出幣記錄查詢頁面**
- 交易記錄列表顯示
- 日期範圍篩選功能
- 機台別篩選功能
- 交易詳情檢視

**幣量統計頁面** (對應LINE Bot功能)
- 今日/昨日幣量對比
- 各機台幣量分佈
- 簡單趨勢圖表
- 營業狀態總覽

#### 3. 雲端資料處理
**MQTT資料整合**
- 接收現有機台MQTT訊息
- 解析狀態與交易資料
- 即時資料庫儲存
- 異常狀況偵測

**資料統計計算**
- 每日幣量自動統計
- 機台狀態統計
- 營業數據計算
- 歷史資料查詢

### ⭕ 次要功能 (Nice to Have)
- 基本用戶認證 (簡化版)
- 推播通知設定
- 簡單的資料匯出

### ❌ 暫不包含 (Future Version)
- Telegram Bot整合
- 複雜報表分析
- 遠端補幣功能  
- 高級權限管理
- 手機App原生開發

---

## 🛠️ 技術架構規格

### 系統架構圖
```
現有機台 → MQTT Broker → 新雲端後端 → PostgreSQL
                              ↓
LINE用戶 ← LINE Bot API ← 新雲端後端 ← UniApp前端 ← Web管理者
```

### 技術選型

#### 後端技術棧
- **運行環境**: Node.js 18+
- **Web框架**: Express.js
- **資料庫**: Linode PostgreSQL (代管服務)
- **MQTT客戶端**: mqtt.js
- **LINE SDK**: @line/bot-sdk
- **進程管理**: PM2
- **認證**: JWT (簡化版)

#### 前端技術棧
- **開發框架**: UniApp
- **UI框架**: uView UI 2.0
- **狀態管理**: Vuex
- **HTTP客戶端**: uni.request
- **圖表組件**: uCharts
- **主題風格**: 深色主題 (延用現有設計)

#### 部署架構
- **雲端服務**: Linode VPS (2GB RAM)
- **資料庫**: Linode Database (1GB)
- **SSL憑證**: Let's Encrypt
- **域名**: 待申請 (建議: coinchanger-mvp.tw)
- **監控**: 基本系統監控

### 資料庫設計

#### 核心資料表
```sql
-- 機台基本資料
CREATE TABLE machines (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    location VARCHAR(200),
    status VARCHAR(20) DEFAULT 'offline',
    last_update TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 交易記錄
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    machine_id VARCHAR(50) REFERENCES machines(id),
    amount DECIMAL(10,2) NOT NULL,
    coin_count INTEGER NOT NULL,
    transaction_time TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 機台狀態記錄
CREATE TABLE machine_status (
    id SERIAL PRIMARY KEY,
    machine_id VARCHAR(50) REFERENCES machines(id),
    status VARCHAR(50) NOT NULL,
    error_code VARCHAR(20),
    sensor_data JSON,
    recorded_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 每日統計 (LINE Bot查詢用)
CREATE TABLE daily_stats (
    id SERIAL PRIMARY KEY,
    machine_id VARCHAR(50) REFERENCES machines(id),
    stat_date DATE NOT NULL,
    total_amount DECIMAL(10,2) DEFAULT 0,
    total_coins INTEGER DEFAULT 0,
    transaction_count INTEGER DEFAULT 0,
    avg_amount DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(machine_id, stat_date)
);

-- LINE用戶 (如需要)
CREATE TABLE line_users (
    id SERIAL PRIMARY KEY,
    line_user_id VARCHAR(100) UNIQUE,
    display_name VARCHAR(100),
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### API設計規格

#### RESTful API端點
```javascript
// 機台管理
GET    /api/machines              // 機台列表
GET    /api/machines/:id          // 機台詳情
GET    /api/machines/:id/status   // 機台狀態
PUT    /api/machines/:id          // 更新機台資料

// 交易記錄
GET    /api/transactions          // 交易列表 (支援分頁、篩選)
GET    /api/transactions/:id      // 交易詳情
GET    /api/transactions/stats    // 交易統計

// 統計報表 (LINE Bot專用)
GET    /api/stats/today           // 今日統計
GET    /api/stats/yesterday       // 昨日統計  
GET    /api/stats/date/:date      // 特定日期統計
GET    /api/stats/business        // 營業狀態統計

// LINE Bot Webhook
POST   /webhook/line              // LINE訊息處理

// 系統管理
GET    /api/system/health         // 系統健康檢查
GET    /api/system/logs           // 系統日誌
```

#### LINE Bot訊息格式
```javascript
// 今日幣量回覆範例
{
  "type": "text",
  "text": "📊 今日幣量查詢結果\n─────────────────\n🗓️ 日期: 2024-01-15\n💰 總幣量: 15,600元\n🎰 機台01: 3,200元 ✅\n🎰 機台02: 4,100元 ✅\n🎰 機台03: 2,800元 ❌故障\n🎰 機台04: 5,500元 ✅\n─────────────────\n⏰ 更新時間: 16:30"
}

// 快速回覆選單
{
  "type": "text", 
  "text": "請選擇查詢功能：",
  "quickReply": {
    "items": [
      {"type": "action", "action": {"type": "message", "label": "今日幣量", "text": "今日幣量"}},
      {"type": "action", "action": {"type": "message", "label": "昨日幣量", "text": "昨日幣量"}},
      {"type": "action", "action": {"type": "message", "label": "營業狀態", "text": "營業狀態"}},
      {"type": "action", "action": {"type": "message", "label": "查詢日期", "text": "查詢特定日期"}}
    ]
  }
}
```

---

## 📱 前端UI設計規範

### 頁面結構 (參考現有PDF)

#### 1. 登入頁面
- 簡化版登入表單
- IOTCoinChanger品牌標識
- 深色主題配色
- 「記住密碼」選項

#### 2. 側邊欄導航
```
IOTCoinChanger
├── 🏠 首頁
├── 👤 機台管理
├── ⚙️ 系統設定
├── 📊 統計報表
└── ❓ 說明資訊
```

#### 3. 機台狀態頁面 (完全參考PDF設計)
- 機台列表卡片式設計
- 狀態指示燈 (綠色:正常/紅色:故障/灰色:離線)
- 展開後詳細資訊顯示
- 最後更新時間顯示

#### 4. 出幣記錄頁面 (完全參考PDF設計)  
- 記錄列表展示
- 日期篩選器
- 分頁載入
- 記錄詳情彈窗

#### 5. 統計報表頁面 (新增)
- 今日/昨日對比卡片
- 各機台幣量分佈圖表
- 營業狀態總覽
- 簡單趨勢圖

### UI組件規範
- **色彩**: 延用現有深色主題 (#2c3e50, #34495e, #1abc9c)
- **字體**: 系統默認字體，16px基礎大小
- **按鈕**: 圓角設計，主色調為青綠色
- **圖標**: 使用uniicons圖標庫
- **響應式**: 支援手機豎屏檢視

---

## 🚀 開發計畫與里程碑

### 第1週：基礎建設 (56小時)

#### Day 1-2：環境建置 (16小時)
**負責人**: 後端工程師
**交付物**: 
- [ ] Linode VPS + Database服務申請完成
- [ ] Node.js + PostgreSQL環境搭建
- [ ] 基本專案結構建立
- [ ] LINE Bot API設定完成

**驗收標準**:
- 伺服器可正常連線
- 資料庫連線測試通過
- LINE Bot能回應基本訊息

#### Day 3-4：MQTT整合 + LINE Bot開發 (16小時)
**負責人**: 後端工程師
**交付物**:
- [ ] MQTT訊息接收功能
- [ ] 資料解析與儲存邏輯
- [ ] LINE Bot快速回覆功能 (4個選單)
- [ ] 基礎資料統計邏輯

**驗收標準**:
- MQTT訊息能正常接收並儲存
- LINE Bot四個快速回覆功能正常運作
- 資料統計計算正確

#### Day 5-6：API開發 (16小時)
**負責人**: 後端工程師  
**交付物**:
- [ ] 機台管理API完整功能
- [ ] 交易記錄API完整功能
- [ ] 統計報表API完整功能
- [ ] API文檔撰寫

**驗收標準**:
- 所有API端點回應正常
- API文檔完整可讀
- 資料格式符合前端需求

#### Day 7：整合測試 (8小時)
**負責人**: 後端工程師
**交付物**:
- [ ] 完整後端系統測試
- [ ] LINE Bot功能驗證
- [ ] API壓力測試
- [ ] 資料一致性驗證

**驗收標準**:
- 所有功能測試通過
- 系統穩定運行24小時
- 資料統計準確無誤

### 第2週：前端開發 (56小時)

#### Day 8-9：頁面開發 (16小時)
**負責人**: 前端工程師
**交付物**:
- [ ] 機台狀態頁面 (參考PDF設計)
- [ ] 出幣記錄頁面 (參考PDF設計)
- [ ] 基礎導航與登入頁面

**驗收標準**:
- 頁面風格與現有系統一致
- 響應式設計適配手機
- 頁面載入速度 < 3秒

#### Day 10-11：統計功能開發 (16小時)
**負責人**: 前端工程師
**交付物**:
- [ ] 幣量統計頁面
- [ ] 營業狀態頁面
- [ ] 圖表組件整合
- [ ] 資料篩選功能

**驗收標準**:
- 統計數據與LINE Bot一致
- 圖表顯示正確
- 篩選功能正常運作

#### Day 12-13：系統整合 (16小時)
**負責人**: 前端工程師 + 後端工程師
**交付物**:
- [ ] 前後端完整對接
- [ ] 錯誤處理機制
- [ ] 效能優化
- [ ] UI細節調整

**驗收標準**:
- 所有功能流程正常
- 錯誤提示友善
- 頁面載入順暢

#### Day 14：最終測試與部署 (8小時)
**負責人**: 全體團隊
**交付物**:
- [ ] 完整系統驗收測試
- [ ] 生產環境部署
- [ ] 使用者操作手冊
- [ ] 維護文檔

**驗收標準**:
- 客戶驗收測試通過
- 系統穩定上線運行
- 文檔完整可用

### 關鍵里程碑

| 里程碑 | 完成日期 | 驗收標準 | 風險等級 |
|--------|----------|----------|----------|
| M1 - 後端基礎完成 | Day 7 | LINE Bot + API全部功能正常 | 🟡 中 |
| M2 - 前端基礎完成 | Day 11 | 主要頁面開發完成 | 🟢 低 |
| M3 - 系統整合完成 | Day 13 | 前後端完整對接 | 🟡 中 |
| M4 - 正式上線 | Day 14 | 客戶驗收通過 | 🟢 低 |

---

## ⚠️ 風險評估與應對策略

### 🔴 高風險項目
**1. MQTT資料格式不符預期**
- 風險描述: 現有機台MQTT格式與預期不同
- 影響程度: 可能延遲2-3天
- 應對策略: 第1天即進行MQTT連線測試，提早發現問題
- 備案方案: 準備通用MQTT解析器

**2. LINE Bot API限制**
- 風險描述: 推播頻率或訊息格式限制
- 影響程度: 功能受限
- 應對策略: 詳細研讀LINE Bot API文檔
- 備案方案: 使用訊息合併與延遲發送

### 🟡 中風險項目
**1. 前端UI設計複雜度**
- 風險描述: PDF參考設計實作困難
- 影響程度: 可能影響UI品質
- 應對策略: 提前進行UI原型設計
- 備案方案: 簡化UI設計，保持功能完整

**2. 資料庫效能問題**  
- 風險描述: 大量資料查詢影響效能
- 影響程度: 系統回應緩慢
- 應對策略: 設計合適索引，進行效能測試
- 備案方案: 使用資料快取機制

### 🟢 低風險項目
- UniApp開發技術成熟
- Node.js + Express架構穩定
- Linode雲端服務可靠

---

## 💰 預算與資源規劃

### 人力資源需求
- **後端工程師** 1名 (全職2週) - 56小時
- **前端工程師** 1名 (全職2週) - 56小時
- **專案管理** 0.2名 (兼職2週) - 10小時
- **測試協助** 0.1名 (兼職2週) - 5小時

### 基礎設施成本 (月費)
```
Linode VPS (2GB RAM)     : $12/月
Linode Database (1GB)    : $15/月
域名費用                 : $10/年 (約$1/月)
SSL憑證                  : $0 (Let's Encrypt免費)
總計                     : $28/月
```

### 開發工具成本
- LINE Bot開發者帳號: 免費
- UniApp開發授權: 免費
- 其他開發工具: 使用開源方案

### 預算總覽 (首年)
```
人力成本: (依團隊薪資標準)
基礎設施: $336/年
總開發成本: 人力成本 + $336
```

---

## 📊 成功指標與驗收標準

### 技術指標
- [ ] **系統可用率**: ≥ 99% (2週內)
- [ ] **API回應時間**: ≤ 500ms (平均)
- [ ] **頁面載入時間**: ≤ 3秒 (首次載入)
- [ ] **LINE Bot回應時間**: ≤ 5秒

### 功能指標  
- [ ] **LINE Bot功能**: 4個快速回覆100%可用
- [ ] **Web頁面**: 所有規劃頁面100%完成
- [ ] **資料準確性**: 統計數據與實際一致
- [ ] **即時性**: 機台狀態更新延遲 ≤ 30秒

### 用戶體驗指標
- [ ] **操作直觀性**: 無需說明書即可使用主要功能
- [ ] **介面一致性**: 與現有系統風格100%一致
- [ ] **錯誤處理**: 所有錯誤都有友善提示
- [ ] **多設備支援**: 手機/電腦都能正常使用

### 商業指標
- [ ] **客戶滿意度**: 驗收測試一次通過
- [ ] **功能完整度**: 承諾功能100%交付
- [ ] **穩定性**: 連續運行7天無重大故障
- [ ] **可擴展性**: 架構支援未來功能擴展

---

## 📚 交付物清單

### 系統交付物
- [ ] **完整雲端系統** (前端+後端+資料庫)
- [ ] **LINE Bot服務** (4個快速回覆功能)
- [ ] **Web管理介面** (UniApp打包版本)
- [ ] **資料庫Schema** (完整建表腳本)

### 文檔交付物  
- [ ] **API文檔** (Swagger格式)
- [ ] **使用者操作手冊** (圖文並茂)
- [ ] **系統管理手冊** (部署與維護指南)
- [ ] **資料庫設計文檔** (ER圖與說明)

### 源碼交付物
- [ ] **後端源碼** (Node.js完整專案)
- [ ] **前端源碼** (UniApp完整專案)  
- [ ] **部署腳本** (自動化部署工具)
- [ ] **測試用例** (單元測試與整合測試)

### 維護交付物
- [ ] **監控儀表板** (基本系統監控)
- [ ] **日誌系統** (錯誤追蹤機制)
- [ ] **備份方案** (資料庫自動備份)
- [ ] **緊急聯絡清單** (問題處理流程)

---

## 🎯 後續發展路線圖

### Phase 2: 完善版 (第3-4週)
- 遠端補幣功能
- 詳細報表分析
- 進階權限管理
- 系統監控優化

### Phase 3: 進階版 (第5-6週)  
- Telegram Bot整合
- 手機App原生開發
- 多客戶管理平台
- 高級數據分析

### Phase 4: 企業版 (第7-8週)
- 多租戶架構
- 企業級安全
- 自動化運維
- 商業智能分析

---

## 📞 聯絡資訊與支援

### 開發團隊聯絡方式
- **專案經理**: [聯絡資訊]
- **技術負責人**: [聯絡資訊]  
- **緊急支援**: [24小時聯絡方式]

### 技術支援承諾
- **響應時間**: 工作日4小時內
- **解決時間**: 重大問題24小時內
- **支援方式**: 電話、LINE、遠端協助
- **支援期限**: 系統上線後30天免費支援

---

**📅 文檔版本**: v1.0  
**📅 最後更新**: 2024-01-15  
**👨‍💻 撰寫人員**: MVP開發團隊  
**✅ 核准狀態**: 待核准  

---

*本文檔為兌幣機雲服務MVP產品的完整規格書，所有功能與技術規格以此文檔為準。如有疑問或需要修改，請聯絡專案團隊。*