"""Tests for configuration module."""

import os
import pytest
from deeplit_analyzer.config import Config


def test_config_default_values():
    """Test default configuration values."""
    config = Config()
    
    assert config.deepseek_base_url == "https://api.deepseek.com/v1"
    assert config.max_tokens == 2000
    assert config.temperature == 0.3
    assert config.output_format == "markdown"
    assert config.include_evidence is True


def test_config_api_key_validation():
    """Test API key validation."""
    # Test with no API key
    config = Config(deepseek_api_key=None)
    assert not config.validate_api_key()
    
    # Test with empty API key
    config = Config(deepseek_api_key="")
    assert not config.validate_api_key()
    
    # Test with whitespace API key
    config = Config(deepseek_api_key="   ")
    assert not config.validate_api_key()
    
    # Test with valid API key
    config = Config(deepseek_api_key="test-key")
    assert config.validate_api_key()


def test_config_load():
    """Test configuration loading."""
    config = Config.load()
    assert isinstance(config, Config)