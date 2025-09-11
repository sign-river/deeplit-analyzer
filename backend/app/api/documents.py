"""
文档管理API
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
import uuid
import os
from datetime import datetime

from ..models.document import Document, DocumentStatus, DocumentType
from ..services.parser.document_parser import DocumentParser
from ..services.storage.document_storage import DocumentStorage
from ..core.config import settings

router = APIRouter(prefix="/documents", tags=["documents"])

# 初始化服务
parser = DocumentParser()
storage = DocumentStorage()


@router.post("/upload", response_model=dict)
async def upload_documents(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...)
):
    """
    上传文档文件
    支持多文件上传和批量处理
    """
    try:
        if len(files) > settings.max_batch_size:
            raise HTTPException(
                400,
                f"批量上传文件数量不能超过 {settings.max_batch_size} 个"
            )
        
        uploaded_docs = []
        
        for file in files:
            # 验证文件类型
            if not _is_supported_file_type(file.filename):
                raise HTTPException(
                    400,
                    f"不支持的文件类型: {file.filename}"
                )
            
            # 生成文档ID
            doc_id = str(uuid.uuid4())
            
            # 保存文件
            file_path = await _save_uploaded_file(file, doc_id)
            
            # 创建文档记录
            document = Document(
                id=doc_id,
                filename=file.filename,
                file_path=file_path,
                file_size=file.size or 0,
                document_type=_get_document_type(file.filename),
                status=DocumentStatus.UPLOADED
            )
            
            # 保存到存储
            await storage.save_document(document)
            
            # 添加到后台处理任务
            background_tasks.add_task(process_document, doc_id)
            
            uploaded_docs.append({
                "id": doc_id,
                "filename": file.filename,
                "status": document.status.value
            })
        
        return {
            "message": f"成功上传 {len(files)} 个文件",
            "documents": uploaded_docs
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"文档上传错误: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"文档上传失败: {str(e)}")


@router.get("/", response_model=List[dict])
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status: Optional[DocumentStatus] = Query(None)
):
    """
    获取文档列表
    """
    documents = await storage.list_documents(skip=skip, limit=limit, status=status)
    
    return [
        {
            "id": doc.id,
            "filename": doc.filename,
            "status": doc.status.value,
            "created_at": doc.created_at.isoformat(),
            "page_count": doc.page_count,
            "word_count": doc.word_count
        }
        for doc in documents
    ]


@router.get("/{document_id}", response_model=dict)
async def get_document(document_id: str):
    """
    获取文档详情
    """
    document = await storage.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    return {
        "id": document.id,
        "filename": document.filename,
        "status": document.status.value,
        "metadata": document.metadata.dict() if document.metadata else None,
        "sections": [section.dict() for section in document.sections],
        "figures": [figure.dict() for figure in document.figures],
        "references": [ref.dict() for ref in document.references],
        "created_at": document.created_at.isoformat(),
        "updated_at": document.updated_at.isoformat(),
        "processing_errors": document.processing_errors
    }


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """
    删除文档
    """
    try:
        # 首先检查文档是否存在
        document = await storage.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在或已被删除")
        
        success = await storage.delete_document(document_id)
        if not success:
            raise HTTPException(status_code=500, detail="文档删除失败，请稍后重试")
        
        return {"message": "文档删除成功", "document_id": document_id}
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"删除文档错误: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"删除文档时发生错误: {str(e)}")


@router.post("/{document_id}/reprocess")
async def reprocess_document(
    background_tasks: BackgroundTasks,
    document_id: str
):
    """
    重新处理文档
    """
    document = await storage.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 重置状态
    document.status = DocumentStatus.UPLOADED
    document.processing_errors = []
    await storage.save_document(document)
    
    # 重新处理
    background_tasks.add_task(process_document, document_id)
    
    return {"message": "文档重新处理已开始"}


async def process_document(document_id: str):
    """
    处理文档的后台任务
    """
    try:
        # 获取文档
        document = await storage.get_document(document_id)
        if not document:
            return
        
        # 更新状态为解析中
        document.status = DocumentStatus.PARSING
        await storage.save_document(document)
        
        # 解析文档
        parsed_doc = await parser.parse_document(document)
        
        # 更新状态为已解析
        parsed_doc.status = DocumentStatus.PARSED
        await storage.save_document(parsed_doc)
        
        # TODO: 添加知识点提取和索引构建
        
    except Exception as e:
        # 更新错误状态
        document = await storage.get_document(document_id)
        if document:
            document.status = DocumentStatus.FAILED
            document.processing_errors.append(str(e))
            await storage.save_document(document)


def _is_supported_file_type(filename: str) -> bool:
    """检查是否为支持的文件类型"""
    supported_extensions = {'.pdf', '.doc', '.docx', '.tex', '.html', '.txt'}
    ext = os.path.splitext(filename.lower())[1]
    return ext in supported_extensions


def _get_document_type(filename: str) -> DocumentType:
    """根据文件名获取文档类型"""
    ext = os.path.splitext(filename.lower())[1]
    type_mapping = {
        '.pdf': DocumentType.PDF,
        '.doc': DocumentType.WORD,
        '.docx': DocumentType.WORD,
        '.tex': DocumentType.LATEX,
        '.html': DocumentType.HTML,
        '.txt': DocumentType.TEXT
    }
    return type_mapping.get(ext, DocumentType.TEXT)


async def _save_uploaded_file(file: UploadFile, doc_id: str) -> str:
    """保存上传的文件"""
    file_ext = os.path.splitext(file.filename)[1]
    file_path = os.path.join(settings.upload_dir, f"{doc_id}{file_ext}")
    
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    return file_path
