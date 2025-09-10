#!/usr/bin/env python3
"""
测试SummarizerService
"""
import asyncio
import sys
import os

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.services.summarizer.summarizer_service import SummarizerService
from backend.app.core.config import settings

async def test_summarizer():
    """测试总结服务"""
    print("测试SummarizerService...")
    print(f"API Key: {settings.deepseek_api_key[:10]}..." if settings.deepseek_api_key else "API Key: None")
    print(f"Base URL: {settings.deepseek_base_url}")
    
    summarizer = SummarizerService()
    print(f"Summarizer API Key: {summarizer.api_key[:10]}..." if summarizer.api_key else "Summarizer API Key: None")
    print(f"Summarizer Base URL: {summarizer.base_url}")
    
    # 测试简单的API调用
    test_prompt = "请总结以下内容：这是一篇关于人工智能的学术论文。"
    result = await summarizer._call_deepseek_api(test_prompt)
    print(f"API调用结果: {result}")

if __name__ == "__main__":
    asyncio.run(test_summarizer())
