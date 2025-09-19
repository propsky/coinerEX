#!/usr/bin/env python3
"""
Hello OTA 測試套件
測試OTA更新功能的各種情況
"""

import os
import sys
import time
import json
import unittest
import tempfile
import threading
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加app目錄到Python路徑
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from ota_manager import OTAManager
from config import Config
import requests

class TestOTAManager(unittest.TestCase):
    """OTA管理器測試"""

    def setUp(self):
        """測試前設定"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.ota_manager = OTAManager()

        # 使用臨時目錄
        self.ota_manager.temp_dir = self.temp_dir / "temp"
        self.ota_manager.backup_dir = self.temp_dir / "backup"

    def tearDown(self):
        """測試後清理"""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_verify_checksum(self):
        """測試檔案校驗和驗證"""
        # 建立測試檔案
        test_file = self.temp_dir / "test.txt"
        test_content = b"Hello, OTA Test!"

        with open(test_file, 'wb') as f:
            f.write(test_content)

        # 計算正確的校驗和
        import hashlib
        expected_checksum = hashlib.sha256(test_content).hexdigest()

        # 測試正確校驗和
        self.assertTrue(
            self.ota_manager._verify_checksum(test_file, expected_checksum)
        )

        # 測試錯誤校驗和
        wrong_checksum = "wrong_checksum"
        self.assertFalse(
            self.ota_manager._verify_checksum(test_file, wrong_checksum)
        )

    def test_backup_current_version(self):
        """測試當前版本備份"""
        # 模擬應用程式目錄
        mock_app_dir = self.temp_dir / "app"
        mock_app_dir.mkdir()

        test_file = mock_app_dir / "test.py"
        with open(test_file, 'w') as f:
            f.write("print('test')")

        # 設定模擬目錄
        self.ota_manager.app_dir = mock_app_dir

        # 執行備份
        with patch('hello_ota.app.version.__version__', '1.0.0'):
            self.ota_manager._backup_current_version()

        # 檢查備份是否存在
        backup_files = list(self.ota_manager.backup_dir.glob('backup_1.0.0_*'))
        self.assertEqual(len(backup_files), 1)

        # 檢查備份內容
        backup_test_file = backup_files[0] / "test.py"
        self.assertTrue(backup_test_file.exists())

    @patch('requests.get')
    def test_download_update_success(self, mock_get):
        """測試成功下載更新"""
        # 模擬HTTP回應
        test_content = b"fake update content"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-length': str(len(test_content))}
        mock_response.iter_content.return_value = [test_content]
        mock_get.return_value = mock_response

        # 計算校驗和
        import hashlib
        expected_checksum = hashlib.sha256(test_content).hexdigest()

        update_info = {
            'download_url': 'http://example.com/update.tar.gz',
            'checksum': expected_checksum
        }

        # 執行下載
        result = self.ota_manager.download_update(update_info)

        # 驗證結果
        self.assertTrue(result.exists())
        with open(result, 'rb') as f:
            content = f.read()
        self.assertEqual(content, test_content)

    @patch('requests.get')
    def test_download_update_checksum_fail(self, mock_get):
        """測試下載檔案校驗和失敗"""
        # 模擬HTTP回應
        test_content = b"fake update content"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-length': str(len(test_content))}
        mock_response.iter_content.return_value = [test_content]
        mock_get.return_value = mock_response

        update_info = {
            'download_url': 'http://example.com/update.tar.gz',
            'checksum': 'wrong_checksum'
        }

        # 執行下載，應該拋出異常
        with self.assertRaises(Exception) as context:
            self.ota_manager.download_update(update_info)

        self.assertIn("校驗失敗", str(context.exception))

class TestOTAIntegration(unittest.TestCase):
    """OTA整合測試"""

    @classmethod
    def setUpClass(cls):
        """測試類別設定"""
        cls.mock_server = None
        cls.mock_server_thread = None

    @classmethod
    def tearDownClass(cls):
        """測試類別清理"""
        if cls.mock_server:
            cls.mock_server.shutdown()

    def setUp(self):
        """測試前設定"""
        # 啟動模擬服務器
        self._start_mock_server()

    def tearDown(self):
        """測試後清理"""
        # 停止模擬服務器
        self._stop_mock_server()

    def _start_mock_server(self):
        """啟動模擬服務器"""
        def run_server():
            from mock_server import MockUpdateServerHandler
            from http.server import HTTPServer

            server = HTTPServer(('localhost', 9001), MockUpdateServerHandler)
            self.__class__.mock_server = server
            server.serve_forever()

        self.__class__.mock_server_thread = threading.Thread(target=run_server)
        self.__class__.mock_server_thread.daemon = True
        self.__class__.mock_server_thread.start()

        # 等待服務器啟動
        time.sleep(1)

    def _stop_mock_server(self):
        """停止模擬服務器"""
        if self.__class__.mock_server:
            self.__class__.mock_server.shutdown()
            self.__class__.mock_server = None

    def test_check_update_api(self):
        """測試檢查更新API"""
        try:
            response = requests.get(
                "http://localhost:9001/api/check_update",
                params={"current_version": "1.0.0"},
                timeout=5
            )

            self.assertEqual(response.status_code, 200)

            data = response.json()
            self.assertIn('has_update', data)
            self.assertIn('current_version', data)

        except requests.exceptions.RequestException:
            self.skipTest("模擬服務器未啟動")

    def test_download_update_file(self):
        """測試下載更新檔案"""
        try:
            response = requests.get(
                "http://localhost:9001/updates/v1.1.0.tar.gz",
                timeout=5
            )

            # 如果檔案存在，應該返回200
            # 如果檔案不存在，應該返回404
            self.assertIn(response.status_code, [200, 404])

        except requests.exceptions.RequestException:
            self.skipTest("模擬服務器未啟動")

class TestConfig(unittest.TestCase):
    """設定管理測試"""

    def setUp(self):
        """測試前設定"""
        self.temp_config_file = Path(tempfile.mktemp(suffix='.json'))

    def tearDown(self):
        """測試後清理"""
        if self.temp_config_file.exists():
            self.temp_config_file.unlink()

    def test_config_creation(self):
        """測試設定檔建立"""
        config = Config(str(self.temp_config_file))

        # 檢查設定檔是否建立
        self.assertTrue(self.temp_config_file.exists())

        # 檢查預設設定
        self.assertEqual(config.get('app.name'), 'hello-ota')
        self.assertEqual(config.get('app.port'), 8080)
        self.assertTrue(config.get('ota.enabled'))

    def test_config_get_set(self):
        """測試設定值取得和設定"""
        config = Config(str(self.temp_config_file))

        # 測試設定新值
        config.set('test.value', 'test_data')
        self.assertEqual(config.get('test.value'), 'test_data')

        # 測試巢狀設定
        config.set('nested.deep.value', 'deep_data')
        self.assertEqual(config.get('nested.deep.value'), 'deep_data')

        # 測試預設值
        self.assertEqual(config.get('nonexistent.key', 'default'), 'default')

def run_performance_test():
    """執行效能測試"""
    print("執行效能測試...")

    # 測試大檔案下載模擬
    import tempfile
    import time

    large_file = Path(tempfile.mktemp())
    try:
        # 建立10MB測試檔案
        with open(large_file, 'wb') as f:
            f.write(b'0' * (10 * 1024 * 1024))

        # 測試校驗和計算時間
        ota_manager = OTAManager()
        start_time = time.time()

        import hashlib
        sha256_hash = hashlib.sha256()
        with open(large_file, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        checksum = sha256_hash.hexdigest()

        end_time = time.time()

        print(f"10MB檔案校驗和計算時間: {end_time - start_time:.2f}秒")
        print(f"校驗和: {checksum[:16]}...")

    finally:
        if large_file.exists():
            large_file.unlink()

def run_manual_tests():
    """執行手動測試"""
    print("執行手動測試...")
    print("請在另一個終端執行以下命令來測試Hello OTA應用程式：")
    print()
    print("1. 啟動Hello OTA應用程式:")
    print("   cd ../app && python3 main.py")
    print()
    print("2. 在另一個終端啟動模擬服務器:")
    print("   python3 mock_server.py")
    print()
    print("3. 測試API:")
    print("   curl http://localhost:8080/health")
    print("   curl http://localhost:8080/version")
    print("   curl http://localhost:8080/ota/status")
    print()
    print("4. 觸發更新:")
    print("   curl -X POST http://localhost:8080/trigger_update \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{\"version\": \"1.1.0\", \"update_url\": \"http://localhost:9000/updates/v1.1.0.tar.gz\"}'")
    print()

def main():
    """主測試函數"""
    print("Hello OTA 測試套件")
    print("==================")
    print()

    # 檢查參數
    if len(sys.argv) > 1:
        if sys.argv[1] == '--performance':
            run_performance_test()
            return
        elif sys.argv[1] == '--manual':
            run_manual_tests()
            return

    # 執行單元測試
    print("執行單元測試...")
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加測試
    suite.addTests(loader.loadTestsFromTestCase(TestOTAManager))
    suite.addTests(loader.loadTestsFromTestCase(TestConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestOTAIntegration))

    # 執行測試
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 輸出結果
    print()
    print("測試結果:")
    print(f"  執行測試: {result.testsRun}")
    print(f"  失敗: {len(result.failures)}")
    print(f"  錯誤: {len(result.errors)}")

    if result.failures:
        print("\n失敗的測試:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")

    if result.errors:
        print("\n錯誤的測試:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")

    # 執行效能測試
    print()
    run_performance_test()

    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(main())