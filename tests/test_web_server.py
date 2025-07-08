"""Tests for the web server module."""

import pytest
from unittest.mock import Mock, patch
import os
import sys

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient


class TestWebServer:
    """Test cases for web server module."""
    
    def test_imports_work(self):
        """Test that web server imports work correctly."""
        # This should not raise any exceptions
        from src.web_server import app
        assert app is not None
    
    @patch.dict(os.environ, {
        'SNOWFLAKE_ACCOUNT': 'test_account',
        'SNOWFLAKE_USER': 'test_user',
        'SNOWFLAKE_PASSWORD': 'test_password',
        'OPENAI_API_KEY': 'test_key'
    })
    def test_web_server_starts(self):
        """Test that web server can be started."""
        from src.web_server import app
        
        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["name"] == "DataPilot MCP Server"
    
    @patch.dict(os.environ, {
        'SNOWFLAKE_ACCOUNT': 'test_account',
        'SNOWFLAKE_USER': 'test_user',
        'SNOWFLAKE_PASSWORD': 'test_password',
        'OPENAI_API_KEY': 'test_key'
    })
    def test_health_endpoint(self):
        """Test that health endpoint works."""
        from src.web_server import app
        
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


if __name__ == "__main__":
    pytest.main([__file__]) 