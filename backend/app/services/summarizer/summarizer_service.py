"""
文献总结服务
"""
import aiohttp
from typing import List, Dict, Optional
from datetime import datetime

from ...models.document import Document
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
        summary_type: str = "full"
    ) -> Dict:
        """
        生成文档总结
        """
        try:
            if summary_type == "full":
                return await self._generate_full_summary(document)
            elif summary_type == "section":
                return await self._generate_section_summary(document)
            elif summary_type == "custom":
                return await self._generate_custom_summary(document)
            else:
                raise ValueError(f"不支持的总结类型: {summary_type}")
                
        except Exception as e:
            return {
                "error": f"总结生成失败: {str(e)}",
                "summary": "",
                "metadata": {}
            }
    
    async def _generate_full_summary(self, document: Document) -> Dict:
        """生成全文献概括总结"""
        # 构建文档内容
        content = self._build_document_content(document)
        
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
                "word_count": document.word_count,
                "generated_at": datetime.now().isoformat()
            }
        }
    
    async def _generate_section_summary(self, document: Document) -> Dict:
        """生成章节聚焦总结"""
        summaries = {}
        
        # 为章节生成总结：不再仅限于主要章节，默认处理前20个章节，避免前端标题匹配不到导致404
        max_sections = 20
        for section in document.sections[:max_sections]:
            try:
                section_summary = await self._summarize_single_section(section)
                summaries[section.title] = section_summary
            except Exception:
                # 单章失败不影响整体
                summaries[section.title] = "该章节总结生成失败。"
        
        return {
            "type": "section_summary",
            "summaries": summaries,
            "metadata": {
                "document_id": document.id,
                "sections_count": len(summaries),
                "generated_at": datetime.now().isoformat()
            }
        }
    
    async def _generate_custom_summary(self, document: Document) -> Dict:
        """生成定制化总结"""
        # 这里可以根据用户需求生成不同类型的总结
        # 例如：仅总结研究局限与未来方向、按特定结构总结等
        
        content = self._build_document_content(document)
        
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
    
    async def summarize_single_section(self, section) -> str:
        """"""
        return await self._summarize_single_section(section)

    async def _summarize_single_section(self, section) -> str:
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
    
    def _build_document_content(self, document: Document) -> str:
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
        
        return "\n".join(content_parts)
    
    async def _call_deepseek_api(self, prompt: str) -> str:
        """调用DeepSeek API"""
        if not self.api_key:
            return "抱歉，AI服务未配置，无法生成总结。"
        
        messages = [
            {
                "role": "system",
                "content": """你是一个专业的学术文献总结助手。

【严格要求】必须完全按照用户指定的格式输出，不得有任何偏差：
1. 如果用户要求特定的标题格式（如**问题：**、**方法：**、**结论：**），必须严格使用相同的格式
2. 标题必须加粗显示（使用**包围）
3. 每个部分必须换行分隔
4. 严格控制字数，不得超出要求范围
5. 使用简洁、规范的学术语言
6. 保持内容的准确性和客观性

【输出格式示例】
**问题：**
这里是问题描述内容

**方法：**
这里是方法描述内容

**结论：**
这里是结论描述内容

请严格遵循用户的格式要求，用中文回答。"""
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
    ) -> Dict:
        """根据关键词生成总结"""
        content = self._build_document_content(document)
        
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
    ) -> Dict:
        """根据模板生成总结"""
        print(f"开始生成模板总结，模板ID: {template}")
        
        content = self._build_document_content(document)
        
        # 根据不同模板生成特定的结构化提示
        template_prompts = {
            "problem_method_conclusion": f"""
你是一个专业的学术总结助手。请严格按照指定格式为以下文献生成结构化总结。

文献内容：
{content}

【重要】必须严格按照以下格式输出，不要添加任何其他内容：

**问题：**
[在这里写研究要解决的核心问题或研究目标，控制在100-150字]

**方法：**
[在这里写采用的研究方法、技术路线、实验设计等，控制在100-150字]

**结论：**
[在这里写主要研究结论、创新点和研究意义，控制在100-150字]

请严格按照上述格式生成总结，每个部分必须以"**问题：**"、"**方法：**"、"**结论：**"开头。
""",
            "background_method_result": f"""
你是一个专业的学术总结助手。请严格按照指定格式为以下文献生成结构化总结。

文献内容：
{content}

【重要】必须严格按照以下格式输出，不要添加任何其他内容：

**背景：**
[在这里写研究背景、现状和必要性，控制在100-150字]

**方法：**
[在这里写研究方法、实验设计、技术手段等，控制在100-150字]

**结果：**
[在这里写主要研究结果、数据发现和分析，控制在100-150字]

请严格按照上述格式生成总结，每个部分必须以"**背景：**"、"**方法：**"、"**结果：**"开头。
""",
            "objective_method_finding": f"""
你是一个专业的学术总结助手。请严格按照指定格式为以下文献生成结构化总结。

文献内容：
{content}

【重要】必须严格按照以下格式输出，不要添加任何其他内容：

**目标：**
[在这里写研究目标、预期成果和解决的问题，控制在100-150字]

**方法：**
[在这里写研究方法、实施路径、技术方案等，控制在100-150字]

**发现：**
[在这里写主要发现、新见解和重要结论，控制在100-150字]

请严格按照上述格式生成总结，每个部分必须以"**目标：**"、"**方法：**"、"**发现：**"开头。
""",
            "limitation_future": f"""
你是一个专业的学术总结助手。请严格按照指定格式为以下文献生成结构化总结。

文献内容：
{content}

【重要】必须严格按照以下格式输出，不要添加任何其他内容：

**局限：**
[在这里写研究的局限性、不足之处和待改进方面，控制在150-200字]

**展望：**
[在这里写未来研究方向、潜在应用和发展前景，控制在150-200字]

请严格按照上述格式生成总结，每个部分必须以"**局限：**"、"**展望：**"开头。
""",
            "contribution_impact": f"""
你是一个专业的学术总结助手。请严格按照指定格式为以下文献生成结构化总结。

文献内容：
{content}

【重要】必须严格按照以下格式输出，不要添加任何其他内容：

**贡献：**
[在这里写研究的主要贡献、创新点和学术价值，控制在150-200字]

**影响：**
[在这里写研究的学术影响、实践意义和社会价值，控制在150-200字]

请严格按照上述格式生成总结，每个部分必须以"**贡献：**"、"**影响：**"开头。
"""
        }
        
        # 选择对应的模板提示，如果没有匹配则使用通用提示
        print(f"可用模板: {list(template_prompts.keys())}")
        print(f"请求模板: {template}")
        
        if template in template_prompts:
            prompt = template_prompts[template]
            print(f"使用特定模板提示词，长度: {len(prompt)}")
        else:
            prompt = f"""
请按照"{template}"模板为以下文献生成总结：

文献内容：
{content}

要求：
1. 严格按照指定模板结构组织内容
2. 每个部分都要有实质性内容
3. 中文控制在500字以内
4. 使用清晰的段落结构

请生成模板总结：
"""
            print(f"使用通用模板提示词，长度: {len(prompt)}")
        
        print(f"发送给AI的提示词前100字符: {prompt[:100]}...")
        
        summary = await self._call_deepseek_api(prompt)
        
        print(f"AI响应前100字符: {summary[:100]}...")
        
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

    async def generate_summary_by_keywords_and_template(
        self, 
        document: Document, 
        keywords: List[str],
        template: str
    ) -> Dict:
        """根据关键词和模板同时生成总结"""
        print(f"开始生成关键词+模板总结，关键词: {keywords}, 模板ID: {template}")
        
        content = self._build_document_content(document)
        keywords_str = "、".join(keywords)
        
        # 根据不同模板生成特定的结构化提示，同时融入关键词
        template_prompts = {
            "problem_method_conclusion": f"""
你是一个专业的学术总结助手。请严格按照指定格式为以下文献生成结构化总结，并特别关注指定的关键词。

文献内容：
{content}

关键词重点：{keywords_str}

【重要】必须严格按照以下格式输出，并在每个部分中体现关键词相关内容：

**问题：**
[在这里写研究要解决的核心问题或研究目标，重点体现关键词"{keywords_str}"相关内容，控制在100-150字]

**方法：**
[在这里写采用的研究方法、技术路线、实验设计等，重点体现关键词"{keywords_str}"相关内容，控制在100-150字]

**结论：**
[在这里写主要研究结论、创新点和研究意义，重点体现关键词"{keywords_str}"相关内容，控制在100-150字]

请严格按照上述格式生成总结，每个部分必须以"**问题：**"、"**方法：**"、"**结论：**"开头，并突出关键词相关内容。
""",
            "background_method_result": f"""
你是一个专业的学术总结助手。请严格按照指定格式为以下文献生成结构化总结，并特别关注指定的关键词。

文献内容：
{content}

关键词重点：{keywords_str}

【重要】必须严格按照以下格式输出，并在每个部分中体现关键词相关内容：

**背景：**
[在这里写研究背景、现状和必要性，重点体现关键词"{keywords_str}"相关内容，控制在100-150字]

**方法：**
[在这里写研究方法、实验设计、技术手段等，重点体现关键词"{keywords_str}"相关内容，控制在100-150字]

**结果：**
[在这里写主要研究结果、数据发现和分析，重点体现关键词"{keywords_str}"相关内容，控制在100-150字]

请严格按照上述格式生成总结，每个部分必须以"**背景：**"、"**方法：**"、"**结果：**"开头，并突出关键词相关内容。
""",
            "objective_method_finding": f"""
你是一个专业的学术总结助手。请严格按照指定格式为以下文献生成结构化总结，并特别关注指定的关键词。

文献内容：
{content}

关键词重点：{keywords_str}

【重要】必须严格按照以下格式输出，并在每个部分中体现关键词相关内容：

**目标：**
[在这里写研究目标、预期成果和解决的问题，重点体现关键词"{keywords_str}"相关内容，控制在100-150字]

**方法：**
[在这里写研究方法、实施路径、技术方案等，重点体现关键词"{keywords_str}"相关内容，控制在100-150字]

**发现：**
[在这里写主要发现、新见解和重要结论，重点体现关键词"{keywords_str}"相关内容，控制在100-150字]

请严格按照上述格式生成总结，每个部分必须以"**目标：**"、"**方法：**"、"**发现：**"开头，并突出关键词相关内容。
""",
            "limitation_future": f"""
你是一个专业的学术总结助手。请严格按照指定格式为以下文献生成结构化总结，并特别关注指定的关键词。

文献内容：
{content}

关键词重点：{keywords_str}

【重要】必须严格按照以下格式输出，并在每个部分中体现关键词相关内容：

**局限：**
[在这里写研究的局限性、不足之处和待改进方面，重点体现关键词"{keywords_str}"相关内容，控制在150-200字]

**展望：**
[在这里写未来研究方向、潜在应用和发展前景，重点体现关键词"{keywords_str}"相关内容，控制在150-200字]

请严格按照上述格式生成总结，每个部分必须以"**局限：**"、"**展望：**"开头，并突出关键词相关内容。
""",
            "contribution_impact": f"""
你是一个专业的学术总结助手。请严格按照指定格式为以下文献生成结构化总结，并特别关注指定的关键词。

文献内容：
{content}

关键词重点：{keywords_str}

【重要】必须严格按照以下格式输出，并在每个部分中体现关键词相关内容：

**贡献：**
[在这里写研究的主要贡献、创新点和学术价值，重点体现关键词"{keywords_str}"相关内容，控制在150-200字]

**影响：**
[在这里写研究的学术影响、实践意义和社会价值，重点体现关键词"{keywords_str}"相关内容，控制在150-200字]

请严格按照上述格式生成总结，每个部分必须以"**贡献：**"、"**影响：**"开头，并突出关键词相关内容。
"""
        }
        
        # 选择对应的模板提示，如果没有匹配则使用通用提示
        print(f"可用模板: {list(template_prompts.keys())}")
        print(f"请求模板: {template}")
        
        if template in template_prompts:
            prompt = template_prompts[template]
            print(f"使用关键词+模板特定提示词，长度: {len(prompt)}")
        else:
            prompt = f"""
请按照"{template}"模板为以下文献生成总结，并特别关注关键词：{keywords_str}

文献内容：
{content}

要求：
1. 严格按照指定模板结构组织内容
2. 每个部分都要突出关键词相关内容
3. 中文控制在500字以内
4. 使用清晰的段落结构

请生成关键词聚焦的模板总结：
"""
            print(f"使用关键词+模板通用提示词，长度: {len(prompt)}")
        
        print(f"发送给AI的提示词前100字符: {prompt[:100]}...")
        
        summary = await self._call_deepseek_api(prompt)
        
        print(f"AI响应前100字符: {summary[:100]}...")
        
        return {
            "type": "keywords_template_summary",
            "template": template,
            "keywords": keywords,
            "summary": summary,
            "metadata": {
                "document_id": document.id,
                "template": template,
                "keywords": keywords,
                "generated_at": datetime.now().isoformat()
            }
        }
