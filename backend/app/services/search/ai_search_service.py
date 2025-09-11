"""
AI增强文档检索服务
支持分批并发处理和智能相关性评估
"""
import asyncio
import re
from typing import List, Dict, Optional, Tuple
import json
from datetime import datetime
import logging

from ...models.document import Document
from ...core.config import settings
from rapidfuzz import fuzz
import requests

logger = logging.getLogger(__name__)


class AISearchService:
    """AI增强的文档检索服务"""
    
    def __init__(self):
        self.api_key = settings.deepseek_api_key
        self.base_url = settings.deepseek_base_url
        self.max_chunk_size = 1500  # 每个片段的最大字符数
        self.min_chunk_size = 300   # 最小片段大小
        self.max_concurrent = 5     # 最大并发API调用数
        
    async def enhanced_search(self, document: Document, query: str, top_k: int = 10) -> List[Dict]:
        """
        AI增强的文档检索
        
        Args:
            document: 要搜索的文档
            query: 搜索查询
            top_k: 返回的结果数量
            
        Returns:
            List[Dict]: 搜索结果列表
        """
        try:
            # 1. 预处理：提取文档片段
            text_chunks = self._extract_document_chunks(document)
            
            if not text_chunks:
                return []
            
            # 2. 初步筛选：基于关键词的快速过滤
            filtered_chunks = self._preliminary_filter(text_chunks, query)
            
            # 3. AI评估：并发调用DeepSeek API进行智能相关性评估
            ai_scores = await self._ai_relevance_scoring(filtered_chunks, query)
            
            # 4. 综合评分并排序
            final_results = self._combine_scores_and_rank(filtered_chunks, ai_scores, top_k)
            
            return final_results
            
        except Exception as e:
            logger.error(f"AI检索失败: {str(e)}")
            raise Exception(f"检索失败: {str(e)}")
    
    def _extract_document_chunks(self, document: Document) -> List[Dict]:
        """提取文档片段"""
        chunks = []
        
        for section in document.sections:
            if not section.content or len(section.content.strip()) < 100:
                continue
                
            # 清理文本
            cleaned_text = self._clean_text(section.content)
            
            # 如果章节内容较短，直接作为一个片段
            if len(cleaned_text) <= self.max_chunk_size:
                chunks.append({
                    'section_id': section.id,
                    'section_title': section.title,
                    'text': cleaned_text,
                    'start_pos': 0,
                    'end_pos': len(cleaned_text)
                })
            else:
                # 长章节需要分割
                sub_chunks = self._split_long_section(cleaned_text, section)
                chunks.extend(sub_chunks)
        
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """清理文本"""
        # 去除多余空白
        text = re.sub(r'\s+', ' ', text)
        # 去除markdown标记和特殊字符
        text = re.sub(r'[#*_`">]', '', text)
        # 去除多余的换行
        text = re.sub(r'\n\s*\n', '\n', text)
        return text.strip()
    
    def _split_long_section(self, text: str, section) -> List[Dict]:
        """分割长章节"""
        chunks = []
        
        # 首先按段落分割
        paragraphs = re.split(r'\n\s*\n', text)
        
        current_chunk = ""
        start_pos = 0
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
                
            # 如果添加这个段落不会超出大小限制
            if len(current_chunk) + len(paragraph) + 2 <= self.max_chunk_size:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
            else:
                # 保存当前片段
                if len(current_chunk) >= self.min_chunk_size:
                    chunks.append({
                        'section_id': section.id,
                        'section_title': section.title,
                        'text': current_chunk,
                        'start_pos': start_pos,
                        'end_pos': start_pos + len(current_chunk)
                    })
                    start_pos += len(current_chunk)
                
                # 开始新片段
                current_chunk = paragraph
        
        # 添加最后一个片段
        if len(current_chunk) >= self.min_chunk_size:
            chunks.append({
                'section_id': section.id,
                'section_title': section.title,
                'text': current_chunk,
                'start_pos': start_pos,
                'end_pos': start_pos + len(current_chunk)
            })
        
        return chunks
    
    def _preliminary_filter(self, chunks: List[Dict], query: str, threshold: float = 30.0) -> List[Dict]:
        """基于关键词的初步筛选"""
        query_keywords = self._extract_keywords(query.lower())
        filtered = []
        
        for chunk in chunks:
            text_lower = chunk['text'].lower()
            
            # 计算关键词匹配分数
            keyword_score = sum(text_lower.count(kw) for kw in query_keywords)
            
            # 计算模糊匹配分数
            fuzzy_score = fuzz.partial_ratio(text_lower, query.lower())
            
            # 综合分数
            combined_score = keyword_score * 10 + fuzzy_score
            
            if combined_score >= threshold:
                chunk['preliminary_score'] = combined_score
                filtered.append(chunk)
        
        # 按初步分数排序，只保留前50个候选
        filtered.sort(key=lambda x: x['preliminary_score'], reverse=True)
        return filtered[:50]
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 移除停用词和标点符号
        stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
        
        # 简单分词（可以替换为更好的分词工具）
        words = re.findall(r'\w+', text)
        keywords = [w for w in words if len(w) > 1 and w not in stop_words]
        
        return list(set(keywords))[:10]  # 最多保留10个关键词
    
    async def _ai_relevance_scoring(self, chunks: List[Dict], query: str) -> List[float]:
        """AI相关性评分（并发处理）"""
        if not chunks:
            return []
        
        # 将片段分批处理
        batches = self._create_batches(chunks, batch_size=self.max_concurrent)
        all_scores = []
        
        for batch in batches:
            # 并发处理每一批
            batch_tasks = []
            for chunk in batch:
                task = self._score_single_chunk(chunk['text'], query)
                batch_tasks.append(task)
            
            try:
                batch_scores = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                # 处理结果，对于异常的情况使用回退分数
                processed_scores = []
                for score in batch_scores:
                    if isinstance(score, Exception):
                        logger.warning(f"AI评分失败，使用回退分数: {str(score)}")
                        processed_scores.append(0.5)  # 回退分数
                    else:
                        processed_scores.append(score)
                
                all_scores.extend(processed_scores)
                
                # 在批次之间添加小延迟，避免API限制
                if len(batches) > 1:
                    await asyncio.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"批次处理失败: {str(e)}")
                # 对整个批次使用回退分数
                all_scores.extend([0.5] * len(batch))
        
        return all_scores
    
    def _create_batches(self, items: List, batch_size: int) -> List[List]:
        """创建批次"""
        batches = []
        for i in range(0, len(items), batch_size):
            batches.append(items[i:i + batch_size])
        return batches
    
    async def _score_single_chunk(self, text: str, query: str) -> float:
        """为单个文本片段评分"""
        try:
            prompt = f"""请评估以下文本片段与查询的相关性。

查询: {query}

文本片段:
{text[:1000]}...

请从以下角度评估相关性：
1. 内容匹配度（文本是否直接回答了查询）
2. 语义相关性（即使没有直接回答，是否讨论了相关主题）
3. 信息价值（文本包含的信息对查询者是否有用）

请只返回一个0到1之间的数字，表示相关性分数（1表示非常相关，0表示完全不相关）。
只返回数字，不要其他说明。"""

            response = await self._call_deepseek_api(prompt)
            
            if response:
                # 尝试提取数字
                score_text = response.strip()
                try:
                    score = float(score_text)
                    return max(0.0, min(1.0, score))  # 确保在0-1范围内
                except ValueError:
                    # 如果无法解析数字，尝试从文本中提取
                    import re
                    numbers = re.findall(r'0\.\d+|1\.0+|0|1', score_text)
                    if numbers:
                        return float(numbers[0])
            
            return 0.5  # 默认分数
            
        except Exception as e:
            logger.error(f"AI评分失败: {str(e)}")
            return 0.5
    
    async def _call_deepseek_api(self, prompt: str) -> Optional[str]:
        """调用DeepSeek API"""
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': 'deepseek-chat',
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'temperature': 0.1,
                'max_tokens': 10
            }
            
            # 使用asyncio运行同步的requests调用
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=10
                )
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and result['choices']:
                    return result['choices'][0]['message']['content'].strip()
            else:
                logger.error(f"DeepSeek API错误: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"调用DeepSeek API失败: {str(e)}")
        
        return None
    
    def _combine_scores_and_rank(self, chunks: List[Dict], ai_scores: List[float], top_k: int) -> List[Dict]:
        """综合评分并排序"""
        results = []
        
        for i, chunk in enumerate(chunks):
            if i < len(ai_scores):
                ai_score = ai_scores[i]
                preliminary_score = chunk.get('preliminary_score', 0)
                
                # 综合分数：AI分数权重70%，初步分数权重30%
                final_score = ai_score * 0.7 + (preliminary_score / 100.0) * 0.3
                
                results.append({
                    'section_id': chunk['section_id'],
                    'section_title': chunk['section_title'],
                    'text': chunk['text'],
                    'score': final_score,
                    'ai_score': ai_score,
                    'preliminary_score': preliminary_score,
                    'start_pos': chunk.get('start_pos', 0),
                    'end_pos': chunk.get('end_pos', len(chunk['text']))
                })
        
        # 按综合分数排序
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results[:top_k]