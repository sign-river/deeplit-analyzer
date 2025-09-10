"""
文献总结服务
"""
import aiohttp
from typing import List, Dict, Optional
from datetime import datetime

from ...models.document import Document
from ...models.knowledge import KnowledgeExtraction
from ...core.config import settings


class SummarizerService:
    """文献总结服务"""
    
    def __init__(self):
        self.api_key = settings.deepseek_api_key
        self.base_url = settings.deepseek_base_url
        self.model = "deepseek-chat"
    
    async def summarize_document(
        self, 
        document: Document, 
        knowledge: Optional[KnowledgeExtraction] = None,
        summary_type: str = "full"
    ) -> Dict:
        """
        生成文档总结
        """
        try:
            if summary_type == "full":
                return await self._generate_full_summary(document, knowledge)
            elif summary_type == "section":
                return await self._generate_section_summary(document, knowledge)
            elif summary_type == "custom":
                return await self._generate_custom_summary(document, knowledge)
            else:
                raise ValueError(f"不支持的总结类型: {summary_type}")
                
        except Exception as e:
            return {
                "error": f"总结生成失败: {str(e)}",
                "summary": "",
                "metadata": {}
            }
    
    async def _generate_full_summary(self, document: Document, knowledge: Optional[KnowledgeExtraction]) -> Dict:
        """生成全文献概括总结"""
        # 构建文档内容
        content = self._build_document_content(document, knowledge)
        
        # 生成总结提示
        prompt = f"""
请为以下学术文献生成一个简洁的概括总结，要求：

1. 包含核心要素：文献主题、研究目的、核心方法、关键结果、主要结论、研究意义
2. 按"目的→方法→结果→结论"的学术逻辑组织内容
3. 中文总结控制在500字以内
4. 使用简洁、规范的学术语言
5. 开头标注文献标题、作者、发表期刊

文献内容：
{content}

请生成总结：
"""
        
        summary = await self._call_deepseek_api(prompt)
        
        return {
            "type": "full_summary",
            "summary": summary,
            "metadata": {
                "document_id": document.id,
                "title": document.metadata.title if document.metadata else "未知标题",
                "authors": [author.name for author in document.metadata.authors] if document.metadata else [],
                "journal": document.metadata.journal if document.metadata else None,
                "word_count": len(summary.split()),
                "generated_at": datetime.now().isoformat()
            }
        }
    
    async def _generate_section_summary(self, document: Document, knowledge: Optional[KnowledgeExtraction]) -> Dict:
        """生成章节聚焦总结"""
        summaries = {}
        
        # 为每个主要章节生成总结
        main_sections = ["摘要", "引言", "方法", "结果", "讨论", "结论"]
        
        for section in document.sections:
            if any(keyword in section.title for keyword in main_sections):
                section_summary = await self._summarize_single_section(section, knowledge)
                summaries[section.title] = section_summary
        
        return {
            "type": "section_summary",
            "summaries": summaries,
            "metadata": {
                "document_id": document.id,
                "sections_count": len(summaries),
                "generated_at": datetime.now().isoformat()
            }
        }
    
    async def _generate_custom_summary(self, document: Document, knowledge: Optional[KnowledgeExtraction]) -> Dict:
        """生成定制化总结"""
        # 这里可以根据用户需求生成不同类型的总结
        # 例如：仅总结研究局限与未来方向、按特定结构总结等
        
        content = self._build_document_content(document, knowledge)
        
        prompt = f"""
请为以下学术文献生成定制化总结，重点关注：

1. 研究局限与未来方向
2. 按"问题-方法-结论"结构组织
3. 中文控制在400字以内

文献内容：
{content}

请生成定制化总结：
"""
        
        summary = await self._call_deepseek_api(prompt)
        
        return {
            "type": "custom_summary",
            "summary": summary,
            "metadata": {
                "document_id": document.id,
                "template": "问题-方法-结论",
                "focus": "研究局限与未来方向",
                "generated_at": datetime.now().isoformat()
            }
        }
    
    async def _summarize_single_section(self, section, knowledge: Optional[KnowledgeExtraction]) -> str:
        """总结单个章节"""
        # 构建章节内容
        section_content = f"章节标题：{section.title}\n内容：{section.content[:1000]}"
        
        # 根据章节类型生成不同的总结提示
        if any(keyword in section.title for keyword in ["方法", "Method"]):
            prompt = f"""
请总结以下方法章节的核心内容，包括：
1. 方法类型
2. 关键步骤
3. 参数/材料
4. 工具/平台
5. 方法的合理性说明

{section_content}

请生成方法总结（300字以内）：
"""
        elif any(keyword in section.title for keyword in ["结果", "Result"]):
            prompt = f"""
请总结以下结果章节的核心内容，包括：
1. 核心数据
2. 图表解读
3. 结果的统计学意义
4. 与研究目的的对应关系

{section_content}

请生成结果总结（300字以内）：
"""
        else:
            prompt = f"""
请总结以下章节的核心内容，突出要点：

{section_content}

请生成章节总结（300字以内）：
"""
        
        return await self._call_deepseek_api(prompt)
    
    def _build_document_content(self, document: Document, knowledge: Optional[KnowledgeExtraction]) -> str:
        """构建文档内容"""
        content_parts = []
        
        # 添加基本信息
        if document.metadata:
            content_parts.append(f"标题：{document.metadata.title}")
            if document.metadata.abstract:
                content_parts.append(f"摘要：{document.metadata.abstract}")
            if document.metadata.keywords:
                content_parts.append(f"关键词：{', '.join(document.metadata.keywords)}")
        
        # 添加章节内容
        for section in document.sections:
            content_parts.append(f"\n{section.title}：\n{section.content[:500]}")
        
        # 添加知识点信息
        if knowledge:
            if knowledge.core_points:
                points_text = "\n".join([f"- {point.content}" for point in knowledge.core_points[:5]])
                content_parts.append(f"\n核心观点：\n{points_text}")
            
            if knowledge.methods:
                methods_text = "\n".join([f"- {method.method_type}" for method in knowledge.methods[:3]])
                content_parts.append(f"\n研究方法：\n{methods_text}")
            
            if knowledge.results:
                results_text = "\n".join([f"- {result.metric_name}: {result.value}" for result in knowledge.results[:5]])
                content_parts.append(f"\n实验结果：\n{results_text}")
        
        return "\n".join(content_parts)
    
    async def _call_deepseek_api(self, prompt: str) -> str:
        """调用DeepSeek API"""
        if not self.api_key:
            return "抱歉，AI服务未配置，无法生成总结。"
        
        messages = [
            {
                "role": "system",
                "content": """你是一个专业的学术文献总结助手。请根据用户要求生成高质量的文献总结。

要求：
1. 使用简洁、规范的学术语言
2. 保持内容的准确性和客观性
3. 按照指定的结构和字数要求
4. 突出文献的核心价值和贡献
5. 避免重复和冗余信息

请用中文回答。"""
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 1500,
                    "stream": False
                }
                
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["choices"][0]["message"]["content"]
                    else:
                        error_text = await response.text()
                        return f"API调用失败：{response.status} - {error_text}"
        except Exception as e:
            return f"总结生成失败：{str(e)}"
    
    async def generate_summary_by_keywords(
        self, 
        document: Document, 
        keywords: List[str],
        knowledge: Optional[KnowledgeExtraction] = None
    ) -> Dict:
        """根据关键词生成总结"""
        content = self._build_document_content(document, knowledge)
        
        keywords_text = "、".join(keywords)
        prompt = f"""
请根据关键词"{keywords_text}"为以下文献生成相关内容的总结：

文献内容：
{content}

要求：
1. 重点关注与关键词相关的内容
2. 提取相关信息并组织成连贯的总结
3. 中文控制在400字以内

请生成关键词总结：
"""
        
        summary = await self._call_deepseek_api(prompt)
        
        return {
            "type": "keyword_summary",
            "keywords": keywords,
            "summary": summary,
            "metadata": {
                "document_id": document.id,
                "keywords_count": len(keywords),
                "generated_at": datetime.now().isoformat()
            }
        }
    
    async def generate_summary_by_template(
        self, 
        document: Document, 
        template: str,
        knowledge: Optional[KnowledgeExtraction] = None
    ) -> Dict:
        """根据模板生成总结"""
        content = self._build_document_content(document, knowledge)
        
        prompt = f"""
请按照"{template}"模板为以下文献生成总结：

文献内容：
{content}

要求：
1. 严格按照指定模板结构组织内容
2. 每个部分都要有实质性内容
3. 中文控制在500字以内

请生成模板总结：
"""
        
        summary = await self._call_deepseek_api(prompt)
        
        return {
            "type": "template_summary",
            "template": template,
            "summary": summary,
            "metadata": {
                "document_id": document.id,
                "template": template,
                "generated_at": datetime.now().isoformat()
            }
        }
