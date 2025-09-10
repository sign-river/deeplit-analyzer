"""
智能问答服务
集成DeepSeek API进行智能问答
"""
import aiohttp
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from ...models.document import Document
from ...models.qa import Question, Answer, QAResponse, QuestionType, AnswerSource
from ...models.knowledge import KnowledgeExtraction
from ...core.config import settings


class QAService:
    """智能问答服务"""
    
    def __init__(self):
        self.api_key = settings.deepseek_api_key
        self.base_url = settings.deepseek_base_url
        self.model = "deepseek-chat"
    
    async def answer_question(
        self, 
        document: Document, 
        question: str, 
        knowledge: Optional[KnowledgeExtraction] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> QAResponse:
        """
        回答用户问题
        """
        start_time = datetime.now()
        
        try:
            # 1. 分析问题类型
            question_type = self._analyze_question_type(question)
            
            # 2. 检索相关文档片段
            relevant_sections = await self._retrieve_relevant_sections(document, question)
            
            # 3. 构建上下文
            context = self._build_context(document, relevant_sections, knowledge)
            
            # 4. 调用DeepSeek API
            answer_text = await self._call_deepseek_api(question, context, conversation_history)
            
            # 5. 构建答案来源
            sources = self._build_answer_sources(relevant_sections)
            
            # 6. 计算置信度
            confidence = self._calculate_confidence(answer_text, relevant_sections)
            
            # 7. 生成后续建议
            follow_up_suggestions = self._generate_follow_up_suggestions(question, question_type)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return QAResponse(
                answer=answer_text,
                confidence=confidence,
                sources=sources,
                question_type=question_type,
                reasoning=self._extract_reasoning(answer_text),
                follow_up_suggestions=follow_up_suggestions,
                processing_time=processing_time
            )
            
        except Exception as e:
            return QAResponse(
                answer=f"抱歉，处理您的问题时出现错误：{str(e)}",
                confidence=0.0,
                sources=[],
                question_type=QuestionType.FACTUAL,
                processing_time=(datetime.now() - start_time).total_seconds()
            )
    
    def _analyze_question_type(self, question: str) -> QuestionType:
        """分析问题类型"""
        question_lower = question.lower()
        
        # 事实类问题关键词
        factual_keywords = ["是什么", "什么是", "多少", "哪个", "谁", "哪里", "什么时候", "how many", "what is", "who", "where", "when"]
        
        # 逻辑类问题关键词
        logical_keywords = ["为什么", "如何", "怎么", "为什么选择", "为什么使用", "why", "how", "why choose"]
        
        # 分析类问题关键词
        analytical_keywords = ["分析", "评价", "比较", "影响", "意义", "局限性", "analyze", "evaluate", "compare", "impact", "limitation"]
        
        if any(keyword in question_lower for keyword in analytical_keywords):
            return QuestionType.ANALYTICAL
        elif any(keyword in question_lower for keyword in logical_keywords):
            return QuestionType.LOGICAL
        else:
            return QuestionType.FACTUAL
    
    async def _retrieve_relevant_sections(self, document: Document, question: str) -> List[Dict]:
        """检索相关文档片段"""
        relevant_sections = []
        
        # 简单的关键词匹配检索
        question_keywords = self._extract_keywords(question)
        
        for section in document.sections:
            section_text = section.content.lower()
            relevance_score = 0
            
            # 计算相关性分数
            for keyword in question_keywords:
                if keyword in section_text:
                    relevance_score += section_text.count(keyword)
            
            if relevance_score > 0:
                relevant_sections.append({
                    "section": section,
                    "score": relevance_score,
                    "text": section.content[:500]  # 限制长度
                })
        
        # 按相关性排序
        relevant_sections.sort(key=lambda x: x["score"], reverse=True)
        
        return relevant_sections[:5]  # 返回最相关的5个片段
    
    def _build_context(self, document: Document, relevant_sections: List[Dict], knowledge: Optional[KnowledgeExtraction]) -> str:
        """构建上下文"""
        context_parts = []
        
        # 添加文档基本信息
        if document.metadata:
            context_parts.append(f"文档标题：{document.metadata.title}")
            if document.metadata.abstract:
                context_parts.append(f"摘要：{document.metadata.abstract[:300]}")
        
        # 添加相关章节
        for section_info in relevant_sections:
            section = section_info["section"]
            context_parts.append(f"章节：{section.title}\n内容：{section_info['text']}")
        
        # 添加知识点信息
        if knowledge:
            if knowledge.core_points:
                points_text = "\n".join([f"- {point.content}" for point in knowledge.core_points[:3]])
                context_parts.append(f"核心观点：\n{points_text}")
            
            if knowledge.methods:
                methods_text = "\n".join([f"- {method.method_type}: {', '.join(method.core_steps[:2])}" for method in knowledge.methods[:2]])
                context_parts.append(f"研究方法：\n{methods_text}")
        
        return "\n\n".join(context_parts)
    
    async def _call_deepseek_api(self, question: str, context: str, conversation_history: Optional[List[Dict]]) -> str:
        """调用DeepSeek API"""
        if not self.api_key:
            return "抱歉，AI服务未配置，无法回答问题。"
        
        # 构建消息
        messages = [
            {
                "role": "system",
                "content": """你是一个专业的学术文献分析助手。请基于提供的文献内容回答用户的问题。

要求：
1. 答案必须基于文献内容，不要编造信息
2. 如果文献中没有相关信息，请明确说明
3. 提供准确的答案来源
4. 使用简洁、专业的学术语言
5. 对于分析类问题，请提供合理的推理过程

请用中文回答。"""
            }
        ]
        
        # 添加对话历史
        if conversation_history:
            for history in conversation_history[-3:]:  # 只保留最近3轮对话
                messages.append({"role": "user", "content": history.get("question", "")})
                messages.append({"role": "assistant", "content": history.get("answer", "")})
        
        # 添加当前问题和上下文
        user_content = f"文献内容：\n{context}\n\n问题：{question}"
        messages.append({"role": "user", "content": user_content})
        
        # 调用API
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 1000,
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
    
    def _build_answer_sources(self, relevant_sections: List[Dict]) -> List[AnswerSource]:
        """构建答案来源"""
        sources = []
        
        for section_info in relevant_sections:
            section = section_info["section"]
            source = AnswerSource(
                source_type="section",
                source_id=section.id,
                source_text=section_info["text"],
                confidence=min(section_info["score"] / 10.0, 1.0)  # 归一化置信度
            )
            sources.append(source)
        
        return sources
    
    def _calculate_confidence(self, answer: str, relevant_sections: List[Dict]) -> float:
        """计算答案置信度"""
        if not relevant_sections:
            return 0.0
        
        # 基于相关片段数量和答案长度计算置信度
        base_confidence = min(len(relevant_sections) / 3.0, 1.0)
        
        # 如果答案包含"未找到"、"没有"等词汇，降低置信度
        low_confidence_words = ["未找到", "没有", "无法", "不清楚", "不确定"]
        if any(word in answer for word in low_confidence_words):
            base_confidence *= 0.5
        
        return min(base_confidence, 1.0)
    
    def _generate_follow_up_suggestions(self, question: str, question_type: QuestionType) -> List[str]:
        """生成后续建议"""
        suggestions = []
        
        if question_type == QuestionType.FACTUAL:
            suggestions = [
                "能否详细解释这个结果？",
                "这个结果有什么意义？",
                "还有其他相关数据吗？"
            ]
        elif question_type == QuestionType.LOGICAL:
            suggestions = [
                "这个方法的优缺点是什么？",
                "为什么选择这种方法？",
                "还有其他替代方案吗？"
            ]
        elif question_type == QuestionType.ANALYTICAL:
            suggestions = [
                "这个研究的局限性是什么？",
                "对未来研究有什么建议？",
                "如何改进这个方法？"
            ]
        
        return suggestions[:3]  # 返回3个建议
    
    def _extract_reasoning(self, answer: str) -> Optional[str]:
        """提取推理过程"""
        # 简单的推理提取（实际应用中可以使用更复杂的方法）
        reasoning_keywords = ["因为", "由于", "因此", "所以", "基于", "根据"]
        
        for keyword in reasoning_keywords:
            if keyword in answer:
                # 提取包含推理关键词的句子
                sentences = answer.split("。")
                for sentence in sentences:
                    if keyword in sentence:
                        return sentence.strip()
        
        return None
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        import re
        
        # 简单的关键词提取
        words = re.findall(r'[\u4e00-\u9fa5A-Za-z]+', text)
        
        # 过滤常见词
        stop_words = {"的", "了", "是", "在", "有", "和", "与", "或", "但", "然而", "因此", "所以"}
        keywords = [word for word in words if word not in stop_words and len(word) > 1]
        
        return keywords[:10]  # 返回前10个关键词
    
    async def multi_turn_conversation(
        self, 
        document: Document, 
        conversation_history: List[Dict],
        current_question: str
    ) -> QAResponse:
        """多轮对话"""
        return await self.answer_question(
            document=document,
            question=current_question,
            conversation_history=conversation_history
        )
