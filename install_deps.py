#!/usr/bin/env python3
"""
依赖安装脚本
"""
import subprocess
import sys

def install_package(package):
    """安装单个包"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--user"])
        print(f"✓ 成功安装: {package}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 安装失败: {package} - {e}")
        return False

def main():
    packages = [
        "fastapi",
        "uvicorn",
        "python-multipart", 
        "pydantic",
        "pymupdf",
        "python-docx",
        "pillow",
        "pytesseract",
        "beautifulsoup4",
        "requests",
        "sentence-transformers",
        "faiss-cpu",
        "numpy",
        "rapidfuzz",
        "python-dotenv",
        "tenacity"
    ]
    
    print("开始安装依赖包...")
    success_count = 0
    
    for package in packages:
        if install_package(package):
            success_count += 1
    
    print(f"\n安装完成: {success_count}/{len(packages)} 个包安装成功")
    
    # 测试关键包
    print("\n测试关键包导入...")
    test_packages = ["fastapi", "uvicorn", "pydantic"]
    for pkg in test_packages:
        try:
            __import__(pkg)
            print(f"✓ {pkg} 导入成功")
        except ImportError as e:
            print(f"✗ {pkg} 导入失败: {e}")

if __name__ == "__main__":
    main()
