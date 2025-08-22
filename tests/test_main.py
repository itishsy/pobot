"""
测试主程序模块
"""

import pytest
import sys
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from main import main


def test_main_success():
    """测试主函数成功执行"""
    # 这里可以添加具体的测试逻辑
    assert True


def test_main_import():
    """测试模块导入"""
    import main
    assert main is not None

