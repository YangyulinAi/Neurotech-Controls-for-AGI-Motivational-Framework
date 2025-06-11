#!/usr/bin/env python3
"""
简化的BCI Controller打包脚本
避免pathlib冲突问题
"""

import os
import sys
import subprocess


def check_environment():
    """检查Python环境"""
    print(f"Python版本: {sys.version}")
    print(f"Python路径: {sys.executable}")


def manual_removal_guide():
    """显示手动移除pathlib的指导"""
    print("\n" + "=" * 50)
    print("需要手动移除pathlib包")
    print("=" * 50)
    print("请按以下步骤操作：")
    print("\n1. 打开命令提示符 (以管理员身份运行)")
    print("2. 运行以下命令之一：")
    print("   conda remove pathlib")
    print("   或者")
    print("   pip uninstall pathlib")
    print("\n3. 移除完成后，重新运行此脚本")
    print("=" * 50)


def install_pyinstaller():
    """安装PyInstaller"""
    try:
        print("安装PyInstaller...")
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'],
                                capture_output=True, text=True)
        if result.returncode == 0:
            print("PyInstaller安装成功")
            return True
        else:
            print(f"安装失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"安装异常: {e}")
        return False


def try_build():
    """尝试构建可执行文件"""
    try:
        print("尝试构建可执行文件...")

        # 简化的PyInstaller命令
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--onefile',
            '--name=BCI_Controller',
            'bci_controller.py'
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print("构建成功！")
            print("可执行文件位于: dist/BCI_Controller.exe")
            return True
        else:
            print("构建失败:")
            print(result.stderr)

            # 检查是否是pathlib冲突
            if 'pathlib' in result.stderr.lower():
                manual_removal_guide()

            return False

    except Exception as e:
        print(f"构建异常: {e}")
        return False


def create_spec_file():
    """创建PyInstaller spec文件来避免冲突"""
    import os
    current_dir = os.getcwd()

    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None

# 确保使用绝对路径
script_path = r'{current_dir}'

a = Analysis(
    ['bci_controller.py'],
    pathex=[script_path],
    binaries=[],
    datas=[],
    hiddenimports=['tkinter', 'tkinter.ttk', 'tkinter.scrolledtext', 'websocket', 'requests', 'threading', 'subprocess'],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=['pathlib'],  # 排除pathlib
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='BCI_Controller',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 显示控制台以便调试
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''

    with open('bci_controller.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)

    print("已创建spec文件")


def build_with_spec():
    """使用spec文件构建"""
    try:
        print("使用spec文件构建...")
        result = subprocess.run([sys.executable, '-m', 'PyInstaller', 'bci_controller.spec'],
                                capture_output=True, text=True)

        if result.returncode == 0:
            print("构建成功！")
            print("可执行文件位于: dist/BCI_Controller.exe")
            return True
        else:
            print("构建失败:")
            print(result.stderr)
            return False

    except Exception as e:
        print(f"构建异常: {e}")
        return False


if __name__ == "__main__":
    print("BCI Controller 简化打包器")
    print("=" * 40)

    # 检查环境
    check_environment()

    # 检查主文件
    if not os.path.exists('bci_controller.py'):
        print("错误: 找不到 bci_controller.py 文件")
        sys.exit(1)

    # 安装PyInstaller
    if not install_pyinstaller():
        print("无法安装PyInstaller，退出")
        sys.exit(1)

    # 先尝试直接构建
    if try_build():
        print("\n构建完成！")
    else:
        print("\n直接构建失败，尝试使用spec文件...")
        create_spec_file()
        if build_with_spec():
            print("\n构建完成！")
        else:
            print("\n构建失败，请手动移除pathlib包后重试")
            manual_removal_guide()