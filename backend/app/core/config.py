"""
应用配置模块
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用基础配置
    app_name: str = "ScholarMind AI"
    app_version: str = "1.0.0"
    debug: bool = True
    log_level: str = "INFO"
    
    # DeepSeek API配置
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    
    # 数据库配置
    database_url: str = "sqlite:///./scholarmind.db"
    
    # Redis配置
    redis_url: str = "redis://localhost:6379/0"
    
    # 文件存储配置
    upload_dir: str = "./data/uploads"
    processed_dir: str = "./data/processed"
    index_dir: str = "./data/index"
    
    # OCR配置
    tesseract_cmd: Optional[str] = None
    
    # 性能配置
    max_file_size: str = "50MB"
    max_batch_size: int = 100
    ocr_timeout: int = 300
    api_timeout: int = 30
    
    # 安全配置
    secret_key: str = "your_secret_key_here"
    access_token_expire_minutes: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# 创建全局配置实例
settings = Settings()

# 确保目录存在
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.processed_dir, exist_ok=True)
os.makedirs(settings.index_dir, exist_ok=True)
