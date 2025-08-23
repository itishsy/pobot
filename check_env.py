#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python环境检查脚本
验证所有依赖包是否正确安装
"""

import sys

def check_python_version():
    """检查Python版本"""
    print(f"🐍 Python版本: {sys.version}")
    if sys.version_info >= (3, 6):
        print("✅ Python版本满足要求 (>= 3.6)")
        return True
    else:
        print("❌ Python版本过低，需要3.6或更高版本")
        return False

def check_dependencies():
    """检查关键依赖包"""
    dependencies = [
        ('requests', 'HTTP请求库'),
        ('pandas', '数据处理库'),
        ('numpy', '数值计算库'),
        ('torch', 'PyTorch深度学习库'),
        ('selenium', 'Web自动化库'),
        ('peewee', 'ORM数据库库'),
        ('sqlalchemy', 'SQL工具库'),
        ('treys', '德州扑克牌型评估库'),
        ('ddddocr', 'OCR识别库'),
        ('PyAutoGUI', 'GUI自动化库')
    ]
    
    print("\n📦 依赖包检查:")
    all_ok = True
    
    for package, description in dependencies:
        try:
            __import__(package)
            print(f"✅ {package} - {description}")
        except ImportError:
            print(f"❌ {package} - {description} (未安装)")
            all_ok = False
    
    return all_ok

def check_project_imports():
    """检查项目模块导入"""
    print("\n🔧 项目模块检查:")
    try:
        from src.train.cli import PokerGame, Player
        print("✅ src.train.cli 模块导入成功")
        
        from src.train.cal import distribute_pot
        print("✅ src.train.cal 模块导入成功")
        
        return True
    except ImportError as e:
        print(f"❌ 项目模块导入失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("🚀 Pobot项目环境检查")
    print("=" * 50)
    
    # 检查Python版本
    python_ok = check_python_version()
    
    # 检查依赖包
    deps_ok = check_dependencies()
    
    # 检查项目模块
    project_ok = check_project_imports()
    
    print("\n" + "=" * 50)
    print("📊 检查结果汇总:")
    print(f"Python版本: {'✅' if python_ok else '❌'}")
    print(f"依赖包: {'✅' if deps_ok else '❌'}")
    print(f"项目模块: {'✅' if project_ok else '❌'}")
    
    if all([python_ok, deps_ok, project_ok]):
        print("\n🎉 环境配置完成！所有检查都通过了。")
        print("现在可以运行德州扑克游戏了：")
        print("  python -m src.train.cli")
    else:
        print("\n⚠️  环境配置存在问题，请检查上述错误信息。")
    
    print("=" * 50)

if __name__ == "__main__":
    main()

