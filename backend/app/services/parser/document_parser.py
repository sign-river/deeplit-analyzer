"""
文档解析服务
支持多种格式的文档解析
"""
import os
import fitz  # PyMuPDF
from docx import Document as DocxDocument
from bs4 import BeautifulSoup
import pytesseract
from PIL import Image
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from ...models.document import (
    Document, DocumentMetadata, Author, Section, Figure, Reference,
    DocumentType, DocumentStatus
)
from ...core.config import settings


class DocumentParser:
    """文档解析器"""
    
    def __init__(self):
        # 设置Tesseract路径
        if settings.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
    
    async def parse_document(self, document: Document) -> Document:
        """
        解析文档
        """
        try:
            if document.document_type == DocumentType.PDF:
                return await self._parse_pdf(document)
            elif document.document_type == DocumentType.WORD:
                return await self._parse_word(document)
            elif document.document_type == DocumentType.LATEX:
                return await self._parse_latex(document)
            elif document.document_type == DocumentType.HTML:
                return await self._parse_html(document)
            else:
                return await self._parse_text(document)
        except Exception as e:
            document.status = DocumentStatus.FAILED
            document.processing_errors.append(f"解析失败: {str(e)}")
            return document
    
    async def _parse_pdf(self, document: Document) -> Document:
        """解析PDF文档"""
        try:
            doc = fitz.open(document.file_path)
            
            # 检查是否需要OCR
            if self._needs_ocr(doc):
                return await self._parse_pdf_with_ocr(document, doc)
            else:
                return await self._parse_pdf_text(document, doc)
                
        except Exception as e:
            document.processing_errors.append(f"PDF解析失败: {str(e)}")
            return document
    
    async def _parse_pdf_text(self, document: Document, doc) -> Document:
        """解析可编辑PDF"""
        full_text = ""
        sections = []
        figures = []
        references = []
        
        # 提取文本和元数据
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text("text")
            full_text += page_text + "\n"
            
            # 提取图片
            image_list = page.get_images()
            for img_index, img in enumerate(image_list):
                figure = Figure(
                    id=f"fig_{page_num}_{img_index}",
                    caption=f"图 {page_num + 1}-{img_index + 1}",
                    type="figure",
                    page_number=page_num + 1
                )
                figures.append(figure)
        
        # 解析章节
        sections = self._extract_sections(full_text)
        
        # 提取元数据
        metadata = self._extract_metadata(full_text, doc.metadata)
        
        # 提取参考文献
        references = self._extract_references(full_text)
        
        # 更新文档
        document.metadata = metadata
        document.sections = sections
        document.figures = figures
        document.references = references
        document.page_count = len(doc)
        document.word_count = len(full_text.split())
        
        doc.close()
        return document
    
    async def _parse_pdf_with_ocr(self, document: Document, doc) -> Document:
        """使用OCR解析扫描PDF"""
        full_text = ""
        sections = []
        figures = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # 转换为图片
            pix = page.get_pixmap(dpi=300)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # OCR识别
            try:
                page_text = pytesseract.image_to_string(img, lang='chi_sim+eng')
                full_text += page_text + "\n"
            except Exception as e:
                document.processing_errors.append(f"OCR识别失败 (第{page_num + 1}页): {str(e)}")
        
        # 解析章节和元数据
        sections = self._extract_sections(full_text)
        metadata = self._extract_metadata(full_text, {})
        references = self._extract_references(full_text)
        
        document.metadata = metadata
        document.sections = sections
        document.figures = figures
        document.references = references
        document.page_count = len(doc)
        document.word_count = len(full_text.split())
        
        doc.close()
        return document
    
    async def _parse_word(self, document: Document) -> Document:
        """解析Word文档"""
        try:
            doc = DocxDocument(document.file_path)
            
            # 提取段落
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            full_text = "\n".join(paragraphs)
            
            # 解析章节
            sections = self._extract_sections(full_text)
            
            # 提取元数据
            metadata = self._extract_metadata(full_text, {})
            
            # 提取参考文献
            references = self._extract_references(full_text)
            
            document.metadata = metadata
            document.sections = sections
            document.references = references
            document.word_count = len(full_text.split())
            
            return document
            
        except Exception as e:
            document.processing_errors.append(f"Word解析失败: {str(e)}")
            return document
    
    async def _parse_latex(self, document: Document) -> Document:
        """解析LaTeX文档"""
        try:
            with open(document.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 简单的LaTeX解析
            full_text = self._latex_to_text(content)
            
            # 解析章节
            sections = self._extract_sections(full_text)
            
            # 提取元数据
            metadata = self._extract_metadata(full_text, {})
            
            # 提取参考文献
            references = self._extract_references(full_text)
            
            document.metadata = metadata
            document.sections = sections
            document.references = references
            document.word_count = len(full_text.split())
            
            return document
            
        except Exception as e:
            document.processing_errors.append(f"LaTeX解析失败: {str(e)}")
            return document
    
    async def _parse_html(self, document: Document) -> Document:
        """解析HTML文档"""
        try:
            with open(document.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # 提取文本
            full_text = soup.get_text()
            
            # 解析章节
            sections = self._extract_sections(full_text)
            
            # 提取元数据
            metadata = self._extract_metadata(full_text, {})
            
            # 提取参考文献
            references = self._extract_references(full_text)
            
            document.metadata = metadata
            document.sections = sections
            document.references = references
            document.word_count = len(full_text.split())
            
            return document
            
        except Exception as e:
            document.processing_errors.append(f"HTML解析失败: {str(e)}")
            return document
    
    async def _parse_text(self, document: Document) -> Document:
        """解析纯文本文档"""
        try:
            with open(document.file_path, 'r', encoding='utf-8') as f:
                full_text = f.read()
            
            # 解析章节
            sections = self._extract_sections(full_text)
            
            # 提取元数据
            metadata = self._extract_metadata(full_text, {})
            
            # 提取参考文献
            references = self._extract_references(full_text)
            
            document.metadata = metadata
            document.sections = sections
            document.references = references
            document.word_count = len(full_text.split())
            
            return document
            
        except Exception as e:
            document.processing_errors.append(f"文本解析失败: {str(e)}")
            return document
    
    def _needs_ocr(self, doc) -> bool:
        """检查PDF是否需要OCR"""
        # 检查前几页是否有可提取的文本
        for page_num in range(min(3, len(doc))):
            page = doc[page_num]
            text = page.get_text("text").strip()
            if len(text) > 100:  # 如果有足够的文本，不需要OCR
                return False
        return True
    
    def _extract_sections(self, text: str) -> List[Section]:
        """提取文档章节"""
        sections = []
        
        # 章节标题模式
        section_patterns = [
            r'^(\d+\.?\s*[^\n]+)$',  # 数字标题
            r'^(Abstract|摘要)$',    # 摘要
            r'^(Introduction|引言|前言)$',  # 引言
            r'^(Method|方法|实验方法|材料与方法)$',  # 方法
            r'^(Result|结果|实验结果)$',  # 结果
            r'^(Discussion|讨论)$',  # 讨论
            r'^(Conclusion|结论)$',  # 结论
            r'^(Reference|参考文献)$',  # 参考文献
        ]
        
        lines = text.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检查是否是章节标题
            is_section_header = False
            for pattern in section_patterns:
                if re.match(pattern, line, re.IGNORECASE):
                    is_section_header = True
                    break
            
            if is_section_header:
                # 保存当前章节
                if current_section and current_content:
                    section = Section(
                        id=f"section_{len(sections)}",
                        title=current_section,
                        content='\n'.join(current_content)
                    )
                    sections.append(section)
                
                # 开始新章节
                current_section = line
                current_content = []
            else:
                current_content.append(line)
        
        # 保存最后一个章节
        if current_section and current_content:
            section = Section(
                id=f"section_{len(sections)}",
                title=current_section,
                content='\n'.join(current_content)
            )
            sections.append(section)
        
        return sections
    
    def _extract_metadata(self, text: str, pdf_metadata: Dict) -> DocumentMetadata:
        """提取文档元数据"""
        metadata = DocumentMetadata(title="", language="zh")
        
        # 从PDF元数据提取
        if pdf_metadata:
            metadata.title = pdf_metadata.get('title', '') or ''
            metadata.abstract = pdf_metadata.get('subject', '') or ''
        
        # 从文本提取标题
        if not metadata.title:
            lines = text.split('\n')
            for line in lines[:10]:  # 检查前10行
                line = line.strip()
                if len(line) > 10 and len(line) < 200:
                    metadata.title = line
                    break
        
        # 提取摘要
        if not metadata.abstract:
            abstract_match = re.search(r'(?:Abstract|摘要)[:\s]*(.*?)(?:\n\n|\n[A-Z]|\n\d)', text, re.DOTALL | re.IGNORECASE)
            if abstract_match:
                metadata.abstract = abstract_match.group(1).strip()[:1000]
        
        # 提取关键词
        keywords_match = re.search(r'(?:Keywords|关键词)[:\s]*(.*?)(?:\n\n|\n[A-Z]|\n\d)', text, re.DOTALL | re.IGNORECASE)
        if keywords_match:
            keywords_text = keywords_match.group(1).strip()
            metadata.keywords = [kw.strip() for kw in keywords_text.split(',') if kw.strip()]
        
        # 提取DOI
        doi_match = re.search(r'DOI[:\s]*([0-9.]+/[^\s]+)', text, re.IGNORECASE)
        if doi_match:
            metadata.doi = doi_match.group(1)
        
        return metadata
    
    def _extract_references(self, text: str) -> List[Reference]:
        """提取参考文献"""
        references = []
        
        # 查找参考文献部分
        ref_section_match = re.search(r'(?:Reference|参考文献)[:\s]*(.*)', text, re.DOTALL | re.IGNORECASE)
        if not ref_section_match:
            return references
        
        ref_text = ref_section_match.group(1)
        ref_lines = [line.strip() for line in ref_text.split('\n') if line.strip()]
        
        for i, line in enumerate(ref_lines):
            if len(line) > 20:  # 过滤太短的行
                ref = Reference(
                    id=f"ref_{i}",
                    title=line[:200],  # 截取前200字符作为标题
                    authors=[],
                    raw_text=line
                )
                references.append(ref)
        
        return references
    
    def _latex_to_text(self, latex_content: str) -> str:
        """将LaTeX转换为纯文本"""
        # 移除LaTeX命令
        text = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', latex_content)
        text = re.sub(r'\\[a-zA-Z]+', '', text)
        
        # 移除环境
        text = re.sub(r'\\begin\{[^}]+\}.*?\\end\{[^}]+\}', '', text, flags=re.DOTALL)
        
        # 移除注释
        text = re.sub(r'%.*$', '', text, flags=re.MULTILINE)
        
        # 清理多余空白
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
