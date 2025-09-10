"""
文档存储服务
"""
import json
import os
from typing import List, Optional
from datetime import datetime

from ...models.document import Document, DocumentStatus
from ...core.config import settings


class DocumentStorage:
    """文档存储服务"""
    
    def __init__(self):
        self.storage_dir = settings.processed_dir
        os.makedirs(self.storage_dir, exist_ok=True)
    
    async def save_document(self, document: Document) -> bool:
        """保存文档"""
        try:
            file_path = os.path.join(self.storage_dir, f"{document.id}.json")
            
            # 更新修改时间
            document.updated_at = datetime.now()
            
            # 转换为字典并保存
            doc_dict = document.dict()
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(doc_dict, f, ensure_ascii=False, indent=2, default=str)
            
            return True
        except Exception as e:
            print(f"保存文档失败: {e}")
            return False
    
    async def get_document(self, document_id: str) -> Optional[Document]:
        """获取文档"""
        try:
            file_path = os.path.join(self.storage_dir, f"{document_id}.json")
            
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                doc_dict = json.load(f)
            
            return Document(**doc_dict)
        except Exception as e:
            print(f"获取文档失败: {e}")
            return None
    
    async def list_documents(
        self, 
        skip: int = 0, 
        limit: int = 10, 
        status: Optional[DocumentStatus] = None
    ) -> List[Document]:
        """列出文档"""
        try:
            documents = []
            
            # 遍历存储目录
            for filename in os.listdir(self.storage_dir):
                if filename.endswith('.json'):
                    doc_id = filename[:-5]  # 移除.json扩展名
                    document = await self.get_document(doc_id)
                    
                    if document:
                        # 状态过滤
                        if status is None or document.status == status:
                            documents.append(document)
            
            # 按创建时间排序
            documents.sort(key=lambda x: x.created_at, reverse=True)
            
            # 分页
            return documents[skip:skip + limit]
            
        except Exception as e:
            print(f"列出文档失败: {e}")
            return []
    
    async def delete_document(self, document_id: str) -> bool:
        """删除文档"""
        try:
            file_path = os.path.join(self.storage_dir, f"{document_id}.json")
            
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            
            return False
        except Exception as e:
            print(f"删除文档失败: {e}")
            return False
    
    async def update_document_status(self, document_id: str, status: DocumentStatus) -> bool:
        """更新文档状态"""
        try:
            document = await self.get_document(document_id)
            if not document:
                return False
            
            document.status = status
            document.updated_at = datetime.now()
            
            return await self.save_document(document)
        except Exception as e:
            print(f"更新文档状态失败: {e}")
            return False
