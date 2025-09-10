#!/usr/bin/env python3
"""
启动前端服务
"""
import subprocess
import sys
import os

if __name__ == "__main__":
    print("🚀 启动 deeplit-analyzer 前端服务...")
    print("📚 学术文献处理AI系统 - 用户界面")
    print("=" * 50)
    
    # 启动Streamlit应用
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", 
        "frontend/streamlit_app.py",
        "--server.port", "8501",
        "--server.address", "0.0.0.0"
    ])
