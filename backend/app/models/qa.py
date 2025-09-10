"""
问答系统数据模型
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class QuestionType(str, Enum):
    """问题类型"""
    FACTUAL = "factual"  # 事实类问题
    LOGICAL = "logical"  # 逻辑类问题
    ANALYTICAL = "analytical"  # 深度分析类问题


class AnswerSource(BaseModel):
    """答案来源"""
    source_type: str  # 如：metadata、section、figure等
    source_id: str
    source_text: str
    confidence: float
    page_number: Optional[int] = None


class Question(BaseModel):
    """问题模型"""
    id: str
    document_id: str
    question_text: str
    question_type: QuestionType
    context: Optional[str] = None  # 上下文信息
    created_at: datetime = Field(default_factory=datetime.now)


class Answer(BaseModel):
    """答案模型"""
    id: str
    question_id: str
    answer_text: str
    confidence: float
    sources: List[AnswerSource] = []
    reasoning_chain: Optional[str] = None  # 推理链条
    created_at: datetime = Field(default_factory=datetime.now)


class Conversation(BaseModel):
    """对话模型"""
    id: str
    document_id: str
    questions: List[Question] = []
    answers: List[Answer] = []
    context_history: List[str] = []  # 上下文历史
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class QAResponse(BaseModel):
    """问答响应"""
    answer: str
    confidence: float
    sources: List[AnswerSource] = []
    question_type: QuestionType
    reasoning: Optional[str] = None
    follow_up_suggestions: List[str] = []
    processing_time: float
