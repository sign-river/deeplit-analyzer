"""
对话历史模型
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ConversationStatus(str, Enum):
    """对话状态"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ConversationEntry(BaseModel):
    """单条对话记录"""
    question: str
    answer: str
    confidence: float
    sources: List[Dict[str, Any]] = []
    timestamp: datetime
    processing_time: float = 0.0
    question_type: Optional[str] = None
    reasoning: Optional[str] = None


class Conversation(BaseModel):
    """完整对话记录"""
    id: str
    document_id: str
    document_title: str
    title: str  # 对话标题（根据第一个问题生成）
    entries: List[ConversationEntry] = []
    status: ConversationStatus = ConversationStatus.ACTIVE
    created_at: datetime
    updated_at: datetime
    total_questions: int = 0
    
    def add_entry(self, entry: ConversationEntry):
        """添加对话条目"""
        self.entries.append(entry)
        self.total_questions += 1
        self.updated_at = datetime.now()
        
        # 如果是第一个问题，生成对话标题
        if self.total_questions == 1:
            self.title = self._generate_title(entry.question)
    
    def _generate_title(self, first_question: str) -> str:
        """根据第一个问题生成对话标题"""
        # 简单的标题生成逻辑
        title = first_question[:50]
        if len(first_question) > 50:
            title += "..."
        return title
    
    def to_history_format(self) -> List[Dict[str, str]]:
        """转换为历史对话格式"""
        history = []
        for entry in self.entries:
            history.append({
                "question": entry.question,
                "answer": entry.answer,
                "timestamp": entry.timestamp.isoformat()
            })
        return history
