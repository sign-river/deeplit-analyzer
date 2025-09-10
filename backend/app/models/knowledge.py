"""
知识点数据模型
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class KnowledgeType(str, Enum):
    """知识点类型"""
    CORE_POINT = "core_point"  # 核心观点
    METHOD = "method"  # 研究方法
    RESULT = "result"  # 实验结果
    LIMITATION = "limitation"  # 研究局限
    FUTURE_WORK = "future_work"  # 未来展望
    KEYWORD = "keyword"  # 关键词


class ConfidenceLevel(str, Enum):
    """置信度等级"""
    HIGH = "high"  # 高置信度
    MEDIUM = "medium"  # 中等置信度
    LOW = "low"  # 低置信度


class CorePoint(BaseModel):
    """核心观点"""
    id: str
    content: str
    source_section: str
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    supporting_evidence: List[str] = []
    related_concepts: List[str] = []


class ResearchMethod(BaseModel):
    """研究方法"""
    id: str
    method_type: str  # 如：随机对照试验、问卷调查等
    core_steps: List[str] = []
    key_parameters: Dict[str, Any] = {}
    materials: List[str] = []
    tools: List[str] = []
    platform: Optional[str] = None
    source_section: str
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


class ExperimentalResult(BaseModel):
    """实验结果"""
    id: str
    metric_name: str
    value: str
    unit: Optional[str] = None
    statistical_significance: Optional[str] = None
    comparison_group: Optional[str] = None
    source_section: str
    related_figure: Optional[str] = None
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


class ResearchLimitation(BaseModel):
    """研究局限"""
    id: str
    limitation_type: str  # 如：样本量、方法局限等
    description: str
    impact: Optional[str] = None
    source_section: str
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


class FutureWork(BaseModel):
    """未来展望"""
    id: str
    direction: str
    description: str
    priority: Optional[str] = None  # 如：高、中、低
    source_section: str
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


class KeywordTree(BaseModel):
    """关键词树"""
    core_keyword: str
    related_keywords: List[str] = []
    frequency: int = 0
    importance_score: float = 0.0


class KnowledgeExtraction(BaseModel):
    """知识点提取结果"""
    document_id: str
    core_points: List[CorePoint] = []
    methods: List[ResearchMethod] = []
    results: List[ExperimentalResult] = []
    limitations: List[ResearchLimitation] = []
    future_work: List[FutureWork] = []
    keyword_trees: List[KeywordTree] = []
    
    # 提取统计
    extraction_accuracy: Optional[float] = None
    redundancy_ratio: Optional[float] = None
    processing_time: Optional[float] = None
    
    # 学科适配
    discipline: Optional[str] = None  # 如：医学、计算机、生物学等
    extraction_rules: Dict[str, Any] = {}
