"""
问答API
"""
from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Optional, Dict
from pydantic import BaseModel
from collections import defaultdict, deque
import time

from ..models.qa import QAResponse, QuestionType
from ..services.qa.qa_service import QAService
from ..services.storage.document_storage import DocumentStorage
from ..services.storage.conversation_storage import conversation_storage

router = APIRouter(prefix="/qa", tags=["qa"])

# 初始化服务
qa_service = QAService()
storage = DocumentStorage()

# 对话历史管理器（内存存储，生产环境可考虑使用Redis）
class ConversationManager:
    def __init__(self, max_history_per_doc=10, max_age_hours=24):
        self.conversations = defaultdict(lambda: deque(maxlen=max_history_per_doc))
        self.last_access = defaultdict(float)
        self.max_age_hours = max_age_hours
    
    def add_conversation(self, document_id: str, question: str, answer: str):
        """添加对话记录"""
        current_time = time.time()
        self.conversations[document_id].append({
            "question": question,
            "answer": answer,
            "timestamp": current_time
        })
        self.last_access[document_id] = current_time
        self._cleanup_old_conversations()
    
    def get_conversation_history(self, document_id: str) -> List[Dict]:
        """获取对话历史"""
        self._cleanup_old_conversations()
        current_time = time.time()
        self.last_access[document_id] = current_time
        
        # 返回历史记录，按时间顺序
        history = list(self.conversations[document_id])
        return history
    
    def clear_conversation(self, document_id: str):
        """清空特定文档的对话历史"""
        if document_id in self.conversations:
            self.conversations[document_id].clear()
        if document_id in self.last_access:
            del self.last_access[document_id]
    
    def _cleanup_old_conversations(self):
        """清理过期的对话历史"""
        current_time = time.time()
        max_age_seconds = self.max_age_hours * 3600
        
        expired_docs = []
        for doc_id, last_time in self.last_access.items():
            if current_time - last_time > max_age_seconds:
                expired_docs.append(doc_id)
        
        for doc_id in expired_docs:
            if doc_id in self.conversations:
                del self.conversations[doc_id]
            del self.last_access[doc_id]

# 全局对话管理器实例
conversation_manager = ConversationManager()


class QuestionRequest(BaseModel):
    """问题请求模型"""
    document_id: str
    question: str
    conversation_id: Optional[str] = None  # 可选的对话ID，用于延续已有对话


class QuestionResponse(BaseModel):
    """问题响应模型"""
    answer: str
    confidence: float
    sources: List[Dict]
    question_type: str
    reasoning: Optional[str]
    follow_up_suggestions: List[str]
    processing_time: float
    conversation_id: str  # 返回对话ID


@router.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """
    提问接口（支持持久化对话历史）
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
        
        # 获取或创建对话记录
        conversation = None
        if request.conversation_id:
            # 延续已有对话
            conversation = await conversation_storage.get_conversation(request.conversation_id)
            if not conversation:
                raise HTTPException(status_code=404, detail="对话记录不存在")
        else:
            # 创建新对话
            conversation = await conversation_storage.create_conversation(
                document_id=request.document_id,
                document_title=document.metadata.title if document.metadata else "未知文档",
                first_question=request.question
            )
            await conversation_storage.save_conversation(conversation)
        
        # 获取对话历史（转换为QA服务需要的格式）
        conversation_history = conversation.to_history_format()
        
        # 回答问题
        qa_response = await qa_service.answer_question(
            document=document,
            question=request.question,
            conversation_history=conversation_history
        )
        
        # 保存问答到对话记录
        await conversation_storage.add_qa_to_conversation(
            conversation_id=conversation.id,
            question=request.question,
            answer=qa_response.answer,
            confidence=qa_response.confidence,
            sources=[source.dict() for source in qa_response.sources],
            processing_time=qa_response.processing_time,
            question_type=qa_response.question_type.value,
            reasoning=qa_response.reasoning
        )
        
        # 同时保存到内存管理器（向后兼容）
        conversation_manager.add_conversation(
            document_id=request.document_id,
            question=request.question,
            answer=qa_response.answer
        )
        
        return QuestionResponse(
            answer=qa_response.answer,
            confidence=qa_response.confidence,
            sources=[source.dict() for source in qa_response.sources],
            question_type=qa_response.question_type.value,
            reasoning=qa_response.reasoning,
            follow_up_suggestions=qa_response.follow_up_suggestions,
            processing_time=qa_response.processing_time,
            conversation_id=conversation.id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理问题失败: {str(e)}")


@router.get("/conversations/{document_id}")
async def get_conversations_by_document(document_id: str, skip: int = 0, limit: int = 20):
    """
    获取文档的所有对话记录列表
    """
    try:
        # 检查文档是否存在
        document = await storage.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        conversations = await conversation_storage.list_conversations(
            document_id=document_id,
            skip=skip,
            limit=limit
        )
        
        # 转换为简化格式
        conversation_list = []
        for conv in conversations:
            conversation_list.append({
                "id": conv.id,
                "title": conv.title,
                "total_questions": conv.total_questions,
                "created_at": conv.created_at.isoformat(),
                "updated_at": conv.updated_at.isoformat(),
                "status": conv.status.value
            })
        
        return {
            "document_id": document_id,
            "conversations": conversation_list,
            "total": len(conversation_list)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取对话列表失败: {str(e)}")


@router.get("/conversation/{conversation_id}/detail")
async def get_conversation_detail(conversation_id: str):
    """
    获取对话详细内容
    """
    try:
        conversation = await conversation_storage.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="对话记录不存在")
        
        return conversation.dict()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取对话详细内容失败: {str(e)}")


@router.delete("/conversation/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """
    删除对话记录
    """
    try:
        success = await conversation_storage.delete_conversation(conversation_id)
        if not success:
            raise HTTPException(status_code=404, detail="对话记录不存在")
        
        return {"message": "对话记录已删除", "conversation_id": conversation_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除对话记录失败: {str(e)}")


@router.post("/conversation/{conversation_id}/archive")
async def archive_conversation(conversation_id: str):
    """
    归档对话记录
    """
    try:
        success = await conversation_storage.archive_conversation(conversation_id)
        if not success:
            raise HTTPException(status_code=404, detail="对话记录不存在")
        
        return {"message": "对话记录已归档", "conversation_id": conversation_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"归档对话记录失败: {str(e)}")


@router.get("/conversation/{conversation_id}/export")
async def export_conversation(conversation_id: str, format: str = Query("json", regex="^(json|markdown)$")):
    """
    导出对话记录
    """
    try:
        export_data = await conversation_storage.export_conversation(conversation_id, format)
        if not export_data:
            raise HTTPException(status_code=404, detail="对话记录不存在")
        
        return export_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出对话记录失败: {str(e)}")


@router.get("/conversation/{document_id}")
async def get_conversation_history(document_id: str):
    """
    获取文档的对话历史
    """
    try:
        # 检查文档是否存在
        document = await storage.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        history = conversation_manager.get_conversation_history(document_id)
        
        return {
            "document_id": document_id,
            "conversation_history": history,
            "total_conversations": len(history)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取对话历史失败: {str(e)}")


@router.delete("/conversation/{document_id}")
async def clear_conversation_history(document_id: str):
    """
    清空文档的对话历史
    """
    try:
        # 检查文档是否存在
        document = await storage.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        conversation_manager.clear_conversation(document_id)
        
        return {
            "message": "对话历史已清空",
            "document_id": document_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清空对话历史失败: {str(e)}")


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
