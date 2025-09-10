"""
总结API
"""
from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Optional, Dict
from pydantic import BaseModel

from ..services.summarizer.summarizer_service import SummarizerService
from ..services.storage.document_storage import DocumentStorage
from ..services.extractor.knowledge_extractor import KnowledgeExtractor

router = APIRouter(prefix="/summaries", tags=["summaries"])

# 初始化服务
summarizer = SummarizerService()
storage = DocumentStorage()
knowledge_extractor = KnowledgeExtractor()


class SummaryRequest(BaseModel):
    """总结请求模型"""
    document_id: str
    summary_type: str = "full"  # full, section, custom
    keywords: Optional[List[str]] = None
    template: Optional[str] = None


@router.post("/generate", response_model=Dict)
async def generate_summary(request: SummaryRequest):
    """
    生成文档总结
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
        
        # 生成总结
        if request.summary_type == "full":
            result = await summarizer.summarize_document(
                document=document,
                knowledge=knowledge,
                summary_type="full"
            )
        elif request.summary_type == "section":
            result = await summarizer.summarize_document(
                document=document,
                knowledge=knowledge,
                summary_type="section"
            )
        elif request.summary_type == "custom":
            if request.keywords:
                result = await summarizer.generate_summary_by_keywords(
                    document=document,
                    keywords=request.keywords,
                    knowledge=knowledge
                )
            elif request.template:
                result = await summarizer.generate_summary_by_template(
                    document=document,
                    template=request.template,
                    knowledge=knowledge
                )
            else:
                result = await summarizer.summarize_document(
                    document=document,
                    knowledge=knowledge,
                    summary_type="custom"
                )
        else:
            raise HTTPException(status_code=400, detail="不支持的总结类型")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成总结失败: {str(e)}")


@router.get("/full/{document_id}")
async def get_full_summary(document_id: str):
    """
    获取全文献概括总结
    """
    try:
        # 获取文档
        document = await storage.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 生成总结
        result = await summarizer.summarize_document(
            document=document,
            summary_type="full"
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成总结失败: {str(e)}")


@router.get("/section/{document_id}")
async def get_section_summary(
    document_id: str,
    section_name: Optional[str] = Query(None, description="章节名称，如：方法、结果、讨论")
):
    """
    获取章节聚焦总结
    """
    try:
        # 获取文档
        document = await storage.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 生成总结
        result = await summarizer.summarize_document(
            document=document,
            summary_type="section"
        )
        
        # 如果指定了章节名称，只返回该章节的总结
        if section_name and "summaries" in result:
            section_summaries = result["summaries"]
            if section_name in section_summaries:
                return {
                    "section_name": section_name,
                    "summary": section_summaries[section_name],
                    "metadata": result["metadata"]
                }
            else:
                # 查找包含关键词的章节
                matching_sections = []
                for title, summary in section_summaries.items():
                    if section_name in title:
                        matching_sections.append({"title": title, "summary": summary})
                
                if matching_sections:
                    return {
                        "section_name": section_name,
                        "matching_sections": matching_sections,
                        "metadata": result["metadata"]
                    }
                else:
                    raise HTTPException(status_code=404, detail=f"未找到章节: {section_name}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成总结失败: {str(e)}")


@router.post("/custom/{document_id}")
async def get_custom_summary(
    document_id: str,
    keywords: Optional[List[str]] = Body(None, description="关键词列表"),
    template: Optional[str] = Body(None, description="总结模板，如：问题-方法-结论"),
    detail_level: str = Body("brief", description="详细程度：brief, detailed")
):
    """
    获取定制化总结
    """
    try:
        # 获取文档
        document = await storage.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 生成总结
        if keywords:
            result = await summarizer.generate_summary_by_keywords(
                document=document,
                keywords=keywords
            )
        elif template:
            result = await summarizer.generate_summary_by_template(
                document=document,
                template=template
            )
        else:
            result = await summarizer.summarize_document(
                document=document,
                summary_type="custom"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成总结失败: {str(e)}")


@router.get("/templates")
async def get_summary_templates():
    """
    获取可用的总结模板
    """
    templates = [
        {
            "id": "problem_method_conclusion",
            "name": "问题-方法-结论",
            "description": "按照研究问题、研究方法、研究结论的结构组织总结"
        },
        {
            "id": "background_method_result",
            "name": "背景-方法-结果",
            "description": "按照研究背景、研究方法、研究结果的结构组织总结"
        },
        {
            "id": "objective_method_finding",
            "name": "目标-方法-发现",
            "description": "按照研究目标、研究方法、主要发现的结构组织总结"
        },
        {
            "id": "limitation_future",
            "name": "局限-展望",
            "description": "重点关注研究局限和未来研究方向"
        },
        {
            "id": "contribution_impact",
            "name": "贡献-影响",
            "description": "重点关注研究贡献和学术影响"
        }
    ]
    
    return {
        "templates": templates,
        "total": len(templates)
    }


@router.get("/keywords/{document_id}")
async def get_document_keywords(document_id: str):
    """
    获取文档关键词建议
    """
    try:
        # 获取文档
        document = await storage.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 提取关键词
        keywords = []
        
        # 从元数据获取关键词
        if document.metadata and document.metadata.keywords:
            keywords.extend(document.metadata.keywords)
        
        # 从章节标题提取关键词
        section_keywords = []
        for section in document.sections:
            title_words = section.title.split()
            section_keywords.extend([word for word in title_words if len(word) > 1])
        
        # 去重并排序
        all_keywords = list(set(keywords + section_keywords))
        all_keywords.sort()
        
        return {
            "document_id": document_id,
            "keywords": all_keywords[:20],  # 返回前20个关键词
            "total": len(all_keywords)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取关键词失败: {str(e)}")
