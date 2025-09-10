#!/usr/bin/env python3
"""
简化版 deeplit-analyzer 应用
使用已安装的依赖运行基本功能
"""
import os
import json
from datetime import datetime
from typing import Dict, List, Optional

# 尝试导入FastAPI
try:
    from fastapi import FastAPI, UploadFile, File, Form, HTTPException
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    print("⚠️ FastAPI 不可用，将使用简化模式")

# 尝试导入Streamlit
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    print("⚠️ Streamlit 不可用，将使用简化模式")

class DocumentInfo:
    """文档信息类"""
    def __init__(self, filename: str, content: str = ""):
        self.id = f"doc_{hash(filename)}"
        self.filename = filename
        self.content = content
        self.created_at = datetime.now()
        self.status = "uploaded"

class SimpleScholarMind:
    """简化版 deeplit-analyzer"""
    
    def __init__(self):
        self.documents = {}
        self.data_dir = "./data"
        os.makedirs(self.data_dir, exist_ok=True)
    
    def upload_document(self, filename: str, content: str) -> str:
        """上传文档"""
        doc = DocumentInfo(filename, content)
        self.documents[doc.id] = doc
        
        # 保存到文件
        doc_path = os.path.join(self.data_dir, f"{doc.id}.json")
        with open(doc_path, 'w', encoding='utf-8') as f:
            json.dump({
                'id': doc.id,
                'filename': doc.filename,
                'content': doc.content,
                'created_at': doc.created_at.isoformat(),
                'status': doc.status
            }, f, ensure_ascii=False, indent=2)
        
        return doc.id
    
    def get_document(self, doc_id: str) -> Optional[DocumentInfo]:
        """获取文档"""
        return self.documents.get(doc_id)
    
    def list_documents(self) -> List[Dict]:
        """列出文档"""
        return [
            {
                'id': doc.id,
                'filename': doc.filename,
                'status': doc.status,
                'created_at': doc.created_at.isoformat()
            }
            for doc in self.documents.values()
        ]
    
    def generate_summary(self, doc_id: str) -> str:
        """生成简单总结"""
        doc = self.get_document(doc_id)
        if not doc:
            return "文档不存在"
        
        content = doc.content
        if len(content) > 500:
            summary = content[:500] + "..."
        else:
            summary = content
        
        return f"文档总结：\n{summary}"
    
    def answer_question(self, doc_id: str, question: str) -> str:
        """简单问答"""
        doc = self.get_document(doc_id)
        if not doc:
            return "文档不存在"
        
        # 简单的关键词匹配
        content = doc.content.lower()
        question_lower = question.lower()
        
        if any(word in content for word in question_lower.split()):
            return f"根据文档内容，找到了相关信息。问题：{question}\n文档内容片段：{content[:200]}..."
        else:
            return f"抱歉，在文档中没有找到与问题'{question}'相关的信息。"

def create_fastapi_app():
    """创建FastAPI应用"""
    if not FASTAPI_AVAILABLE:
        return None
    
    app = FastAPI(title="deeplit-analyzer - 简化版")
    scholar_mind = SimpleScholarMind()
    
    @app.get("/")
    async def root():
        return {"message": "deeplit-analyzer - 简化版", "status": "running"}
    
    @app.get("/health")
    async def health():
        return {"status": "healthy"}
    
    @app.post("/documents/upload")
    async def upload_document(
        filename: str = Form(...),
        content: str = Form(...)
    ):
        doc_id = scholar_mind.upload_document(filename, content)
        return {"message": "文档上传成功", "document_id": doc_id}
    
    @app.get("/documents/")
    async def list_documents():
        return {"documents": scholar_mind.list_documents()}
    
    @app.get("/documents/{doc_id}")
    async def get_document(doc_id: str):
        doc = scholar_mind.get_document(doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="文档不存在")
        return {
            "id": doc.id,
            "filename": doc.filename,
            "content": doc.content,
            "status": doc.status,
            "created_at": doc.created_at.isoformat()
        }
    
    @app.get("/summaries/{doc_id}")
    async def get_summary(doc_id: str):
        summary = scholar_mind.generate_summary(doc_id)
        return {"summary": summary}
    
    @app.post("/qa/ask")
    async def ask_question(doc_id: str = Form(...), question: str = Form(...)):
        answer = scholar_mind.answer_question(doc_id, question)
        return {"answer": answer}
    
    return app

def create_streamlit_app():
    """创建Streamlit应用"""
    if not STREAMLIT_AVAILABLE:
        return None
    
    st.set_page_config(
        page_title="deeplit-analyzer - 简化版",
        page_icon="📚",
        layout="wide"
    )
    
    st.title("📚 deeplit-analyzer - 简化版")
    st.markdown("学术文献处理AI系统（简化版）")
    
    scholar_mind = SimpleScholarMind()
    
    # 文档上传
    st.header("📤 文档上传")
    
    filename = st.text_input("文件名", placeholder="例如：研究论文.pdf")
    content = st.text_area("文档内容", placeholder="粘贴文档内容...", height=200)
    
    if st.button("上传文档"):
        if filename and content:
            doc_id = scholar_mind.upload_document(filename, content)
            st.success(f"✅ 文档上传成功！ID: {doc_id}")
        else:
            st.warning("请输入文件名和内容")
    
    # 文档列表
    st.header("📋 文档列表")
    
    documents = scholar_mind.list_documents()
    if documents:
        for doc in documents:
            with st.expander(f"📄 {doc['filename']}"):
                st.write(f"**ID**: {doc['id']}")
                st.write(f"**状态**: {doc['status']}")
                st.write(f"**上传时间**: {doc['created_at']}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button(f"📝 生成总结", key=f"summary_{doc['id']}"):
                        summary = scholar_mind.generate_summary(doc['id'])
                        st.text_area("总结", summary, height=150)
                
                with col2:
                    question = st.text_input("问题", key=f"question_{doc['id']}")
                    if st.button(f"💬 提问", key=f"ask_{doc['id']}"):
                        if question:
                            answer = scholar_mind.answer_question(doc['id'], question)
                            st.text_area("回答", answer, height=150)
                        else:
                            st.warning("请输入问题")
    else:
        st.info("📭 暂无文档")
    
    # 使用说明
    st.header("📖 使用说明")
    st.markdown("""
    这是一个简化版的deeplit-analyzer系统，包含以下功能：
    
    1. **文档上传**: 输入文件名和内容
    2. **文档管理**: 查看已上传的文档
    3. **简单总结**: 生成文档的基本总结
    4. **简单问答**: 基于关键词匹配的问答
    
    ⚠️ 注意：这是简化版本，完整功能需要安装所有依赖。
    """)

def main():
    """主函数"""
    print("🚀 deeplit-analyzer - 简化版")
    print("=" * 50)
    
    if FASTAPI_AVAILABLE and STREAMLIT_AVAILABLE:
        print("✅ 检测到完整依赖，可以选择运行模式：")
        print("1. 后端API服务 (FastAPI)")
        print("2. 前端界面 (Streamlit)")
        print("3. 退出")
        
        choice = input("请选择 (1/2/3): ").strip()
        
        if choice == "1":
            print("🚀 启动后端API服务...")
            app = create_fastapi_app()
            if app:
                import uvicorn
                uvicorn.run(app, host="0.0.0.0", port=8000)
        
        elif choice == "2":
            print("🚀 启动前端界面...")
            create_streamlit_app()
        
        elif choice == "3":
            print("👋 再见！")
        
        else:
            print("❌ 无效选择")
    
    elif FASTAPI_AVAILABLE:
        print("✅ 检测到FastAPI，启动后端服务...")
        app = create_fastapi_app()
        if app:
            try:
                import uvicorn
                uvicorn.run(app, host="0.0.0.0", port=8000)
            except ImportError:
                print("❌ Uvicorn 未安装，无法启动服务")
    
    elif STREAMLIT_AVAILABLE:
        print("✅ 检测到Streamlit，启动前端界面...")
        create_streamlit_app()
    
    else:
        print("❌ 未检测到可用依赖")
        print("请安装 FastAPI 或 Streamlit 来运行系统")

if __name__ == "__main__":
    main()
