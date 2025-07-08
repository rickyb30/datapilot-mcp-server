"""Tests for the main module."""

import pytest
from unittest.mock import Mock, patch
import os
import sys

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.main import create_server
from src.models import SnowflakeConnection


class TestMain:
    """Test cases for main module."""
    
    @patch.dict(os.environ, {
        'SNOWFLAKE_ACCOUNT': 'test_account',
        'SNOWFLAKE_USER': 'test_user',
        'SNOWFLAKE_PASSWORD': 'test_password',
        'OPENAI_API_KEY': 'test_key'
    })
    def test_create_server_returns_server_instance(self):
        """Test that create_server returns a server instance."""
        server = create_server()
        assert server is not None
        assert hasattr(server, 'name')
        assert server.name == "datapilot"
    
    @patch.dict(os.environ, {
        'SNOWFLAKE_ACCOUNT': 'test_account',
        'SNOWFLAKE_USER': 'test_user',
        'SNOWFLAKE_PASSWORD': 'test_password',
        'OPENAI_API_KEY': 'test_key'
    })
    def test_snowflake_connection_from_env(self):
        """Test creating Snowflake connection from environment variables."""
        # Test that we can create a connection object
        conn = SnowflakeConnection(
            account='test_account',
            user='test_user',
            password='test_password'
        )
        assert conn.account == 'test_account'
        assert conn.user == 'test_user'
        assert conn.password == 'test_password'
    
    def test_snowflake_connection_validation(self):
        """Test Snowflake connection validation."""
        # Test required fields
        with pytest.raises(Exception):
            SnowflakeConnection()
        
        # Test valid connection
        conn = SnowflakeConnection(
            account='test_account',
            user='test_user',
            password='test_password'
        )
        assert conn.account == 'test_account'
        assert conn.user == 'test_user'
        assert conn.password == 'test_password'
    
    @patch.dict(os.environ, {
        'SNOWFLAKE_ACCOUNT': 'test_account',
        'SNOWFLAKE_USER': 'test_user',
        'SNOWFLAKE_PASSWORD': 'test_password',
        'OPENAI_API_KEY': 'test_key'
    })
    def test_server_has_required_capabilities(self):
        """Test that server has all required capabilities."""
        server = create_server()
        
        # Check that server has tools
        assert hasattr(server, '_tools')
        assert len(server._tools) > 0
        
        # Check for key tools
        tool_names = [tool.name for tool in server._tools]
        expected_tools = [
            'execute_sql',
            'list_databases',
            'list_schemas',
            'list_tables',
            'natural_language_to_sql'
        ]
        
        for tool_name in expected_tools:
            assert tool_name in tool_names, f"Tool {tool_name} not found in server tools"
    
    def test_imports_work(self):
        """Test that basic imports work correctly."""
        # This should not raise any exceptions
        from src.main import create_server
        from src.models import SnowflakeConnection
        from src.snowflake_client import SnowflakeClient
        from src.openai_client import OpenAIClient
        
        assert create_server is not None
        assert SnowflakeConnection is not None
        assert SnowflakeClient is not None
        assert OpenAIClient is not None


@pytest.mark.asyncio
class TestAsyncOperations:
    """Test cases for async operations."""
    
    async def test_async_functionality_exists(self):
        """Test that async functionality is properly set up."""
        # This is a placeholder test to ensure async testing works
        assert True


if __name__ == "__main__":
    pytest.main([__file__]) 