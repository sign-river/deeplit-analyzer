"""
知识点提取服务
"""
import re
from typing import List, Dict, Optional, Tuple
from collections import Counter

from ...models.document import Document, Section
from ...models.knowledge import (
    KnowledgeExtraction, CorePoint, ResearchMethod, ExperimentalResult,
    ResearchLimitation, FutureWork, KeywordTree, ConfidenceLevel
)


class KnowledgeExtractor:
    """知识点提取器"""
    
    def __init__(self):
        # 学科特定的提取规则
        self.discipline_rules = {
            "医学": {
                "method_keywords": ["随机对照试验", "双盲", "样本量", "统计学", "P值"],
                "result_keywords": ["有效率", "治愈率", "不良反应", "生存率", "复发率"],
                "limitation_keywords": ["样本量", "随访时间", "单中心", "回顾性"]
            },
            "计算机": {
                "method_keywords": ["算法", "模型", "数据集", "准确率", "性能"],
                "result_keywords": ["准确率", "召回率", "F1分数", "运行时间", "内存使用"],
                "limitation_keywords": ["数据集", "计算资源", "泛化能力", "可扩展性"]
            },
            "生物学": {
                "method_keywords": ["实验设计", "对照组", "样本", "检测", "分析"],
                "result_keywords": ["表达量", "活性", "浓度", "显著性", "相关性"],
                "limitation_keywords": ["样本量", "实验条件", "时间限制", "技术限制"]
            }
        }
    
    async def extract_knowledge(self, document: Document, discipline: str = "通用") -> KnowledgeExtraction:
        """
        提取文档知识点
        """
        extraction = KnowledgeExtraction(
            document_id=document.id,
            discipline=discipline
        )
        
        try:
            # 提取核心观点
            extraction.core_points = await self._extract_core_points(document)
            
            # 提取研究方法
            extraction.methods = await self._extract_methods(document, discipline)
            
            # 提取实验结果
            extraction.results = await self._extract_results(document, discipline)
            
            # 提取研究局限
            extraction.limitations = await self._extract_limitations(document, discipline)
            
            # 提取未来展望
            extraction.future_work = await self._extract_future_work(document)
            
            # 提取关键词树
            extraction.keyword_trees = await self._extract_keyword_trees(document)
            
            # 计算提取统计
            extraction.extraction_accuracy = self._calculate_accuracy(extraction)
            extraction.redundancy_ratio = self._calculate_redundancy(extraction)
            
            return extraction
            
        except Exception as e:
            print(f"知识点提取失败: {e}")
            return extraction
    
    async def _extract_core_points(self, document: Document) -> List[CorePoint]:
        """提取核心观点"""
        core_points = []
        
        # 目标章节
        target_sections = ["摘要", "讨论", "结论", "Abstract", "Discussion", "Conclusion"]
        
        for section in document.sections:
            if any(keyword in section.title for keyword in target_sections):
                points = self._find_core_points_in_text(section.content)
                
                for i, point in enumerate(points):
                    core_point = CorePoint(
                        id=f"cp_{document.id}_{len(core_points)}",
                        content=point,
                        source_section=section.title,
                        confidence=self._calculate_confidence(point)
                    )
                    core_points.append(core_point)
        
        return core_points[:10]  # 限制数量
    
    async def _extract_methods(self, document: Document, discipline: str) -> List[ResearchMethod]:
        """提取研究方法"""
        methods = []
        
        # 目标章节
        method_sections = ["方法", "实验方法", "材料与方法", "Method", "Methods", "Materials and Methods"]
        
        for section in document.sections:
            if any(keyword in section.title for keyword in method_sections):
                method = self._parse_method_section(section.content, discipline)
                if method:
                    method.id = f"method_{document.id}_{len(methods)}"
                    method.source_section = section.title
                    methods.append(method)
        
        return methods
    
    async def _extract_results(self, document: Document, discipline: str) -> List[ExperimentalResult]:
        """提取实验结果"""
        results = []
        
        # 目标章节
        result_sections = ["结果", "实验结果", "Result", "Results"]
        
        for section in document.sections:
            if any(keyword in section.title for keyword in result_sections):
                section_results = self._parse_result_section(section.content, discipline)
                
                for i, result in enumerate(section_results):
                    result.id = f"result_{document.id}_{len(results)}"
                    result.source_section = section.title
                    results.append(result)
        
        return results
    
    async def _extract_limitations(self, document: Document, discipline: str) -> List[ResearchLimitation]:
        """提取研究局限"""
        limitations = []
        
        # 目标章节
        limitation_sections = ["讨论", "结论", "局限", "Discussion", "Conclusion", "Limitation"]
        
        for section in document.sections:
            if any(keyword in section.title for keyword in limitation_sections):
                section_limitations = self._find_limitations_in_text(section.content, discipline)
                
                for i, limitation in enumerate(section_limitations):
                    lim = ResearchLimitation(
                        id=f"lim_{document.id}_{len(limitations)}",
                        limitation_type=limitation["type"],
                        description=limitation["description"],
                        source_section=section.title,
                        confidence=ConfidenceLevel.MEDIUM
                    )
                    limitations.append(lim)
        
        return limitations
    
    async def _extract_future_work(self, document: Document) -> List[FutureWork]:
        """提取未来展望"""
        future_work = []
        
        # 目标章节
        future_sections = ["讨论", "结论", "展望", "Discussion", "Conclusion", "Future Work"]
        
        for section in document.sections:
            if any(keyword in section.title for keyword in future_sections):
                work_items = self._find_future_work_in_text(section.content)
                
                for i, work in enumerate(work_items):
                    fw = FutureWork(
                        id=f"fw_{document.id}_{len(future_work)}",
                        direction=work["direction"],
                        description=work["description"],
                        source_section=section.title,
                        confidence=ConfidenceLevel.MEDIUM
                    )
                    future_work.append(fw)
        
        return future_work
    
    async def _extract_keyword_trees(self, document: Document) -> List[KeywordTree]:
        """提取关键词树"""
        keyword_trees = []
        
        # 获取基础关键词
        base_keywords = []
        if document.metadata and document.metadata.keywords:
            base_keywords = document.metadata.keywords
        
        # 从全文中提取关键词
        full_text = " ".join([section.content for section in document.sections])
        all_keywords = self._extract_keywords_from_text(full_text)
        
        # 为每个基础关键词创建关键词树
        for base_keyword in base_keywords:
            related_keywords = self._find_related_keywords(base_keyword, all_keywords)
            
            tree = KeywordTree(
                core_keyword=base_keyword,
                related_keywords=related_keywords,
                frequency=all_keywords.get(base_keyword, 0),
                importance_score=self._calculate_importance_score(base_keyword, full_text)
            )
            keyword_trees.append(tree)
        
        return keyword_trees
    
    def _find_core_points_in_text(self, text: str) -> List[str]:
        """在文本中查找核心观点"""
        points = []
        
        # 核心观点模式
        patterns = [
            r'[。！？]([^。！？]*(?:提出|证明|发现|表明|显示|证实|验证)[^。！？]*)[。！？]',
            r'[。！？]([^。！？]*(?:提高|提升|改善|优化|增强)[^。！？]*)[。！？]',
            r'[。！？]([^。！？]*(?:显著|明显|有效|成功)[^。！？]*)[。！？]'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match.strip()) > 20 and len(match.strip()) < 200:
                    points.append(match.strip())
        
        return points[:5]  # 限制数量
    
    def _parse_method_section(self, text: str, discipline: str) -> Optional[ResearchMethod]:
        """解析方法章节"""
        # 识别方法类型
        method_type = self._identify_method_type(text)
        
        # 提取关键步骤
        steps = self._extract_method_steps(text)
        
        # 提取关键参数
        parameters = self._extract_parameters(text)
        
        # 提取工具和平台
        tools = self._extract_tools(text)
        
        return ResearchMethod(
            method_type=method_type,
            core_steps=steps,
            key_parameters=parameters,
            tools=tools,
            confidence=ConfidenceLevel.MEDIUM
        )
    
    def _parse_result_section(self, text: str, discipline: str) -> List[ExperimentalResult]:
        """解析结果章节"""
        results = []
        
        # 查找数值结果
        number_patterns = [
            r'([^。！？]*(?:准确率|准确度|精度|召回率|F1|AUC|P值|t值|χ²)[^。！？]*\d+[%\.\d]*[^。！？]*)[。！？]',
            r'([^。！？]*\d+[%\.\d]*(?:提高|提升|改善|降低|减少)[^。！？]*)[。！？]',
            r'([^。！？]*(?:P\s*[<>=]\s*0\.\d+)[^。！？]*)[。！？]'
        ]
        
        for pattern in number_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                result = self._parse_single_result(match)
                if result:
                    results.append(result)
        
        return results
    
    def _find_limitations_in_text(self, text: str, discipline: str) -> List[Dict]:
        """在文本中查找研究局限"""
        limitations = []
        
        # 局限模式
        limitation_patterns = [
            r'([^。！？]*(?:局限|不足|缺点|限制|问题)[^。！？]*)[。！？]',
            r'([^。！？]*(?:样本量|样本数|样本大小)[^。！？]*)[。！？]',
            r'([^。！？]*(?:时间|周期|随访)[^。！？]*(?:短|少|不足)[^。！？]*)[。！？]'
        ]
        
        for pattern in limitation_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match.strip()) > 10:
                    limitations.append({
                        "type": "一般局限",
                        "description": match.strip()
                    })
        
        return limitations
    
    def _find_future_work_in_text(self, text: str) -> List[Dict]:
        """在文本中查找未来工作"""
        future_work = []
        
        # 未来工作模式
        future_patterns = [
            r'([^。！？]*(?:未来|今后|后续|进一步|下一步)[^。！？]*)[。！？]',
            r'([^。！？]*(?:建议|推荐|希望)[^。！？]*)[。！？]',
            r'([^。！？]*(?:探索|研究|改进|优化)[^。！？]*)[。！？]'
        ]
        
        for pattern in future_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match.strip()) > 10:
                    future_work.append({
                        "direction": "研究方向",
                        "description": match.strip()
                    })
        
        return future_work
    
    def _extract_keywords_from_text(self, text: str) -> Dict[str, int]:
        """从文本中提取关键词"""
        # 简单的关键词提取（实际应用中可以使用更复杂的NLP技术）
        words = re.findall(r'[\u4e00-\u9fa5A-Za-z]+', text)
        word_freq = Counter(words)
        
        # 过滤常见词
        stop_words = {'研究', '方法', '结果', '讨论', '结论', '实验', '数据', '分析', '研究', '方法', '结果', '讨论', '结论', '实验', '数据', '分析'}
        filtered_words = {word: freq for word, freq in word_freq.items() 
                         if word not in stop_words and len(word) > 1 and freq > 2}
        
        return filtered_words
    
    def _find_related_keywords(self, base_keyword: str, all_keywords: Dict[str, int]) -> List[str]:
        """查找相关关键词"""
        related = []
        
        # 简单的相关性判断（实际应用中可以使用词向量等更复杂的方法）
        for keyword, freq in all_keywords.items():
            if (base_keyword in keyword or keyword in base_keyword) and keyword != base_keyword:
                related.append(keyword)
        
        return related[:10]  # 限制数量
    
    def _identify_method_type(self, text: str) -> str:
        """识别方法类型"""
        method_types = {
            "随机对照试验": ["随机", "对照", "RCT", "randomized", "controlled"],
            "问卷调查": ["问卷", "调查", "survey", "questionnaire"],
            "仿真实验": ["仿真", "模拟", "simulation", "model"],
            "案例分析": ["案例", "个案", "case study", "case analysis"],
            "实验研究": ["实验", "experiment", "experimental"]
        }
        
        for method_type, keywords in method_types.items():
            if any(keyword in text for keyword in keywords):
                return method_type
        
        return "其他"
    
    def _extract_method_steps(self, text: str) -> List[str]:
        """提取方法步骤"""
        steps = []
        
        # 查找步骤模式
        step_patterns = [
            r'(\d+[\.\)]\s*[^。！？]+)',
            r'([^。！？]*(?:首先|然后|接着|最后|第一步|第二步)[^。！？]*)[。！？]'
        ]
        
        for pattern in step_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match.strip()) > 5:
                    steps.append(match.strip())
        
        return steps[:5]  # 限制数量
    
    def _extract_parameters(self, text: str) -> Dict[str, str]:
        """提取关键参数"""
        parameters = {}
        
        # 参数模式
        param_patterns = [
            r'([^。！？]*(?:学习率|learning rate|batch size|epoch|迭代)[^。！？]*\d+[^。！？]*)[。！？]',
            r'([^。！？]*(?:浓度|剂量|温度|时间)[^。！？]*\d+[^。！？]*)[。！？]'
        ]
        
        for pattern in param_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                # 简单的参数提取
                if '=' in match:
                    parts = match.split('=')
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip()
                        parameters[key] = value
        
        return parameters
    
    def _extract_tools(self, text: str) -> List[str]:
        """提取工具和平台"""
        tools = []
        
        # 常见工具
        tool_keywords = [
            "Python", "R", "MATLAB", "SPSS", "SAS", "TensorFlow", "PyTorch",
            "Keras", "Scikit-learn", "Pandas", "NumPy", "Excel", "Origin"
        ]
        
        for tool in tool_keywords:
            if tool in text:
                tools.append(tool)
        
        return tools
    
    def _parse_single_result(self, text: str) -> Optional[ExperimentalResult]:
        """解析单个结果"""
        # 提取数值
        numbers = re.findall(r'\d+[\.\d]*[%]?', text)
        if not numbers:
            return None
        
        # 提取指标名称
        metric_name = "未知指标"
        metric_keywords = ["准确率", "召回率", "F1", "AUC", "P值", "t值", "χ²"]
        for keyword in metric_keywords:
            if keyword in text:
                metric_name = keyword
                break
        
        return ExperimentalResult(
            metric_name=metric_name,
            value=numbers[0],
            confidence=ConfidenceLevel.MEDIUM
        )
    
    def _calculate_confidence(self, text: str) -> ConfidenceLevel:
        """计算置信度"""
        # 简单的置信度计算
        if len(text) > 50 and any(keyword in text for keyword in ["显著", "明显", "有效", "成功"]):
            return ConfidenceLevel.HIGH
        elif len(text) > 20:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def _calculate_importance_score(self, keyword: str, text: str) -> float:
        """计算重要性分数"""
        # 简单的TF-IDF计算
        word_count = text.count(keyword)
        total_words = len(text.split())
        return word_count / total_words if total_words > 0 else 0.0
    
    def _calculate_accuracy(self, extraction: KnowledgeExtraction) -> float:
        """计算提取准确率"""
        # 简单的准确率估算
        total_items = (len(extraction.core_points) + len(extraction.methods) + 
                      len(extraction.results) + len(extraction.limitations))
        
        if total_items == 0:
            return 0.0
        
        # 基于置信度计算
        high_confidence = sum(1 for item in extraction.core_points if item.confidence == ConfidenceLevel.HIGH)
        return high_confidence / total_items if total_items > 0 else 0.0
    
    def _calculate_redundancy(self, extraction: KnowledgeExtraction) -> float:
        """计算冗余率"""
        # 简单的冗余率计算
        all_texts = []
        for point in extraction.core_points:
            all_texts.append(point.content)
        
        # 计算相似度（简化版）
        similar_count = 0
        for i in range(len(all_texts)):
            for j in range(i + 1, len(all_texts)):
                if self._text_similarity(all_texts[i], all_texts[j]) > 0.8:
                    similar_count += 1
        
        return similar_count / len(all_texts) if all_texts else 0.0
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度（简化版）"""
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
