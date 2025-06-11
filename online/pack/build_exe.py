#!/usr/bin/env python3
"""
Build script to create executable file for BCI Controller
使用 PyInstaller 将 BCI Controller 打包成 exe 文件
"""

import os
import sys
import subprocess


def install_dependencies():
    """安装必要的依赖"""
    dependencies = [
        'pyinstaller',
        'requests',
        'websocket-client'
    ]

    for dep in dependencies:
        print(f"安装 {dep}...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', dep])


def build_executable():
    """构建可执行文件"""
    print("开始构建 BCI Controller 可执行文件...")

    # PyInstaller 命令
    cmd = [
        'pyinstaller',
        '--onefile',  # 单文件模式
        '--windowed',  # 无控制台窗口
        '--name=BCI_Controller',  # 可执行文件名
        '--icon=icon.ico' if os.path.exists('icon.ico') else '',  # 图标（如果存在）
        'bci_controller.py'
    ]

    # 移除空的图标参数
    cmd = [arg for arg in cmd if arg]

    try:
        subprocess.run(cmd, check=True)
        print("构建成功！可执行文件位于 dist/BCI_Controller.exe")
    except subprocess.CalledProcessError as e:
        print(f"构建失败: {e}")
        return False

    return True


if __name__ == "__main__":
    print("BCI Controller 可执行文件构建器")
    print("=" * 40)

    # 检查是否存在主文件
    if not os.path.exists('bci_controller.py'):
        print("错误: 找不到 bci_controller.py 文件")
        sys.exit(1)

    # 安装依赖
    install_dependencies()

    # 构建可执行文件
    if build_executable():
        print("\n构建完成！")
        print("可执行文件路径: dist/BCI_Controller.exe")
    else:
        print("\n构建失败，请检查错误信息")