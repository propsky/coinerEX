"""
應用程式版本資訊
"""

__version__ = "1.0.0"
__build_date__ = "2025-01-20"
__description__ = "Hello OTA 示範應用程式"

def get_version_info():
    """取得完整版本資訊"""
    return {
        "version": __version__,
        "build_date": __build_date__,
        "description": __description__
    }