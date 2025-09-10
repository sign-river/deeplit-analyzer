"""
文档数据模型
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class DocumentStatus(str, Enum):
    """文档处理状态"""
    UPLOADED = "uploaded"
    PARSING = "parsing"
    PARSED = "parsed"
    EXTRACTING = "extracting"
    EXTRACTED = "extracted"
    INDEXING = "indexing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentType(str, Enum):
    """文档类型"""
    PDF = "pdf"
    WORD = "word"
    LATEX = "latex"
    HTML = "html"
    TEXT = "text"


class Author(BaseModel):
    """作者信息"""
    name: str
    email: Optional[str] = None
    affiliation: Optional[str] = None
    orcid: Optional[str] = None


class Reference(BaseModel):
    """参考文献"""
    id: str
    title: str
    authors: List[str] = []
    journal: Optional[str] = None
    year: Optional[int] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    raw_text: str


class Figure(BaseModel):
    """图表信息"""
    id: str
    caption: str
    type: str  # "figure" or "table"
    content: Optional[str] = None  # 图表内容描述
    page_number: int


class Section(BaseModel):
    """文档章节"""
    id: str
    title: str
    content: str
    level: int = 1
    page_start: Optional[int] = None
    page_end: Optional[int] = None


class DocumentMetadata(BaseModel):
    """文档元数据"""
    title: str
    authors: List[Author] = []
    abstract: Optional[str] = None
    keywords: List[str] = []
    journal: Optional[str] = None
    issn: Optional[str] = None
    impact_factor: Optional[float] = None
    publish_date: Optional[datetime] = None
    pages: Optional[str] = None
    doi: Optional[str] = None
    funding: Optional[str] = None
    language: str = "zh"  # 文档语言


class Document(BaseModel):
    """文档模型"""
    id: str
    filename: str
    file_path: str
    file_size: int
    document_type: DocumentType
    status: DocumentStatus = DocumentStatus.UPLOADED
    
    # 解析结果
    metadata: Optional[DocumentMetadata] = None
    sections: List[Section] = []
    figures: List[Figure] = []
    references: List[Reference] = []
    
    # 处理信息
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    processing_errors: List[str] = []
    
    # 统计信息
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    processing_time: Optional[float] = None


class DocumentChunk(BaseModel):
    """文档分块"""
    id: str
    document_id: str
    section_id: Optional[str] = None
    content: str
    chunk_index: int
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = {}
