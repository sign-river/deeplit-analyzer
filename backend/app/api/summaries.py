"""
总结API
"""
from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Optional, Dict
from pydantic import BaseModel

from ..services.summarizer.summarizer_service import SummarizerService
from ..services.storage.document_storage import DocumentStorage
from ..models.document import Document

router = APIRouter(prefix="/summaries", tags=["summaries"])

# 初始化服务
summarizer = SummarizerService()
storage = DocumentStorage()


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
        
        # 生成总结
        if request.summary_type == "full":
            result = await summarizer.summarize_document(
                document=document,
                summary_type="full"
            )
        elif request.summary_type == "section":
            result = await summarizer.summarize_document(
                document=document,
                summary_type="section"
            )
        elif request.summary_type == "custom":
            if request.keywords:
                result = await summarizer.generate_summary_by_keywords(
                    document=document,
                    keywords=request.keywords,
                )
            elif request.template:
                result = await summarizer.generate_summary_by_template(
                    document=document,
                    template=request.template,
                )
            else:
                result = await summarizer.summarize_document(
                    document=document,
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
        
        # 使用AI智能提取关键词
        keywords = await _extract_smart_keywords(document)
        
        return {
            "document_id": document_id,
            "keywords": keywords[:20],  # 返回前20个关键词
            "total": len(keywords)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取关键词失败: {str(e)}")


async def _extract_smart_keywords(document: Document) -> List[str]:
    """
    智能提取文档关键词
    """
    import re
    
    # 收集所有可用的文本内容
    text_content = []
    
    # 1. 从元数据获取关键词
    keywords_from_meta = []
    if document.metadata:
        if document.metadata.keywords:
            keywords_from_meta.extend(document.metadata.keywords)
        if document.metadata.title:
            text_content.append(document.metadata.title)
        if document.metadata.abstract:
            text_content.append(document.metadata.abstract)
    
    # 2. 从章节内容提取（限制长度避免API调用过大）
    section_content = []
    for section in document.sections[:10]:  # 只处理前10个章节
        # 合并章节标题和内容前500字
        content = f"{section.title}: {section.content[:500]}"
        section_content.append(content)
    
    # 合并所有文本内容
    full_text = "\n".join(text_content + section_content)
    
    # 3. 使用AI提取关键词
    try:
        ai_keywords = await _extract_keywords_with_ai(full_text[:3000])  # 限制文本长度
    except Exception:
        ai_keywords = []
    
    # 4. 规则基础的关键词提取作为补充
    rule_based_keywords = _extract_keywords_by_rules(full_text)
    
    # 5. 合并和过滤关键词
    all_keywords = []
    
    # 优先使用元数据关键词
    all_keywords.extend(keywords_from_meta)
    
    # 添加AI提取的关键词
    all_keywords.extend(ai_keywords)
    
    # 添加规则提取的关键词
    all_keywords.extend(rule_based_keywords)
    
    # 去重和过滤
    filtered_keywords = _filter_and_rank_keywords(all_keywords)
    
    return filtered_keywords


async def _extract_keywords_with_ai(text: str) -> List[str]:
    """
    使用AI提取关键词
    """
    from ..services.summarizer.summarizer_service import SummarizerService
    
    summarizer = SummarizerService()
    
    prompt = f"""
请从以下学术文献内容中提取15-20个最重要的关键词。要求：

1. 关键词必须是学术术语、研究方法、技术名词、重要概念
2. 避免提取：数字、年份、一般性词汇、连接词、介词
3. 优先提取：研究主题、方法名称、技术术语、专业概念、学科词汇
4. 关键词长度在2-8个字符之间
5. 每行一个关键词，不要编号

文献内容：
{text}

请提取关键词：
"""
    
    try:
        result = await summarizer._call_deepseek_api(prompt)
        # 解析AI返回的关键词
        keywords = []
        for line in result.split('\n'):
            keyword = line.strip()
            if keyword and len(keyword) >= 2 and len(keyword) <= 8:
                keywords.append(keyword)
        return keywords[:20]
    except Exception:
        return []


def _extract_keywords_by_rules(text: str) -> List[str]:
    """
    基于规则的关键词提取
    """
    import re
    
    # 常见的学术关键词模式
    academic_patterns = [
        r'[\u4e00-\u9fa5]{2,6}方法',  # 某某方法
        r'[\u4e00-\u9fa5]{2,6}算法',  # 某某算法
        r'[\u4e00-\u9fa5]{2,6}模型',  # 某某模型
        r'[\u4e00-\u9fa5]{2,6}系统',  # 某某系统
        r'[\u4e00-\u9fa5]{2,6}技术',  # 某某技术
        r'[\u4e00-\u9fa5]{2,6}分析',  # 某某分析
        r'[\u4e00-\u9fa5]{2,6}研究',  # 某某研究
        r'[\u4e00-\u9fa5]{2,6}理论',  # 某某理论
        r'[\u4e00-\u9fa5]{2,6}框架',  # 某某框架
        r'[\u4e00-\u9fa5]{2,6}实验',  # 某某实验
    ]
    
    keywords = []
    
    # 提取符合学术模式的词汇
    for pattern in academic_patterns:
        matches = re.findall(pattern, text)
        keywords.extend(matches)
    
    # 提取英文专业术语（大写开头的连续单词）
    english_terms = re.findall(r'\b[A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)*\b', text)
    for term in english_terms:
        if len(term) >= 3 and len(term) <= 20:
            keywords.append(term)
    
    return keywords


def _filter_and_rank_keywords(keywords: List[str]) -> List[str]:
    """
    过滤和排序关键词
    """
    import re
    
    # 停用词列表
    stop_words = {
        # 中文停用词
        '我们', '他们', '可以', '应该', '因为', '所以', '但是', '然而', '因此', '而且', '或者',
        '的', '了', '是', '在', '有', '和', '与', '或', '但', '也', '都', '很', '更', '最',
        '这', '那', '这个', '那个', '这些', '那些', '什么', '怎么', '为什么', '如何',
        '研究', '分析', '方法', '结果', '结论', '讨论', '实验', '数据', '文献', '论文',
        '学者', '作者', '文章', '内容', '问题', '解决', '提出', '发现', '表明', '显示',
        # 英文停用词
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
        'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after',
        'above', 'below', 'between', 'among', 'this', 'that', 'these', 'those',
        'study', 'research', 'analysis', 'method', 'result', 'conclusion', 'discussion',
    }
    
    # 无效模式
    invalid_patterns = [
        r'^\d+$',  # 纯数字
        r'^\d{4}$',  # 年份
        r'^[a-zA-Z]$',  # 单个字母
        r'^[\u4e00-\u9fa5]$',  # 单个汉字
        r'^\W+$',  # 纯符号
    ]
    
    filtered_keywords = []
    seen = set()
    
    for keyword in keywords:
        if not keyword or keyword.lower() in seen:
            continue
            
        # 清理关键词
        cleaned = keyword.strip()
        if not cleaned:
            continue
            
        # 转换为小写用于重复检查
        lower_keyword = cleaned.lower()
        
        # 跳过停用词
        if lower_keyword in stop_words:
            continue
            
        # 跳过无效模式
        if any(re.match(pattern, cleaned) for pattern in invalid_patterns):
            continue
            
        # 长度检查
        if len(cleaned) < 2 or len(cleaned) > 15:
            continue
            
        # 添加到结果
        if lower_keyword not in seen:
            filtered_keywords.append(cleaned)
            seen.add(lower_keyword)
    
    # 按长度和复杂度排序（优先显示更有意义的关键词）
    def keyword_score(kw):
        score = 0
        # 长度适中的得分高
        if 3 <= len(kw) <= 8:
            score += 10
        # 包含专业术语的得分高
        if any(term in kw for term in ['算法', '模型', '系统', '技术', '理论', '框架']):
            score += 5
        # 英文专业术语得分高
        if re.match(r'^[A-Z][a-zA-Z]*$', kw):
            score += 3
        return score
    
    filtered_keywords.sort(key=keyword_score, reverse=True)
    
    return filtered_keywords
