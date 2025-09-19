#!/usr/bin/env python3
"""
OTA更新包建立工具
用於建立Hello OTA應用程式的更新包
"""

import os
import sys
import json
import tarfile
import hashlib
import argparse
from pathlib import Path
from datetime import datetime

class UpdatePackageCreator:
    """更新包建立器"""

    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.project_dir = self.script_dir.parent

    def create_update_package(self, version, source_dir=None, output_dir=None):
        """建立更新包"""
        if source_dir is None:
            source_dir = self.project_dir / "app"

        if output_dir is None:
            output_dir = self.script_dir

        source_dir = Path(source_dir)
        output_dir = Path(output_dir)

        if not source_dir.exists():
            raise FileNotFoundError(f"來源目錄不存在: {source_dir}")

        print(f"建立更新包 v{version}")
        print(f"來源目錄: {source_dir}")
        print(f"輸出目錄: {output_dir}")
        print()

        # 建立版本目錄
        version_dir = output_dir / f"v{version}"
        if version_dir.exists():
            import shutil
            shutil.rmtree(version_dir)

        version_dir.mkdir(parents=True)

        # 建立app子目錄
        app_dir = version_dir / "app"
        app_dir.mkdir()

        # 複製檔案
        self._copy_source_files(source_dir, app_dir, version)

        # 建立壓縮檔
        tar_file = self._create_tar_package(version_dir, output_dir, version)

        # 建立更新資訊檔案
        update_info = self._create_update_info(tar_file, version)
        info_file = output_dir / f"v{version}_info.json"

        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(update_info, f, indent=2, ensure_ascii=False)

        print(f"✅ 更新包建立完成:")
        print(f"   - 更新包: {tar_file}")
        print(f"   - 資訊檔: {info_file}")
        print(f"   - 檔案大小: {tar_file.stat().st_size:,} bytes")
        print(f"   - 校驗和: {update_info['checksum']}")

        return tar_file, info_file

    def _copy_source_files(self, source_dir, target_dir, version):
        """複製來源檔案"""
        import shutil

        print("複製來源檔案...")

        for file_path in source_dir.glob("*.py"):
            target_file = target_dir / file_path.name

            if file_path.name == "version.py":
                # 特殊處理版本檔案
                self._create_version_file(target_file, version)
            else:
                shutil.copy2(file_path, target_file)

            print(f"  ✓ {file_path.name}")

    def _create_version_file(self, target_file, version):
        """建立版本檔案"""
        build_date = datetime.now().strftime("%Y-%m-%d")

        version_content = f'''"""
應用程式版本資訊
"""

__version__ = "{version}"
__build_date__ = "{build_date}"
__description__ = "Hello OTA 示範應用程式 - 更新版本 {version}"

def get_version_info():
    """取得完整版本資訊"""
    return {{
        "version": __version__,
        "build_date": __build_date__,
        "description": __description__
    }}'''

        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(version_content)

        print(f"  ✓ version.py (更新到 v{version})")

    def _create_tar_package(self, version_dir, output_dir, version):
        """建立tar壓縮包"""
        tar_file = output_dir / f"v{version}.tar.gz"

        print(f"建立壓縮包: {tar_file.name}")

        with tarfile.open(tar_file, "w:gz") as tar:
            tar.add(version_dir, arcname=f"v{version}")

        return tar_file

    def _calculate_checksum(self, file_path):
        """計算檔案SHA256校驗和"""
        sha256_hash = hashlib.sha256()

        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)

        return sha256_hash.hexdigest()

    def _create_update_info(self, tar_file, version):
        """建立更新資訊"""
        checksum = self._calculate_checksum(tar_file)
        file_size = tar_file.stat().st_size

        return {
            "version": version,
            "filename": tar_file.name,
            "size": file_size,
            "checksum": checksum,
            "created_at": datetime.now().isoformat(),
            "download_url": f"http://localhost:9000/updates/{tar_file.name}",
            "release_notes": f"更新到版本 {version}",
            "requirements": {
                "min_version": "1.0.0",
                "python_version": ">=3.8"
            },
            "changes": [
                f"更新到版本 {version}",
                "效能優化",
                "錯誤修正"
            ]
        }

    def list_available_updates(self):
        """列出可用的更新包"""
        print("可用的更新包:")
        print("=============")

        updates = []
        for tar_file in self.script_dir.glob("v*.tar.gz"):
            info_file = self.script_dir / f"{tar_file.stem}_info.json"

            if info_file.exists():
                with open(info_file, 'r', encoding='utf-8') as f:
                    info = json.load(f)
                updates.append(info)

        if not updates:
            print("沒有找到更新包")
            return

        updates.sort(key=lambda x: x['version'], reverse=True)

        for update in updates:
            print(f"版本: {update['version']}")
            print(f"  檔案: {update['filename']}")
            print(f"  大小: {update['size']:,} bytes")
            print(f"  建立時間: {update['created_at']}")
            print(f"  校驗和: {update['checksum'][:16]}...")
            print()

    def verify_package(self, version):
        """驗證更新包完整性"""
        tar_file = self.script_dir / f"v{version}.tar.gz"
        info_file = self.script_dir / f"v{version}_info.json"

        if not tar_file.exists():
            print(f"❌ 更新包不存在: {tar_file}")
            return False

        if not info_file.exists():
            print(f"❌ 資訊檔不存在: {info_file}")
            return False

        # 載入資訊檔
        with open(info_file, 'r', encoding='utf-8') as f:
            info = json.load(f)

        # 驗證檔案大小
        actual_size = tar_file.stat().st_size
        expected_size = info['size']

        if actual_size != expected_size:
            print(f"❌ 檔案大小不符: 預期 {expected_size}, 實際 {actual_size}")
            return False

        # 驗證校驗和
        actual_checksum = self._calculate_checksum(tar_file)
        expected_checksum = info['checksum']

        if actual_checksum != expected_checksum:
            print(f"❌ 校驗和不符:")
            print(f"   預期: {expected_checksum}")
            print(f"   實際: {actual_checksum}")
            return False

        print(f"✅ 更新包 v{version} 驗證通過")
        return True

    def extract_package(self, version, extract_dir=None):
        """解壓縮更新包"""
        tar_file = self.script_dir / f"v{version}.tar.gz"

        if not tar_file.exists():
            print(f"❌ 更新包不存在: {tar_file}")
            return False

        if extract_dir is None:
            extract_dir = self.script_dir / f"extracted_v{version}"
        else:
            extract_dir = Path(extract_dir)

        print(f"解壓縮更新包到: {extract_dir}")

        if extract_dir.exists():
            import shutil
            shutil.rmtree(extract_dir)

        extract_dir.mkdir(parents=True)

        with tarfile.open(tar_file, "r:gz") as tar:
            tar.extractall(extract_dir)

        print(f"✅ 更新包解壓縮完成")

        # 列出解壓縮的檔案
        print("\n解壓縮的檔案:")
        for file_path in extract_dir.rglob("*"):
            if file_path.is_file():
                rel_path = file_path.relative_to(extract_dir)
                print(f"  {rel_path}")

        return True

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="Hello OTA 更新包建立工具")

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 建立更新包命令
    create_parser = subparsers.add_parser("create", help="建立更新包")
    create_parser.add_argument("--version", required=True, help="版本號 (例如: 1.1.0)")
    create_parser.add_argument("--source", help="來源目錄路徑")
    create_parser.add_argument("--output", help="輸出目錄路徑")

    # 列出更新包命令
    list_parser = subparsers.add_parser("list", help="列出可用更新包")

    # 驗證更新包命令
    verify_parser = subparsers.add_parser("verify", help="驗證更新包")
    verify_parser.add_argument("--version", required=True, help="要驗證的版本號")

    # 解壓縮更新包命令
    extract_parser = subparsers.add_parser("extract", help="解壓縮更新包")
    extract_parser.add_argument("--version", required=True, help="要解壓縮的版本號")
    extract_parser.add_argument("--output", help="解壓縮目標目錄")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    creator = UpdatePackageCreator()

    try:
        if args.command == "create":
            creator.create_update_package(
                version=args.version,
                source_dir=args.source,
                output_dir=args.output
            )

        elif args.command == "list":
            creator.list_available_updates()

        elif args.command == "verify":
            if not creator.verify_package(args.version):
                return 1

        elif args.command == "extract":
            if not creator.extract_package(args.version, args.output):
                return 1

        return 0

    except Exception as e:
        print(f"❌ 錯誤: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())