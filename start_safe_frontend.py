#!/usr/bin/env python3
"""
启动安全版前端服务
"""
import subprocess
import sys
import os

if __name__ == "__main__":
    print("🚀 启动简化版前端...")
    print("📚 学术文献处理AI系统 - 安全版本")
    print("=" * 50)
    print("正在启动安全版前端...")
    
    # 启动Streamlit应用
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", 
        "frontend/streamlit_app.py",
        "--server.port", "8503",
        "--server.address", "localhost"
    ])