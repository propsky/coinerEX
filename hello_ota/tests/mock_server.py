#!/usr/bin/env python3
"""
Mock OTA Update Server - 模擬OTA更新服務器
用於測試Hello OTA應用程式的更新功能
"""

import os
import json
import hashlib
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

class MockUpdateServerHandler(BaseHTTPRequestHandler):
    """模擬更新服務器HTTP請求處理器"""

    def do_GET(self):
        """處理GET請求"""
        path = urlparse(self.path).path
        query = parse_qs(urlparse(self.path).query)

        if path == '/api/check_update':
            self._handle_check_update(query)
        elif path.startswith('/updates/'):
            self._handle_download_update(path)
        elif path == '/api/available_versions':
            self._handle_available_versions()
        else:
            self._send_response(404, {"error": "Not Found"})

    def _handle_check_update(self, query):
        """處理檢查更新請求"""
        current_version = query.get('current_version', [''])[0]

        print(f"[Mock Server] 檢查更新請求 - 當前版本: {current_version}")

        # 模擬可用版本
        available_versions = {
            "1.0.0": "1.1.0",  # 1.0.0 可以更新到 1.1.0
            "1.1.0": None      # 1.1.0 已是最新版本
        }

        latest_version = available_versions.get(current_version)

        if latest_version:
            # 計算更新檔案的校驗和
            update_file = Path(__file__).parent.parent / "updates" / f"v{latest_version}.tar.gz"
            checksum = ""

            if update_file.exists():
                checksum = self._calculate_checksum(update_file)

            response_data = {
                "has_update": True,
                "current_version": current_version,
                "latest_version": latest_version,
                "download_url": f"http://localhost:9000/updates/v{latest_version}.tar.gz",
                "checksum": checksum,
                "release_notes": f"更新到版本 {latest_version}",
                "size": update_file.stat().st_size if update_file.exists() else 0,
                "required": False
            }
        else:
            response_data = {
                "has_update": False,
                "current_version": current_version,
                "latest_version": current_version,
                "message": "目前已是最新版本"
            }

        self._send_response(200, response_data)

    def _handle_download_update(self, path):
        """處理更新檔案下載請求"""
        # 提取檔案名稱
        filename = path.split('/')[-1]
        update_file = Path(__file__).parent.parent / "updates" / filename

        print(f"[Mock Server] 下載請求: {filename}")

        if update_file.exists():
            # 發送檔案
            self.send_response(200)
            self.send_header('Content-Type', 'application/gzip')
            self.send_header('Content-Length', str(update_file.stat().st_size))
            self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
            self.end_headers()

            with open(update_file, 'rb') as f:
                self.wfile.write(f.read())

            print(f"[Mock Server] 檔案下載完成: {filename}")
        else:
            self._send_response(404, {"error": f"檔案不存在: {filename}"})

    def _handle_available_versions(self):
        """處理取得可用版本清單請求"""
        updates_dir = Path(__file__).parent.parent / "updates"
        versions = []

        if updates_dir.exists():
            for item in updates_dir.iterdir():
                if item.is_file() and item.name.endswith('.tar.gz'):
                    version = item.name.replace('v', '').replace('.tar.gz', '')
                    versions.append({
                        "version": version,
                        "filename": item.name,
                        "size": item.stat().st_size,
                        "checksum": self._calculate_checksum(item)
                    })

        versions.sort(key=lambda x: x['version'], reverse=True)

        self._send_response(200, {
            "available_versions": versions,
            "count": len(versions)
        })

    def _calculate_checksum(self, file_path):
        """計算檔案SHA256校驗和"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    def _send_response(self, status_code, data):
        """發送JSON回應"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        response_json = json.dumps(data, ensure_ascii=False, indent=2)
        self.wfile.write(response_json.encode('utf-8'))

    def log_message(self, format, *args):
        """自訂日誌格式"""
        print(f"[Mock Server] {self.address_string()} - {format % args}")

def create_sample_update():
    """建立範例更新檔案"""
    updates_dir = Path(__file__).parent.parent / "updates"
    updates_dir.mkdir(exist_ok=True)

    # 建立v1.1.0更新檔案
    version_dir = updates_dir / "v1.1.0"
    if not version_dir.exists():
        version_dir.mkdir()

        # 建立app目錄
        app_dir = version_dir / "app"
        app_dir.mkdir()

        # 複製並修改版本檔案
        version_file = app_dir / "version.py"
        version_content = '''"""
應用程式版本資訊
"""

__version__ = "1.1.0"
__build_date__ = "2025-01-20"
__description__ = "Hello OTA 示範應用程式 - 新功能版本"

def get_version_info():
    """取得完整版本資訊"""
    return {
        "version": __version__,
        "build_date": __build_date__,
        "description": __description__
    }'''

        with open(version_file, 'w', encoding='utf-8') as f:
            f.write(version_content)

        # 複製其他檔案
        source_app_dir = Path(__file__).parent.parent / "app"
        if source_app_dir.exists():
            import shutil
            for file in source_app_dir.glob("*.py"):
                if file.name != "version.py":
                    shutil.copy2(file, app_dir)

        # 建立壓縮檔
        import tarfile
        tar_file = updates_dir / "v1.1.0.tar.gz"
        with tarfile.open(tar_file, "w:gz") as tar:
            tar.add(version_dir, arcname="v1.1.0")

        print(f"[Mock Server] 已建立範例更新檔案: {tar_file}")

def main():
    """主函數"""
    print("Mock OTA Update Server")
    print("=====================")
    print()

    # 建立範例更新檔案
    create_sample_update()

    # 啟動服務器
    host = "localhost"
    port = 9000

    server = HTTPServer((host, port), MockUpdateServerHandler)

    print(f"模擬更新服務器啟動於: http://{host}:{port}")
    print()
    print("可用端點:")
    print(f"  - 檢查更新: GET http://{host}:{port}/api/check_update?current_version=1.0.0")
    print(f"  - 下載更新: GET http://{host}:{port}/updates/v1.1.0.tar.gz")
    print(f"  - 可用版本: GET http://{host}:{port}/api/available_versions")
    print()
    print("測試指令:")
    print(f"  curl 'http://{host}:{port}/api/check_update?current_version=1.0.0'")
    print()
    print("按 Ctrl+C 停止服務器")
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[Mock Server] 收到中斷信號，正在關閉服務器...")
        server.shutdown()
        server.server_close()
        print("[Mock Server] 服務器已關閉")

if __name__ == "__main__":
    main()