# GitHub Pages + MkDocs 部署指南

## 🚀 快速開始

### 1. 本地安裝與測試

#### 安裝 Python 和 MkDocs
```bash
# 安裝 Python (如果尚未安裝)
# 下載：https://www.python.org/downloads/

# 安裝必要套件
pip install -r requirements.txt

# 或手動安裝
pip install mkdocs mkdocs-material mkdocs-minify-plugin pymdown-extensions
```

#### 本地預覽
```bash
# 在專案根目錄執行
mkdocs serve

# 瀏覽器開啟
http://127.0.0.1:8000
```

#### 建構靜態網站
```bash
mkdocs build
# 產生的網站將在 site/ 目錄中
```

### 2. GitHub 部署設定

#### Step 1: 建立 GitHub Repository
1. 登入 GitHub
2. 建立新的 repository，命名為 `coinerEX`
3. 設定為 Public (Private 也可以，但需要付費版才能使用 Pages)

#### Step 2: 上傳檔案到 GitHub
```bash
# 初始化 Git (如果尚未初始化)
git init

# 添加遠端 repository
git remote add origin https://github.com/你的用戶名/coinerEX.git

# 添加所有檔案
git add .

# 提交
git commit -m "Initial commit: 兌幣機系統文檔"

# 推送到 GitHub
git push -u origin main
```

#### Step 3: 啟用 GitHub Pages
1. 進入 GitHub repository 頁面
2. 點選 **Settings** 標籤
3. 找到 **Pages** 選項
4. 在 **Source** 選擇 **GitHub Actions**
5. 儲存設定

#### Step 4: 自動部署
- GitHub Actions 會自動執行 (參考 `.github/workflows/deploy.yml`)
- 每次推送到 main branch 都會自動更新網站
- 網站將在 `https://你的用戶名.github.io/coinerEX` 上可用

### 3. 自定義設定

#### 更新 mkdocs.yml 中的資訊
```yaml
# 更新這些欄位
site_url: https://你的用戶名.github.io/coinerEX
repo_name: 你的用戶名/coinerEX  
repo_url: https://github.com/你的用戶名/coinerEX
```

#### 自定義域名 (可選)
如果有自己的域名：
1. 在 repository 根目錄建立 `CNAME` 檔案
2. 內容寫入你的域名，例如：`docs.yourcompany.com`
3. 在域名提供商設定 DNS CNAME 記錄指向 `你的用戶名.github.io`

## 📝 日常使用

### 新增或修改文檔
1. 直接編輯 Markdown 檔案
2. 提交變更到 GitHub
3. 網站會自動更新（約 5-10 分鐘）

### 本地預覽變更
```bash
# 啟動本地服務器
mkdocs serve

# 即時預覽變更
# 檔案儲存時會自動重新載入
```

### 新增頁面
1. 在對應資料夾建立新的 `.md` 檔案
2. 在 `mkdocs.yml` 的 `nav` 部分新增連結
3. 提交變更

## 🎨 自定義樣式

### 修改主題顏色
在 `mkdocs.yml` 中：
```yaml
theme:
  palette:
    primary: indigo  # 主色
    accent: indigo   # 強調色
```

### 新增自定義 CSS
在 `docs/stylesheets/extra.css` 中新增樣式

### 新增自定義 JavaScript
在 `docs/javascripts/` 中新增 JS 檔案

## 🔧 進階設定

### 啟用搜尋功能
已經預設啟用，支援中文搜尋

### 新增 Google Analytics
```yaml
# 在 mkdocs.yml 的 extra 區段新增
extra:
  analytics:
    provider: google
    property: G-XXXXXXXXXX
```

### 啟用評論功能
```yaml
# 在 mkdocs.yml 中新增
extra:
  disqus: 你的-disqus-shortname
```

## 📱 響應式設計

網站已經優化為響應式設計，在電腦、平板、手機上都能良好顯示。

## 🔒 權限控制

- GitHub Pages 網站預設是公開的
- 如需私人網站，考慮使用：
  - GitBook (有私人選項)
  - Netlify (付費版有密碼保護)
  - 自建服務器

## 📊 網站分析

可以整合以下分析工具：
- Google Analytics
- Google Search Console
- GitHub Insights

## ⚡ 效能優化

已啟用的優化：
- 程式碼壓縮 (minify)
- 圖片懶加載
- CDN 加速 (GitHub Pages 自帶)

## 🆘 常見問題

### Q: 網站沒有更新？
A: 檢查 GitHub Actions 是否成功執行，通常需要 5-10 分鐘

### Q: 樣式沒有生效？
A: 確認 CSS 檔案路徑正確，清除瀏覽器快取

### Q: 中文顯示問題？
A: 確認檔案編碼為 UTF-8

### Q: 本地預覽正常，線上有問題？
A: 檢查相對路徑是否正確，GitHub Pages 的基礎路徑可能不同

## 📞 技術支援

如有問題，可以：
1. 檢查 GitHub Actions 日誌
2. 查看 MkDocs 官方文檔
3. 查看 Material for MkDocs 文檔

---

**部署完成後，您將擁有一個專業的文檔網站，支援搜尋、響應式設計，且易於維護！**