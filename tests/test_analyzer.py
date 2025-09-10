"""Tests for analyzer module."""

import pytest
from unittest.mock import Mock, patch
from deeplit_analyzer.analyzer import DeepLitAnalyzer
from deeplit_analyzer.config import Config


@pytest.fixture
def mock_config():
    """Mock configuration with valid API key."""
    config = Config(deepseek_api_key="test-key")
    return config


def test_analyzer_init_without_api_key():
    """Test analyzer initialization without API key."""
    config = Config(deepseek_api_key=None)
    
    with pytest.raises(ValueError, match="DeepSeek API key is required"):
        DeepLitAnalyzer(config)


def test_analyzer_init_with_api_key(mock_config):
    """Test analyzer initialization with valid API key."""
    analyzer = DeepLitAnalyzer(mock_config)
    assert analyzer.config == mock_config


@patch('deeplit_analyzer.analyzer.requests.post')
def test_api_request(mock_post, mock_config):
    """Test API request functionality."""
    # Mock response
    mock_response = Mock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Test response"}}]
    }
    mock_post.return_value = mock_response
    
    analyzer = DeepLitAnalyzer(mock_config)
    messages = [{"role": "user", "content": "test"}]
    
    result = analyzer._make_api_request(messages)
    
    assert result["choices"][0]["message"]["content"] == "Test response"
    mock_post.assert_called_once()


def test_analyze_paper_error_handling(mock_config):
    """Test error handling in paper analysis."""
    with patch.object(DeepLitAnalyzer, '_make_api_request') as mock_request:
        mock_request.side_effect = Exception("API Error")
        
        analyzer = DeepLitAnalyzer(mock_config)
        result = analyzer.analyze_paper("test paper")
        
        assert result["analysis_complete"] is False
        assert result["error"] == "API Error"
        assert result["abstract"] is None
        assert result["key_points"] == []