#!/usr/bin/env python3
"""
Hello OTA - Python OTA更新示範應用程式
"""

import os
import sys
import json
import time
import signal
import logging
import threading
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

# 設定模組路徑
sys.path.insert(0, str(Path(__file__).parent))

from version import __version__, get_version_info
from config import config
from ota_manager import OTAManager

# 設定日誌
def setup_logging():
    log_level = getattr(logging, config.get('app.log_level', 'INFO'))
    log_dir = Path(config.get('system.log_dir', '/var/log/hello-ota'))
    log_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'hello-ota.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

logger = logging.getLogger(__name__)

class HelloOTAHandler(BaseHTTPRequestHandler):
    """HTTP請求處理器"""

    def do_GET(self):
        """處理GET請求"""
        if self.path == '/':
            self._send_response(200, self._get_status())
        elif self.path == '/version':
            self._send_response(200, get_version_info())
        elif self.path == '/health':
            self._send_response(200, {"status": "healthy", "timestamp": datetime.now().isoformat()})
        elif self.path == '/ota/status':
            self._send_response(200, self._get_ota_status())
        else:
            self._send_response(404, {"error": "Not Found"})

    def do_POST(self):
        """處理POST請求"""
        if self.path == '/trigger_update':
            self._handle_trigger_update()
        elif self.path == '/ota/check':
            self._handle_check_update()
        else:
            self._send_response(404, {"error": "Not Found"})

    def _send_response(self, status_code, data):
        """發送JSON回應"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8'))

    def _get_status(self):
        """取得應用程式狀態"""
        uptime = time.time() - app.start_time
        return {
            "name": "Hello OTA Demo",
            "version": __version__,
            "status": "running",
            "uptime_seconds": int(uptime),
            "start_time": datetime.fromtimestamp(app.start_time).isoformat(),
            "pid": os.getpid(),
            "config": {
                "ota_enabled": config.get('ota.enabled', True),
                "auto_update": config.get('ota.auto_update', False),
                "update_server": config.get('ota.update_server')
            }
        }

    def _get_ota_status(self):
        """取得OTA狀態"""
        return {
            "current_version": __version__,
            "ota_enabled": config.get('ota.enabled', True),
            "last_check": getattr(app, 'last_update_check', None),
            "update_history": app.ota_manager.get_update_history()[-5:]  # 最近5筆
        }

    def _handle_trigger_update(self):
        """處理觸發更新請求"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))

            version = request_data.get('version')
            update_url = request_data.get('update_url')
            checksum = request_data.get('checksum', '')

            if not version or not update_url:
                self._send_response(400, {"error": "缺少必要參數: version, update_url"})
                return

            logger.info(f"收到更新觸發請求: {version}")

            # 建立更新資訊
            update_info = {
                "version": version,
                "download_url": update_url,
                "checksum": checksum,
                "has_update": True,
                "latest_version": version
            }

            # 在背景執行更新
            update_thread = threading.Thread(
                target=app._perform_update,
                args=(update_info,)
            )
            update_thread.daemon = True
            update_thread.start()

            self._send_response(200, {
                "message": "更新請求已接受",
                "target_version": version,
                "status": "processing"
            })

        except Exception as e:
            logger.error(f"處理更新觸發請求失敗: {e}")
            self._send_response(500, {"error": str(e)})

    def _handle_check_update(self):
        """處理檢查更新請求"""
        try:
            update_info = app.ota_manager.check_for_updates()
            if update_info:
                self._send_response(200, update_info)
            else:
                self._send_response(200, {
                    "has_update": False,
                    "current_version": __version__,
                    "message": "目前已是最新版本"
                })
        except Exception as e:
            logger.error(f"檢查更新失敗: {e}")
            self._send_response(500, {"error": str(e)})

    def log_message(self, format, *args):
        """覆寫日誌方法以使用我們的logger"""
        logger.info(f"{self.address_string()} - {format % args}")

class HelloOTAApp:
    """Hello OTA 主應用程式"""

    def __init__(self):
        self.start_time = time.time()
        self.running = True
        self.server = None
        self.ota_manager = OTAManager()
        self.last_update_check = None

        # 設定信號處理
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """處理系統信號"""
        logger.info(f"收到信號 {signum}，準備優雅關閉")
        self.shutdown()

    def start(self):
        """啟動應用程式"""
        logger.info(f"Hello OTA v{__version__} 正在啟動...")

        # 建立PID檔案
        self._create_pid_file()

        # 啟動HTTP服務器
        host = config.get('app.host', '0.0.0.0')
        port = config.get('app.port', 8080)

        self.server = HTTPServer((host, port), HelloOTAHandler)
        logger.info(f"HTTP服務器啟動於 {host}:{port}")

        # 啟動心跳線程
        self._start_heartbeat()

        # 啟動OTA檢查線程
        if config.get('ota.enabled', True):
            self._start_ota_checker()

        try:
            # 主服務循環
            self.server.serve_forever()
        except KeyboardInterrupt:
            logger.info("收到中斷信號")
        finally:
            self.shutdown()

    def _create_pid_file(self):
        """建立PID檔案"""
        pid_file = Path(config.get('system.pid_file', '/var/run/hello-ota.pid'))
        pid_file.parent.mkdir(parents=True, exist_ok=True)

        with open(pid_file, 'w') as f:
            f.write(str(os.getpid()))

    def _start_heartbeat(self):
        """啟動心跳線程"""
        def heartbeat_loop():
            interval = config.get('app.heartbeat_interval', 30)
            while self.running:
                logger.debug(f"心跳 - 運行時間: {int(time.time() - self.start_time)}秒")
                time.sleep(interval)

        heartbeat_thread = threading.Thread(target=heartbeat_loop)
        heartbeat_thread.daemon = True
        heartbeat_thread.start()

    def _start_ota_checker(self):
        """啟動OTA檢查線程"""
        def ota_check_loop():
            interval = config.get('ota.check_interval', 300)  # 5分鐘
            while self.running:
                try:
                    logger.debug("檢查OTA更新")
                    self.last_update_check = datetime.now().isoformat()

                    update_info = self.ota_manager.check_for_updates()
                    if update_info and config.get('ota.auto_update', False):
                        logger.info("發現更新且已啟用自動更新")
                        self._perform_update(update_info)

                except Exception as e:
                    logger.error(f"OTA檢查失敗: {e}")

                time.sleep(interval)

        ota_thread = threading.Thread(target=ota_check_loop)
        ota_thread.daemon = True
        ota_thread.start()

    def _perform_update(self, update_info):
        """執行OTA更新"""
        try:
            logger.info(f"開始執行OTA更新到版本 {update_info['version']}")

            # 下載更新
            update_file = self.ota_manager.download_update(update_info)

            # 套用更新（這會導致程式退出）
            self.ota_manager.apply_update(update_file, update_info)

        except Exception as e:
            logger.error(f"OTA更新失敗: {e}")

    def shutdown(self):
        """優雅關閉應用程式"""
        logger.info("應用程式正在關閉...")
        self.running = False

        if self.server:
            self.server.shutdown()
            self.server.server_close()

        # 清理PID檔案
        pid_file = Path(config.get('system.pid_file', '/var/run/hello-ota.pid'))
        if pid_file.exists():
            pid_file.unlink()

        logger.info("應用程式已關閉")

# 全域應用程式實例
app = HelloOTAApp()

def main():
    """主入口函數"""
    setup_logging()

    logger.info("="*50)
    logger.info(f"Hello OTA v{__version__} - Python OTA更新示範")
    logger.info("="*50)

    try:
        app.start()
    except Exception as e:
        logger.error(f"應用程式啟動失敗: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()