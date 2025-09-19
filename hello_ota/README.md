# Hello OTA - Python應用程式遠端更新學習教材

這是一個簡單但完整的Python OTA (Over-The-Air) 更新示範專案，展示如何在Linux環境中實現Python應用程式的遠端更新。

## 專案概述

此教材模擬一個簡單的IoT設備應用程式，具備：
- 基本的HTTP服務器功能
- 定時心跳上報
- 遠端OTA更新能力
- 安全的回滾機制

## 檔案結構

```
hello_ota/
├── README.md                    # 本文件
├── requirements.txt             # Python依賴套件
├── app/
│   ├── main.py                 # 主應用程式
│   ├── config.py               # 設定管理
│   ├── ota_manager.py          # OTA管理器
│   └── version.py              # 版本資訊
├── scripts/
│   ├── install.sh              # 安裝腳本
│   ├── update_executor.py      # 更新執行器
│   └── service_manager.py      # 服務管理工具
├── systemd/
│   └── hello-ota.service       # systemd服務檔案
├── updates/
│   ├── create_update.py        # 建立更新包工具
│   └── v1.1.0/                # 示範更新包
│       ├── app/
│       └── update_info.json
└── tests/
    ├── test_ota.py            # OTA功能測試
    └── mock_server.py         # 模擬更新服務器
```

## 快速開始

### 1. 安裝基礎環境

```bash
# 克隆專案
git clone <repository_url>
cd hello_ota

# 執行安裝腳本
chmod +x scripts/install.sh
sudo ./scripts/install.sh
```

### 2. 啟動服務

```bash
# 啟動hello-ota服務
sudo systemctl start hello-ota
sudo systemctl enable hello-ota

# 檢查狀態
sudo systemctl status hello-ota
```

### 3. 測試OTA更新

```bash
# 建立測試更新包
cd updates
python3 create_update.py --version 1.1.0

# 啟動模擬更新服務器
cd ../tests
python3 mock_server.py

# 觸發更新（在另一個終端）
curl -X POST http://localhost:8080/trigger_update \
  -H "Content-Type: application/json" \
  -d '{"version": "1.1.0", "update_url": "http://localhost:9000/updates/v1.1.0.tar.gz"}'
```

## 學習重點

### 1. 安全更新流程
- 檔案完整性驗證（SHA256）
- 原子性更新操作
- 自動回滾機制

### 2. 服務管理
- systemd整合
- 優雅關閉處理
- 服務依賴管理

### 3. 錯誤處理
- 網路異常處理
- 檔案操作錯誤處理
- 更新失敗回滾

### 4. 日誌與監控
- 結構化日誌記錄
- 更新狀態追蹤
- 系統健康檢查

## 進階功能

- 增量更新支援
- 多環境設定管理
- 更新排程功能
- 遠端配置更新

## 技術特點

- **Python 3.8+** 兼容
- **零停機時間** 更新
- **自動回滾** 保護
- **完整日誌** 記錄
- **模組化設計** 易於擴展

## 注意事項

1. 本教材僅供學習使用，生產環境需要額外的安全措施
2. 請在虛擬機或測試環境中進行實驗
3. 更新前請確保有足夠的磁碟空間
4. 建議在更新前建立系統快照

## 授權

MIT License - 自由使用於教育和商業用途