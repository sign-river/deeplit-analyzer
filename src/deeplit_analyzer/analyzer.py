"""Core analyzer functionality for DeepLit."""

import json
from typing import Dict, List, Optional, Any
import requests
from .config import Config


class DeepLitAnalyzer:
    """Main analyzer class for processing academic literature."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the analyzer with configuration."""
        self.config = config or Config.load()
        if not self.config.validate_api_key():
            raise ValueError("DeepSeek API key is required. Set DEEPSEEK_API_KEY environment variable.")
    
    def _make_api_request(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Make a request to DeepSeek API."""
        headers = {
            "Authorization": f"Bearer {self.config.deepseek_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature
        }
        
        response = requests.post(
            f"{self.config.deepseek_base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    
    def generate_abstract(self, paper_text: str) -> str:
        """Generate an abstract from paper text."""
        messages = [
            {
                "role": "system",
                "content": "You are an expert academic literature analyzer. Generate a concise, informative abstract that captures the key points, methodology, and conclusions of the academic paper."
            },
            {
                "role": "user", 
                "content": f"Please generate an abstract for the following academic paper:\n\n{paper_text[:4000]}..."
            }
        ]
        
        response = self._make_api_request(messages)
        return response["choices"][0]["message"]["content"]
    
    def summarize_section(self, section_text: str, section_title: str = "") -> str:
        """Summarize a specific section of a paper."""
        title_context = f" (Section: {section_title})" if section_title else ""
        
        messages = [
            {
                "role": "system",
                "content": "You are an expert academic literature analyzer. Provide a clear, concise summary of the given section, highlighting key points, findings, and implications."
            },
            {
                "role": "user",
                "content": f"Please summarize the following section{title_context}:\n\n{section_text}"
            }
        ]
        
        response = self._make_api_request(messages)
        return response["choices"][0]["message"]["content"]
    
    def extract_key_points(self, paper_text: str) -> List[str]:
        """Extract key points from the paper."""
        messages = [
            {
                "role": "system", 
                "content": "You are an expert academic literature analyzer. Extract the most important key points from the paper as a JSON list of strings. Focus on novel contributions, methodology, findings, and implications."
            },
            {
                "role": "user",
                "content": f"Extract key points from this paper as a JSON list:\n\n{paper_text[:6000]}..."
            }
        ]
        
        response = self._make_api_request(messages)
        content = response["choices"][0]["message"]["content"]
        
        try:
            # Try to parse as JSON
            return json.loads(content)
        except json.JSONDecodeError:
            # Fallback: split by lines and clean up
            lines = content.strip().split('\n')
            return [line.strip('- ').strip() for line in lines if line.strip()]
    
    def analyze_paper(self, paper_text: str) -> Dict[str, Any]:
        """Perform complete analysis of a paper."""
        try:
            abstract = self.generate_abstract(paper_text)
            key_points = self.extract_key_points(paper_text)
            
            return {
                "abstract": abstract,
                "key_points": key_points,
                "analysis_complete": True,
                "error": None
            }
        except Exception as e:
            return {
                "abstract": None,
                "key_points": [],
                "analysis_complete": False,
                "error": str(e)
            }