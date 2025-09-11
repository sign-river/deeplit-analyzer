"""
对话历史存储服务
"""
import json
import os
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

from ...models.conversation import Conversation, ConversationEntry, ConversationStatus
from ...core.config import settings


class ConversationStorage:
    """对话历史存储服务"""
    
    def __init__(self):
        self.storage_dir = settings.conversations_dir
        os.makedirs(self.storage_dir, exist_ok=True)
    
    async def save_conversation(self, conversation: Conversation) -> bool:
        """保存对话记录"""
        try:
            file_path = os.path.join(self.storage_dir, f"{conversation.id}.json")
            
            # 更新修改时间
            conversation.updated_at = datetime.now()
            
            # 转换为字典并保存
            conv_dict = conversation.dict()
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(conv_dict, f, ensure_ascii=False, indent=2, default=str)
            
            return True
        except Exception as e:
            print(f"保存对话记录失败: {e}")
            return False
    
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """获取对话记录"""
        try:
            file_path = os.path.join(self.storage_dir, f"{conversation_id}.json")
            
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                conv_dict = json.load(f)
            
            return Conversation(**conv_dict)
        except Exception as e:
            print(f"获取对话记录失败: {e}")
            return None
    
    async def list_conversations(
        self, 
        document_id: Optional[str] = None,
        skip: int = 0, 
        limit: int = 20,
        status: Optional[ConversationStatus] = None
    ) -> List[Conversation]:
        """列出对话记录"""
        try:
            conversations = []
            
            # 遍历存储目录
            for filename in os.listdir(self.storage_dir):
                if filename.endswith('.json'):
                    conv_id = filename[:-5]  # 移除.json扩展名
                    conversation = await self.get_conversation(conv_id)
                    
                    if conversation:
                        # 文档ID过滤
                        if document_id and conversation.document_id != document_id:
                            continue
                        
                        # 状态过滤
                        if status is not None and conversation.status != status:
                            continue
                        
                        conversations.append(conversation)
            
            # 按更新时间排序（最新的在前面）
            conversations.sort(key=lambda x: x.updated_at, reverse=True)
            
            # 分页
            return conversations[skip:skip + limit]
            
        except Exception as e:
            print(f"列出对话记录失败: {e}")
            return []
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """删除对话记录"""
        try:
            file_path = os.path.join(self.storage_dir, f"{conversation_id}.json")
            
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            
            return False
        except Exception as e:
            print(f"删除对话记录失败: {e}")
            return False
    
    async def archive_conversation(self, conversation_id: str) -> bool:
        """归档对话记录"""
        try:
            conversation = await self.get_conversation(conversation_id)
            if not conversation:
                return False
            
            conversation.status = ConversationStatus.ARCHIVED
            return await self.save_conversation(conversation)
        except Exception as e:
            print(f"归档对话记录失败: {e}")
            return False
    
    async def create_conversation(
        self, 
        document_id: str, 
        document_title: str,
        first_question: str = ""
    ) -> Conversation:
        """创建新的对话记录"""
        conversation_id = str(uuid.uuid4())
        now = datetime.now()
        
        conversation = Conversation(
            id=conversation_id,
            document_id=document_id,
            document_title=document_title,
            title=first_question[:50] + ("..." if len(first_question) > 50 else ""),
            created_at=now,
            updated_at=now
        )
        
        return conversation
    
    async def add_qa_to_conversation(
        self, 
        conversation_id: str,
        question: str,
        answer: str,
        confidence: float = 0.0,
        sources: List[Dict[str, Any]] = None,
        processing_time: float = 0.0,
        question_type: Optional[str] = None,
        reasoning: Optional[str] = None
    ) -> bool:
        """向对话记录添加问答"""
        try:
            conversation = await self.get_conversation(conversation_id)
            if not conversation:
                return False
            
            entry = ConversationEntry(
                question=question,
                answer=answer,
                confidence=confidence,
                sources=sources or [],
                timestamp=datetime.now(),
                processing_time=processing_time,
                question_type=question_type,
                reasoning=reasoning
            )
            
            conversation.add_entry(entry)
            return await self.save_conversation(conversation)
            
        except Exception as e:
            print(f"添加问答到对话记录失败: {e}")
            return False
    
    async def get_conversation_by_document(self, document_id: str) -> List[Conversation]:
        """获取某个文档的所有对话记录"""
        return await self.list_conversations(document_id=document_id, limit=100)
    
    async def export_conversation(self, conversation_id: str, format: str = "json") -> Optional[Dict[str, Any]]:
        """导出对话记录"""
        try:
            conversation = await self.get_conversation(conversation_id)
            if not conversation:
                return None
            
            if format == "json":
                return conversation.dict()
            elif format == "markdown":
                return self._export_to_markdown(conversation)
            else:
                return conversation.dict()
                
        except Exception as e:
            print(f"导出对话记录失败: {e}")
            return None
    
    def _export_to_markdown(self, conversation: Conversation) -> Dict[str, str]:
        """导出为Markdown格式"""
        markdown_content = f"# 对话记录: {conversation.title}\n\n"
        markdown_content += f"**文档**: {conversation.document_title}\n"
        markdown_content += f"**创建时间**: {conversation.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        markdown_content += f"**问题总数**: {conversation.total_questions}\n\n"
        markdown_content += "---\n\n"
        
        for i, entry in enumerate(conversation.entries, 1):
            markdown_content += f"## 问题 {i}\n\n"
            markdown_content += f"**时间**: {entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            markdown_content += f"**问题**: {entry.question}\n\n"
            markdown_content += f"**回答**: {entry.answer}\n\n"
            if entry.confidence > 0:
                markdown_content += f"**置信度**: {entry.confidence:.2f}\n\n"
            if entry.processing_time > 0:
                markdown_content += f"**处理时间**: {entry.processing_time:.2f}秒\n\n"
            markdown_content += "---\n\n"
        
        return {"content": markdown_content, "filename": f"conversation_{conversation.id}.md"}


# 创建全局实例
conversation_storage = ConversationStorage()
