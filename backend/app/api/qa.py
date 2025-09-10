"""
问答API
"""
from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Optional, Dict
from pydantic import BaseModel

from ..models.qa import QAResponse, QuestionType
from ..services.qa.qa_service import QAService
from ..services.storage.document_storage import DocumentStorage
from ..services.extractor.knowledge_extractor import KnowledgeExtractor

router = APIRouter(prefix="/qa", tags=["qa"])

# 初始化服务
qa_service = QAService()
storage = DocumentStorage()
knowledge_extractor = KnowledgeExtractor()


class QuestionRequest(BaseModel):
    """问题请求模型"""
    document_id: str
    question: str
    conversation_history: Optional[List[Dict]] = None


class QuestionResponse(BaseModel):
    """问题响应模型"""
    answer: str
    confidence: float
    sources: List[Dict]
    question_type: str
    reasoning: Optional[str]
    follow_up_suggestions: List[str]
    processing_time: float


@router.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """
    提问接口
    """
    try:
        # 获取文档
        document = await storage.get_document(request.document_id)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 检查文档是否已处理完成
        if document.status.value not in ["parsed", "extracted", "completed"]:
            raise HTTPException(
                status_code=400, 
                detail="文档尚未处理完成，请稍后再试"
            )
        
        # 获取知识点（如果存在）
        knowledge = None
        # TODO: 从存储中获取知识点
        
        # 回答问题
        qa_response = await qa_service.answer_question(
            document=document,
            question=request.question,
            knowledge=knowledge,
            conversation_history=request.conversation_history
        )
        
        return QuestionResponse(
            answer=qa_response.answer,
            confidence=qa_response.confidence,
            sources=[source.dict() for source in qa_response.sources],
            question_type=qa_response.question_type.value,
            reasoning=qa_response.reasoning,
            follow_up_suggestions=qa_response.follow_up_suggestions,
            processing_time=qa_response.processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理问题失败: {str(e)}")


@router.get("/search")
async def search_document(
    document_id: str = Query(..., description="文档ID"),
    q: str = Query(..., description="搜索关键词")
):
    """
    文档内检索（返回相关片段）
    """
    try:
        # 获取文档
        document = await storage.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 状态校验
        if document.status.value not in ["parsed", "extracted", "completed"]:
            raise HTTPException(
                status_code=400,
                detail="文档尚未处理完成，请稍后再试"
            )
        
        # 使用QA检索逻辑获取相关片段
        relevant_sections = await qa_service._retrieve_relevant_sections(document, q)
        
        results = []
        for item in relevant_sections:
            section = item["section"]
            results.append({
                "section_id": section.id,
                "title": section.title,
                "text": item["text"],
                "score": float(item["score"]),
            })
        
        return {"document_id": document_id, "query": q, "results": results}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检索失败: {str(e)}")


@router.get("/suggestions/{document_id}")
async def get_question_suggestions(
    document_id: str,
    question_type: Optional[QuestionType] = Query(None)
):
    """
    获取问题建议
    """
    try:
        # 获取文档
        document = await storage.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 生成问题建议
        suggestions = _generate_question_suggestions(document, question_type)
        
        return {
            "document_id": document_id,
            "suggestions": suggestions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取建议失败: {str(e)}")


@router.post("/conversation/{document_id}")
async def start_conversation(
    document_id: str,
    initial_question: str = Body(..., embed=True)
):
    """
    开始对话
    """
    try:
        # 获取文档
        document = await storage.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 回答初始问题
        qa_response = await qa_service.answer_question(
            document=document,
            question=initial_question
        )
        
        return {
            "conversation_id": f"conv_{document_id}_{hash(initial_question)}",
            "initial_question": initial_question,
            "answer": qa_response.answer,
            "confidence": qa_response.confidence,
            "sources": [source.dict() for source in qa_response.sources],
            "follow_up_suggestions": qa_response.follow_up_suggestions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"开始对话失败: {str(e)}")


@router.post("/conversation/{conversation_id}/continue")
async def continue_conversation(
    conversation_id: str,
    question: str = Body(..., embed=True),
    conversation_history: List[Dict] = Body(default=[])
):
    """
    继续对话
    """
    try:
        # 从conversation_id中提取document_id
        if not conversation_id.startswith("conv_"):
            raise HTTPException(status_code=400, detail="无效的对话ID")
        
        parts = conversation_id.split("_")
        if len(parts) < 3:
            raise HTTPException(status_code=400, detail="无效的对话ID格式")
        
        document_id = parts[1]
        
        # 获取文档
        document = await storage.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 继续对话
        qa_response = await qa_service.multi_turn_conversation(
            document=document,
            conversation_history=conversation_history,
            current_question=question
        )
        
        return {
            "conversation_id": conversation_id,
            "question": question,
            "answer": qa_response.answer,
            "confidence": qa_response.confidence,
            "sources": [source.dict() for source in qa_response.sources],
            "follow_up_suggestions": qa_response.follow_up_suggestions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"继续对话失败: {str(e)}")


def _generate_question_suggestions(document, question_type: Optional[QuestionType]) -> List[str]:
    """生成问题建议"""
    suggestions = []
    
    # 基于文档内容生成建议
    if document.metadata:
        if document.metadata.title:
            suggestions.append(f"这篇文献的主要研究内容是什么？")
            suggestions.append(f"《{document.metadata.title}》的核心观点是什么？")
        
        if document.metadata.authors:
            suggestions.append(f"这篇文献的作者有哪些？")
            suggestions.append(f"第一作者的研究背景是什么？")
    
    # 基于章节生成建议
    section_titles = [section.title for section in document.sections]
    
    if any("方法" in title or "Method" in title for title in section_titles):
        suggestions.append("这篇文献使用了什么研究方法？")
        suggestions.append("实验设计有什么特点？")
    
    if any("结果" in title or "Result" in title for title in section_titles):
        suggestions.append("研究的主要结果是什么？")
        suggestions.append("实验结果有什么统计学意义？")
    
    if any("讨论" in title or "Discussion" in title for title in section_titles):
        suggestions.append("作者如何解释研究结果？")
        suggestions.append("这项研究有什么局限性？")
    
    if any("结论" in title or "Conclusion" in title for title in section_titles):
        suggestions.append("研究的主要结论是什么？")
        suggestions.append("对未来研究有什么建议？")
    
    # 根据问题类型过滤
    if question_type:
        if question_type == QuestionType.FACTUAL:
            suggestions = [s for s in suggestions if any(word in s for word in ["是什么", "有哪些", "什么"])]
        elif question_type == QuestionType.LOGICAL:
            suggestions = [s for s in suggestions if any(word in s for word in ["为什么", "如何", "怎么"])]
        elif question_type == QuestionType.ANALYTICAL:
            suggestions = [s for s in suggestions if any(word in s for word in ["分析", "评价", "局限性", "意义"])]
    
    return suggestions[:8]  # 返回8个建议
