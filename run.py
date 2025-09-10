#!/usr/bin/env python3
"""
同时启动并关闭 前端 + 后端服务
兼容 Windows / Linux
"""
import subprocess
import signal
import sys
import os

processes = []

def cleanup(sig, frame):
    print("\n🛑 收到退出信号，正在关闭服务...")
    for p in processes:
        if p.poll() is None:  # 进程还在运行
            p.terminate()
    sys.exit(0)

if __name__ == "__main__":
    print("🚀 启动 deeplit-analyzer 全部服务...")
    print("📚 学术文献处理AI系统")
    print("=" * 50)

    signal.signal(signal.SIGINT, cleanup)   # 捕捉 Ctrl+C
    signal.signal(signal.SIGTERM, cleanup)  # 捕捉 kill 信号

    # 启动后端
    backend = subprocess.Popen([sys.executable, "start_backend.py"])
    processes.append(backend)

    # 启动前端
    frontend = subprocess.Popen([sys.executable, "start_frontend.py"])
    processes.append(frontend)

    # 等待子进程
    backend.wait()
    frontend.wait()
