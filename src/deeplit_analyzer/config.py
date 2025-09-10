"""Configuration management for DeepLit Analyzer."""

import os
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config(BaseModel):
    """Configuration settings for DeepLit Analyzer."""
    
    # API Configuration
    deepseek_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("DEEPSEEK_API_KEY"),
        description="DeepSeek API key for literature analysis"
    )
    deepseek_base_url: str = Field(
        default="https://api.deepseek.com/v1",
        description="Base URL for DeepSeek API"
    )
    
    # Analysis Configuration
    max_tokens: int = Field(
        default=2000,
        description="Maximum tokens for API responses"
    )
    temperature: float = Field(
        default=0.3,
        description="Temperature for text generation (0.0-1.0)"
    )
    
    # Output Configuration
    output_format: str = Field(
        default="markdown",
        description="Output format (markdown, json, txt)"
    )
    include_evidence: bool = Field(
        default=True,
        description="Whether to include evidence references"
    )
    
    class Config:
        env_prefix = "DEEPLIT_"
        
    @classmethod
    def load(cls) -> "Config":
        """Load configuration from environment variables and defaults."""
        return cls()
    
    def validate_api_key(self) -> bool:
        """Validate that API key is configured."""
        return self.deepseek_api_key is not None and len(self.deepseek_api_key.strip()) > 0