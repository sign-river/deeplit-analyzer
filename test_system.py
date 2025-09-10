#!/usr/bin/env python3
"""
系统测试脚本
"""
import sys
import os

def test_imports():
    """测试导入"""
    print("🔍 测试系统依赖...")
    
    try:
        import fastapi
        print(f"✅ FastAPI {fastapi.__version__}")
    except ImportError as e:
        print(f"❌ FastAPI 导入失败: {e}")
        return False
    
    try:
        import uvicorn
        print(f"✅ Uvicorn 可用")
    except ImportError as e:
        print(f"❌ Uvicorn 导入失败: {e}")
        return False
    
    try:
        import streamlit
        print(f"✅ Streamlit 可用")
    except ImportError as e:
        print(f"❌ Streamlit 导入失败: {e}")
        return False
    
    try:
        import pydantic
        print(f"✅ Pydantic 可用")
    except ImportError as e:
        print(f"❌ Pydantic 导入失败: {e}")
        return False
    
    return True

def test_backend():
    """测试后端"""
    print("\n🔍 测试后端服务...")
    
    try:
        # 添加后端路径
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
        
        from app.core.config import settings
        print(f"✅ 配置加载成功: {settings.app_name}")
        
        from app.models.document import Document, DocumentType
        print("✅ 数据模型加载成功")
        
        return True
    except Exception as e:
        print(f"❌ 后端测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 ScholarMind AI 系统测试")
    print("=" * 50)
    
    # 测试导入
    if not test_imports():
        print("\n❌ 依赖测试失败，请检查安装")
        return
    
    # 测试后端
    if not test_backend():
        print("\n❌ 后端测试失败，请检查代码")
        return
    
    print("\n✅ 系统测试通过！")
    print("\n📋 下一步:")
    print("1. 配置 .env 文件中的 DeepSeek API 密钥")
    print("2. 运行 python start_backend.py 启动后端")
    print("3. 运行 python start_frontend.py 启动前端")
    print("4. 访问 http://localhost:8501 使用系统")

if __name__ == "__main__":
    main()
