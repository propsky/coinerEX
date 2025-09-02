# 兌幣機雲服務開發工作清單
*基於現有UI，專注後端雲服務開發*

## 第一階段：基礎設施建置 (第1-2週)

### 1. 設置Linode伺服器環境
```bash
任務內容：
- 註冊Linode帳號
- 創建Ubuntu 22.04 LTS實例 (Linode 2GB)
- 設定SSH金鑰登入
- 配置防火牆規則
- 更新系統套件

預估時間：4小時
```

### 2. 安裝基礎軟體環境
```bash
需要安裝：
- Node.js 18+ (應用服務器)
- PostgreSQL 14+ (資料庫)  
- Nginx (反向代理)
- PM2 (進程管理)
- Git (版本控制)
- MQTT客戶端套件

預估時間：4小時
```

### 3. 設置域名與SSL憑證
```bash
任務內容：
- 購買域名 (如：coinchanger.tw)
- 配置DNS A記錄指向Linode IP
- 安裝Let's Encrypt SSL憑證
- 配置自動續期

預估時間：2小時
```

### 4. 配置Nginx反向代理
```nginx
任務內容：
- 配置HTTP到HTTPS重定向
- 設置API路由代理
- 配置靜態文件服務
- 設定安全標頭

預估時間：3小時
```

## 第二階段：資料庫設計與MQTT整合 (第2-3週)

### 5. 建立PostgreSQL資料庫結構
```sql
資料表設計：
- users (用戶管理)
- machines (機台管理)  
- machine_status (機台狀態)
- transactions (交易記錄)
- notifications (推播記錄)
- mqtt_logs (MQTT日誌)

預估時間：8小時
```

### 6. 整合現有MQTT Broker
```bash
任務內容：
- 連接到現有MQTT Broker
- 測試MQTT連線穩定性
- 配置訂閱主題設定
- 建立MQTT客戶端連線管理

預估時間：3小時
```

## 第三階段：核心API開發 (第3-6週)

### 7. 開發用戶認證API
```javascript
功能範圍：
POST /api/auth/login     // 用戶登入
POST /api/auth/logout    // 用戶登出  
POST /api/auth/refresh   // Token刷新
GET  /api/auth/me        // 獲取用戶資訊

預估時間：12小時
```

### 8. 開發機台管理API  
```javascript
功能範圍：
GET    /api/machines           // 獲取機台列表
GET    /api/machines/:id       // 獲取機台詳情
PUT    /api/machines/:id       // 更新機台設定
POST   /api/machines           // 新增機台
DELETE /api/machines/:id       // 刪除機台

預估時間：16小時
```

### 9. 開發機台狀態監控API
```javascript
功能範圍：
GET /api/machines/:id/status      // 即時狀態
GET /api/machines/:id/history     // 歷史狀態
GET /api/machines/:id/sensors     // 感應器數據  
GET /api/dashboard/summary        // 儀表板總覽

預估時間：20小時
```

### 10. 開發交易記錄API
```javascript
功能範圍：
GET /api/transactions             // 交易記錄列表
GET /api/transactions/:id         // 交易詳情
GET /api/transactions/stats       // 統計數據
GET /api/reports/daily            // 日報表
GET /api/reports/monthly          // 月報表

預估時間：16小時
```

### 11. 開發遠端補幣API
```javascript
功能範圍：
POST /api/machines/:id/refill     // 執行補幣
GET  /api/machines/:id/refill-history // 補幣記錄
POST /api/machines/:id/commands   // 發送控制指令
GET  /api/machines/:id/commands   // 指令執行狀態

預估時間：20小時
```

## 第四階段：MQTT與推播整合 (第6-8週)

### 12. 整合MQTT資料處理服務
```javascript
功能範圍：
- 監聽機台MQTT訊息
- 解析並存儲狀態資料  
- 觸發異常告警
- 處理指令回應

預估時間：24小時
```

### 13. 建立Telegram Bot推播系統
```javascript
功能範圍：
- 建立Telegram Bot
- 用戶綁定機制與驗證碼系統
- 故障通知推播  
- 兌幣通知推播
- 推播記錄管理
- 綁定狀態API

預估時間：20小時 (+4小時用於綁定功能)
```

## 第五階段：系統整合與優化 (第8-10週)

### 14. 現有UI與新API介面整合
```javascript
整合工作：
- 分析現有UI的API呼叫
- 建立API適配層
- 修改前端API端點
- 確保資料格式相容
- 新增Telegram綁定前端頁面

預估時間：28小時 (+8小時用於前端頁面開發)
```

### 14.1 前端Telegram綁定頁面開發
```javascript
新增頁面：
- /user/settings - 個人設定頁面 (新增通知區塊)
- /user/telegram-binding - Telegram綁定引導頁面
- /user/notification-settings - 通知偏好設定頁面

前端功能：
- 綁定狀態檢查與顯示
- 驗證碼生成與複製功能
- 綁定流程引導UI
- 通知偏好設定表單
- 即時綁定狀態更新
- 響應式設計支援手機與桌面
- 步驟指示器與進度追蹤
- 錯誤處理與用戶反饋

UI/UX規格參考：docs/technical/telegram-ui-design.md
互動示範頁面：docs/images/ui/ui-mockups.html

API整合：
- POST /api/telegram/generate-code - 生成綁定驗證碼
- POST /api/telegram/bind - 執行綁定驗證
- DELETE /api/telegram/unbind - 解除綁定
- GET /api/telegram/status - 檢查綁定狀態
- GET/PUT /api/user/notification-settings - 通知設定管理
- POST /api/telegram/test-notification - 測試通知功能

前端技術堆疊：
- Vue.js 3 Composition API
- Element Plus UI 框架
- Axios HTTP 客戶端
- Vue Router 路由管理
- Pinia 狀態管理

預估時間：16小時 (增加UI/UX精細化開發時間)
```

### 15. 建立資料庫備份機制
```bash
備份策略：
- 每日自動備份
- 保留30天備份
- 備份到對象存儲
- 備份完整性檢查

預估時間：8小時
```

### 16. 系統監控與日誌設定
```bash
監控項目：
- 系統資源使用率
- API響應時間
- 資料庫連線狀態
- MQTT連線監控
- 錯誤日誌收集

預估時間：12小時
```

## 第六階段：測試與部署 (第10-12週)

### 17. 進行系統整合測試
```bash
測試範圍：
- API功能測試
- MQTT通訊測試
- 推播功能測試
- 負載壓力測試
- 安全性測試

預估時間：24小時
```

### 18. 生產環境部署與上線
```bash
部署任務：
- 生產環境配置
- SSL憑證配置
- 監控告警設定
- 性能優化調整
- 正式上線切換

預估時間：16小時
```

## 開發時程總覽

| 階段 | 週數 | 主要工作 | 預估工時 |
|-----|------|---------|----------|
| 第一階段 | 1-2週 | 基礎設施建置 | 13小時 |
| 第二階段 | 2-3週 | 資料庫與MQTT整合 | 11小時 |
| 第三階段 | 3-6週 | 核心API開發 | 84小時 |
| 第四階段 | 6-8週 | 整合與推播 | 44小時 *(+4小時)* |
| 第五階段 | 8-10週 | 優化與前端開發 | 64小時 *(+24小時)* |
| 第六階段 | 10-12週 | 測試與部署 | 40小時 |
| **總計** | **12週** | **含Telegram綁定功能** | **256小時** *(+28小時)* |

## 關鍵成功因素

### 技術風險控制
- [ ] 建立開發環境與生產環境一致性
- [ ] 實施代碼版本控制
- [ ] 建立自動化測試流程
- [ ] 設置錯誤監控與告警

### 業務連續性確保
- [ ] 與現有系統並行運作期間
- [ ] 資料遷移策略與回滾方案
- [ ] 用戶切換引導與支援
- [ ] 24/7監控與緊急響應

## 所需資源

### 人力配置建議
- **後端開發工程師** 1名 (全職)
- **系統管理員** 0.5名 (兼職)
- **測試工程師** 0.3名 (兼職)

### 預算估算
- **開發人力**: 依當地薪資標準
- **雲服務費用**: 5,640元/年 (已計算)
- **域名費用**: 1,200元/年
- **其他工具**: 約2,000元/年

## 交付標準

每個階段完成時需要交付：
- [ ] 功能演示
- [ ] 測試報告
- [ ] 技術文檔  
- [ ] 部署指南
- [ ] 使用說明

此工作清單專注於後端雲服務開發，確保與現有UI無縫整合，實現成本最小化的目標。