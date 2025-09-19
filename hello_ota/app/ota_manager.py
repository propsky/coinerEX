"""
OTA (Over-The-Air) 更新管理器
"""
import os
import sys
import json
import hashlib
import tarfile
import shutil
import subprocess
import logging
import requests
from pathlib import Path
from datetime import datetime
from .config import config

logger = logging.getLogger(__name__)

class OTAManager:
    def __init__(self):
        self.app_dir = Path("/opt/hello-ota")
        self.backup_dir = Path("/var/backups/hello-ota")
        self.temp_dir = Path("/tmp/hello-ota-update")
        self.update_script = Path("/tmp/hello_ota_updater.py")

        # 確保目錄存在
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def check_for_updates(self):
        """檢查是否有可用更新"""
        try:
            from .version import __version__

            update_server = config.get('ota.update_server')
            response = requests.get(
                f"{update_server}/api/check_update",
                params={"current_version": __version__},
                timeout=30
            )

            if response.status_code == 200:
                update_info = response.json()
                if update_info.get('has_update', False):
                    logger.info(f"發現新版本: {update_info['latest_version']}")
                    return update_info
                else:
                    logger.debug("目前已是最新版本")
                    return None
            else:
                logger.warning(f"檢查更新失敗: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"檢查更新時發生錯誤: {e}")
            return None

    def download_update(self, update_info):
        """下載更新檔案"""
        download_url = update_info['download_url']
        expected_checksum = update_info['checksum']

        logger.info(f"開始下載更新: {download_url}")

        # 清理臨時目錄
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        self.temp_dir.mkdir(parents=True)

        update_file = self.temp_dir / "update.tar.gz"

        try:
            # 下載檔案，支援斷點續傳
            self._download_with_progress(download_url, update_file)

            # 驗證檔案完整性
            if self._verify_checksum(update_file, expected_checksum):
                logger.info("更新檔案下載並驗證成功")
                return update_file
            else:
                raise Exception("檔案校驗失敗")

        except Exception as e:
            logger.error(f"下載更新失敗: {e}")
            raise

    def _download_with_progress(self, url, file_path):
        """帶進度的檔案下載"""
        response = requests.get(url, stream=True)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0

        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)

                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        logger.debug(f"下載進度: {progress:.1f}%")

    def _verify_checksum(self, file_path, expected_checksum):
        """驗證檔案SHA256校驗和"""
        sha256_hash = hashlib.sha256()

        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)

        actual_checksum = sha256_hash.hexdigest()
        return actual_checksum == expected_checksum

    def apply_update(self, update_file, update_info):
        """套用更新"""
        try:
            logger.info("開始套用更新")

            # 1. 備份當前版本
            self._backup_current_version()

            # 2. 解壓縮更新檔案
            extract_dir = self.temp_dir / "extracted"
            self._extract_update(update_file, extract_dir)

            # 3. 建立更新執行腳本
            self._create_update_script(extract_dir, update_info)

            # 4. 排程更新並退出
            self._schedule_update_and_exit()

        except Exception as e:
            logger.error(f"套用更新失敗: {e}")
            raise

    def _backup_current_version(self):
        """備份當前版本"""
        from .version import __version__

        backup_name = f"backup_{__version__}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path = self.backup_dir / backup_name

        logger.info(f"備份當前版本到: {backup_path}")

        # 複製當前應用程式目錄
        shutil.copytree(self.app_dir, backup_path, symlinks=True)

        # 清理舊備份（保留最近N個）
        self._cleanup_old_backups()

    def _cleanup_old_backups(self):
        """清理舊備份"""
        backup_count = config.get('ota.backup_count', 3)
        backups = sorted(self.backup_dir.glob('backup_*'), key=lambda x: x.stat().st_ctime)

        while len(backups) > backup_count:
            old_backup = backups.pop(0)
            logger.info(f"刪除舊備份: {old_backup}")
            shutil.rmtree(old_backup)

    def _extract_update(self, update_file, extract_dir):
        """解壓縮更新檔案"""
        logger.info(f"解壓縮更新檔案到: {extract_dir}")

        if extract_dir.exists():
            shutil.rmtree(extract_dir)
        extract_dir.mkdir(parents=True)

        with tarfile.open(update_file, 'r:gz') as tar:
            tar.extractall(extract_dir)

    def _create_update_script(self, source_dir, update_info):
        """建立更新執行腳本"""
        script_content = f'''#!/usr/bin/env python3
"""
自動生成的OTA更新執行腳本
"""
import os
import sys
import time
import shutil
import subprocess
import json
from pathlib import Path

def log(message):
    print(f"[OTA] {{message}}")

def main():
    log("OTA更新執行腳本啟動")

    # 等待主程式完全退出
    time.sleep(3)

    app_dir = Path("/opt/hello-ota")
    source_dir = Path("{source_dir}")
    backup_info_file = Path("/var/lib/hello-ota/last_update.json")

    try:
        # 記錄更新資訊
        update_info = {update_info}
        backup_info_file.parent.mkdir(parents=True, exist_ok=True)
        with open(backup_info_file, 'w') as f:
            json.dump(update_info, f, indent=2)

        # 執行更新
        log("開始複製新版本檔案")

        # 使用原子性操作
        temp_app_dir = app_dir.parent / "hello-ota-new"
        if temp_app_dir.exists():
            shutil.rmtree(temp_app_dir)

        shutil.copytree(source_dir / "app", temp_app_dir)

        # 原子性替換
        old_app_dir = app_dir.parent / "hello-ota-old"
        if old_app_dir.exists():
            shutil.rmtree(old_app_dir)

        if app_dir.exists():
            app_dir.rename(old_app_dir)
        temp_app_dir.rename(app_dir)

        log("檔案更新完成")

        # 重啟服務
        log("重啟hello-ota服務")
        subprocess.run(["sudo", "systemctl", "start", "hello-ota"], check=True)

        log("OTA更新完成成功")

        # 清理
        if old_app_dir.exists():
            shutil.rmtree(old_app_dir)

    except Exception as e:
        log(f"OTA更新失敗: {{e}}")

        # 嘗試回滾
        try:
            if old_app_dir.exists():
                log("執行回滾")
                if app_dir.exists():
                    shutil.rmtree(app_dir)
                old_app_dir.rename(app_dir)

                subprocess.run(["sudo", "systemctl", "start", "hello-ota"], check=True)
                log("回滾完成")
            else:
                log("無法回滾：找不到備份")
        except Exception as rollback_error:
            log(f"回滾失敗: {{rollback_error}}")

        sys.exit(1)

if __name__ == "__main__":
    main()
'''

        with open(self.update_script, 'w', encoding='utf-8') as f:
            f.write(script_content)

        # 設定執行權限
        os.chmod(self.update_script, 0o755)
        logger.info(f"更新腳本已建立: {self.update_script}")

    def _schedule_update_and_exit(self):
        """排程更新執行並優雅退出"""
        logger.info("排程更新執行")

        # 在背景執行更新腳本
        subprocess.Popen([
            sys.executable, str(self.update_script)
        ], start_new_session=True)

        # 停止當前服務
        logger.info("停止當前服務")
        subprocess.run(["sudo", "systemctl", "stop", "hello-ota"])

        # 退出當前程式
        sys.exit(0)

    def get_update_history(self):
        """取得更新歷史"""
        history_file = Path("/var/lib/hello-ota/update_history.json")
        if history_file.exists():
            with open(history_file, 'r') as f:
                return json.load(f)
        return []

    def add_update_record(self, update_info):
        """新增更新記錄"""
        history_file = Path("/var/lib/hello-ota/update_history.json")
        history_file.parent.mkdir(parents=True, exist_ok=True)

        history = self.get_update_history()

        record = {
            "timestamp": datetime.now().isoformat(),
            "version": update_info.get('version'),
            "status": "completed",
            "details": update_info
        }

        history.append(record)

        # 只保留最近50筆記錄
        history = history[-50:]

        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)