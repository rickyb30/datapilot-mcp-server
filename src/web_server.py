"""
Web server wrapper for DataPilot MCP Server.
Provides HTTP/HTTPS endpoints for public hosting.
"""

import asyncio
import json
import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Depends, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn
from dotenv import load_dotenv

from .main import create_server
from .models import SQLQueryRequest, QueryResult

load_dotenv()

# Security
security = HTTPBearer()

class MCPRequest(BaseModel):
    """Request model for MCP tool calls."""
    tool_name: str = Field(..., description="Name of the MCP tool to call")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the tool")

class MCPResponse(BaseModel):
    """Response model for MCP tool calls."""
    success: bool = Field(..., description="Whether the operation was successful")
    result: Optional[Any] = Field(None, description="Result data if successful")
    error: Optional[str] = Field(None, description="Error message if failed")

class ServerInfo(BaseModel):
    """Server information model."""
    name: str
    version: str
    description: str
    tools: List[str]
    resources: List[str]
    prompts: List[str]

# Initialize FastAPI app
app = FastAPI(
    title="DataPilot MCP Server",
    description="Navigate your Snowflake data with AI guidance - Web API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global MCP server instance
mcp_server = None

async def get_mcp_server():
    """Get or create MCP server instance."""
    global mcp_server
    if mcp_server is None:
        mcp_server = create_server()
    return mcp_server

def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """Verify API key authentication."""
    api_key = os.getenv("API_KEY")
    if not api_key:
        # If no API key is set, allow all requests (for development)
        return "development"
    
    if credentials.credentials != api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint."""
    return {
        "name": "DataPilot MCP Server",
        "description": "Navigate your Snowflake data with AI guidance",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        server = await get_mcp_server()
        return {
            "status": "healthy",
            "server": server.name,
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.get("/info", response_model=ServerInfo)
async def get_server_info(api_key: str = Depends(verify_api_key)):
    """Get server information and available tools."""
    try:
        server = await get_mcp_server()
        
        # Extract tool names
        tools = [tool.name for tool in server._tools] if hasattr(server, '_tools') else []
        resources = [resource.uri for resource in server._resources] if hasattr(server, '_resources') else []
        prompts = [prompt.name for prompt in server._prompts] if hasattr(server, '_prompts') else []
        
        return ServerInfo(
            name=server.name,
            version="0.1.0",
            description="Navigate your Snowflake data with AI guidance",
            tools=tools,
            resources=resources,
            prompts=prompts
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get server info: {str(e)}")

@app.post("/tools/{tool_name}", response_model=MCPResponse)
async def call_tool(
    tool_name: str,
    parameters: Dict[str, Any] = None,
    api_key: str = Depends(verify_api_key)
):
    """Call an MCP tool."""
    try:
        server = await get_mcp_server()
        
        # Find the tool
        tool = None
        if hasattr(server, '_tools'):
            for t in server._tools:
                if t.name == tool_name:
                    tool = t
                    break
        
        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
        
        # Call the tool
        if parameters is None:
            parameters = {}
        
        result = await tool.handler(**parameters)
        
        return MCPResponse(
            success=True,
            result=result
        )
    except Exception as e:
        return MCPResponse(
            success=False,
            error=str(e)
        )

@app.post("/mcp/call", response_model=MCPResponse)
async def call_mcp_tool(
    request: MCPRequest,
    api_key: str = Depends(verify_api_key)
):
    """Generic MCP tool call endpoint."""
    return await call_tool(request.tool_name, request.parameters, api_key)

@app.get("/tools")
async def list_tools(api_key: str = Depends(verify_api_key)):
    """List all available tools."""
    try:
        server = await get_mcp_server()
        tools = []
        
        if hasattr(server, '_tools'):
            for tool in server._tools:
                tools.append({
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.input_schema.get("properties", {}) if hasattr(tool, 'input_schema') else {}
                })
        
        return {"tools": tools}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tools: {str(e)}")

@app.get("/resources")
async def list_resources(api_key: str = Depends(verify_api_key)):
    """List all available resources."""
    try:
        server = await get_mcp_server()
        resources = []
        
        if hasattr(server, '_resources'):
            for resource in server._resources:
                resources.append({
                    "uri": resource.uri,
                    "name": resource.name or "",
                    "description": resource.description or ""
                })
        
        return {"resources": resources}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list resources: {str(e)}")

@app.get("/prompts")
async def list_prompts(api_key: str = Depends(verify_api_key)):
    """List all available prompts."""
    try:
        server = await get_mcp_server()
        prompts = []
        
        if hasattr(server, '_prompts'):
            for prompt in server._prompts:
                prompts.append({
                    "name": prompt.name,
                    "description": prompt.description or "",
                    "arguments": prompt.arguments or []
                })
        
        return {"prompts": prompts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list prompts: {str(e)}")

# Convenience endpoints for common operations
@app.post("/sql/execute")
async def execute_sql(
    query: str,
    database: Optional[str] = None,
    schema: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    """Execute SQL query."""
    return await call_tool("execute_sql", {
        "query": query,
        "database": database,
        "schema": schema
    }, api_key)

@app.post("/sql/natural")
async def natural_language_to_sql(
    question: str,
    database: Optional[str] = None,
    schema: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    """Convert natural language to SQL."""
    return await call_tool("natural_language_to_sql", {
        "question": question,
        "database": database,
        "schema": schema
    }, api_key)

@app.get("/databases")
async def list_databases(api_key: str = Depends(verify_api_key)):
    """List all databases."""
    return await call_tool("list_databases", {}, api_key)

@app.get("/tables/{database}")
async def list_tables(
    database: str,
    schema: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    """List tables in database."""
    return await call_tool("list_tables", {
        "database": database,
        "schema": schema
    }, api_key)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        "src.web_server:app",
        host=host,
        port=port,
        reload=os.getenv("ENVIRONMENT") == "development"
    ) 