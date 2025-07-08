from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class SnowflakeConnection(BaseModel):
    """Snowflake connection configuration"""
    account: str
    user: str
    password: str
    warehouse: Optional[str] = None
    database: Optional[str] = None
    schema: Optional[str] = None
    role: Optional[str] = None


class SQLQueryRequest(BaseModel):
    """Request model for SQL query execution"""
    query: str = Field(..., description="SQL query to execute")
    limit: Optional[int] = Field(None, description="Maximum number of rows to return")
    warehouse: Optional[str] = Field(None, description="Warehouse to use for this query")


class TableInfo(BaseModel):
    """Information about a Snowflake table"""
    table_name: str
    schema_name: str
    database_name: str
    table_type: str
    row_count: Optional[int] = None
    bytes: Optional[int] = None
    comment: Optional[str] = None


class ColumnInfo(BaseModel):
    """Information about a table column"""
    column_name: str
    data_type: str
    is_nullable: bool
    default_value: Optional[str] = None
    comment: Optional[str] = None


class QueryResult(BaseModel):
    """Result of a SQL query execution"""
    success: bool
    data: List[Dict[str, Any]]
    columns: List[str]
    row_count: int
    execution_time_ms: Optional[int] = None
    query_id: Optional[str] = None
    warehouse_used: Optional[str] = None
    error: Optional[str] = None


class NaturalLanguageRequest(BaseModel):
    """Request for natural language to SQL conversion"""
    question: str = Field(..., description="Natural language question about the data")
    context: Optional[str] = Field(None, description="Additional context about tables/schema")
    database: Optional[str] = Field(None, description="Database to query")
    schema: Optional[str] = Field(None, description="Schema to query")


class DataAnalysisRequest(BaseModel):
    """Request for AI-powered data analysis"""
    table_name: str = Field(..., description="Table to analyze")
    analysis_type: str = Field(..., description="Type of analysis to perform")
    columns: Optional[List[str]] = Field(None, description="Specific columns to analyze")
    filters: Optional[Dict[str, Any]] = Field(None, description="Filters to apply") 