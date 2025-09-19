#!/bin/bash
#
# Hello OTA 安裝腳本
# 用於在Linux系統上安裝和設定Hello OTA示範應用程式
#

set -e  # 任何命令失敗時退出

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 函數定義
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此腳本需要root權限執行"
        echo "請使用: sudo $0"
        exit 1
    fi
}

check_system() {
    log_info "檢查系統環境..."

    # 檢查作業系統
    if [[ ! -f /etc/os-release ]]; then
        log_error "無法識別的Linux發行版"
        exit 1
    fi

    source /etc/os-release
    log_info "檢測到系統: $PRETTY_NAME"

    # 檢查Python版本
    if ! command -v python3 &> /dev/null; then
        log_error "未找到Python 3，請先安裝Python 3.8或更高版本"
        exit 1
    fi

    PYTHON_VERSION=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
    log_info "Python版本: $PYTHON_VERSION"

    # 檢查systemd
    if ! command -v systemctl &> /dev/null; then
        log_error "此系統不支援systemd"
        exit 1
    fi
}

install_dependencies() {
    log_info "安裝系統依賴套件..."

    # 根據發行版安裝套件
    if command -v apt-get &> /dev/null; then
        apt-get update
        apt-get install -y python3-pip python3-venv curl wget
    elif command -v yum &> /dev/null; then
        yum install -y python3-pip curl wget
    elif command -v dnf &> /dev/null; then
        dnf install -y python3-pip curl wget
    else
        log_warning "無法自動安裝依賴套件，請手動安裝: python3-pip curl wget"
    fi
}

create_user() {
    log_info "建立hello-ota系統用戶..."

    if ! id hello-ota &> /dev/null; then
        useradd --system --shell /bin/false --home-dir /opt/hello-ota \
                --create-home hello-ota
        log_success "已建立hello-ota用戶"
    else
        log_info "hello-ota用戶已存在"
    fi
}

create_directories() {
    log_info "建立必要目錄..."

    # 建立目錄
    mkdir -p /opt/hello-ota
    mkdir -p /var/lib/hello-ota
    mkdir -p /var/log/hello-ota
    mkdir -p /etc/hello-ota
    mkdir -p /var/backups/hello-ota

    # 設定權限
    chown -R hello-ota:hello-ota /opt/hello-ota
    chown -R hello-ota:hello-ota /var/lib/hello-ota
    chown -R hello-ota:hello-ota /var/log/hello-ota
    chown -R hello-ota:hello-ota /etc/hello-ota
    chown -R hello-ota:hello-ota /var/backups/hello-ota

    chmod 755 /opt/hello-ota
    chmod 755 /var/lib/hello-ota
    chmod 755 /var/log/hello-ota
    chmod 755 /etc/hello-ota
    chmod 755 /var/backups/hello-ota

    log_success "目錄建立完成"
}

install_python_deps() {
    log_info "安裝Python依賴套件..."

    # 建立requirements.txt如果不存在
    if [[ ! -f requirements.txt ]]; then
        cat > requirements.txt << EOF
requests>=2.25.0
EOF
    fi

    # 安裝Python套件
    pip3 install -r requirements.txt

    log_success "Python依賴套件安裝完成"
}

copy_application() {
    log_info "複製應用程式檔案..."

    # 複製應用程式檔案
    cp -r app/* /opt/hello-ota/

    # 設定執行權限
    chmod +x /opt/hello-ota/main.py

    # 設定所有權
    chown -R hello-ota:hello-ota /opt/hello-ota

    log_success "應用程式檔案複製完成"
}

install_systemd_service() {
    log_info "安裝systemd服務..."

    # 複製服務檔案
    cp systemd/hello-ota.service /etc/systemd/system/

    # 重新載入systemd
    systemctl daemon-reload

    # 啟用服務
    systemctl enable hello-ota.service

    log_success "systemd服務安裝完成"
}

create_default_config() {
    log_info "建立預設配置檔..."

    if [[ ! -f /etc/hello-ota/config.json ]]; then
        cat > /etc/hello-ota/config.json << EOF
{
  "app": {
    "name": "hello-ota",
    "port": 8080,
    "host": "0.0.0.0",
    "heartbeat_interval": 30,
    "log_level": "INFO"
  },
  "ota": {
    "enabled": true,
    "update_server": "http://localhost:9000",
    "check_interval": 300,
    "backup_count": 3,
    "auto_update": false
  },
  "system": {
    "data_dir": "/var/lib/hello-ota",
    "log_dir": "/var/log/hello-ota",
    "pid_file": "/var/run/hello-ota.pid"
  }
}
EOF
        chown hello-ota:hello-ota /etc/hello-ota/config.json
        chmod 644 /etc/hello-ota/config.json
        log_success "預設配置檔已建立"
    else
        log_info "配置檔已存在，跳過建立"
    fi
}

setup_logrotate() {
    log_info "設定日誌輪替..."

    cat > /etc/logrotate.d/hello-ota << EOF
/var/log/hello-ota/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 hello-ota hello-ota
    postrotate
        systemctl reload hello-ota 2>/dev/null || true
    endscript
}
EOF

    log_success "日誌輪替設定完成"
}

start_service() {
    log_info "啟動Hello OTA服務..."

    systemctl start hello-ota.service

    # 等待服務啟動
    sleep 3

    if systemctl is-active --quiet hello-ota.service; then
        log_success "Hello OTA服務啟動成功"
    else
        log_error "Hello OTA服務啟動失敗"
        log_info "檢查日誌: journalctl -u hello-ota.service"
        exit 1
    fi
}

show_status() {
    log_info "顯示服務狀態..."

    echo ""
    echo "=== Hello OTA 安裝完成 ==="
    echo ""
    systemctl status hello-ota.service --no-pager -l
    echo ""
    log_info "應用程式URL: http://localhost:8080"
    log_info "配置檔位置: /etc/hello-ota/config.json"
    log_info "日誌位置: /var/log/hello-ota/"
    log_info "服務管理:"
    echo "  - 啟動服務: sudo systemctl start hello-ota"
    echo "  - 停止服務: sudo systemctl stop hello-ota"
    echo "  - 重啟服務: sudo systemctl restart hello-ota"
    echo "  - 查看狀態: sudo systemctl status hello-ota"
    echo "  - 查看日誌: sudo journalctl -u hello-ota -f"
    echo ""
}

main() {
    echo "Hello OTA 安裝腳本"
    echo "=================="
    echo ""

    check_root
    check_system
    install_dependencies
    create_user
    create_directories
    install_python_deps
    copy_application
    install_systemd_service
    create_default_config
    setup_logrotate
    start_service
    show_status

    log_success "Hello OTA 安裝完成！"
}

# 執行主函數
main "$@"