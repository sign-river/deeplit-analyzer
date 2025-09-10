#!/usr/bin/env python3
"""
启动后端服务
"""
import uvicorn
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("🚀 启动 ScholarMind AI 后端服务...")
    print("📚 学术文献处理AI系统")
    print("=" * 50)
    
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
