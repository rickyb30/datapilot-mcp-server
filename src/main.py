"""
DataPilot MCP Server
A comprehensive MCP server for interacting with Snowflake using natural language and AI.
Navigate your data with AI guidance.
"""

import asyncio
import logging
import os
from typing import List, Dict, Any, Optional
from fastmcp import FastMCP, Context
from dotenv import load_dotenv

from src.models import (
    SnowflakeConnection, SQLQueryRequest, NaturalLanguageRequest, 
    DataAnalysisRequest, QueryResult, TableInfo, ColumnInfo
)
from src.snowflake_client import SnowflakeClient
from src.openai_client import OpenAIClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("DataPilot")

# Global clients (will be initialized on first use)
snowflake_client: Optional[SnowflakeClient] = None
openai_client: Optional[OpenAIClient] = None


async def get_snowflake_client() -> SnowflakeClient:
    """Get or initialize Snowflake client"""
    global snowflake_client
    if snowflake_client is None:
        config = SnowflakeConnection(
            account=os.getenv("SNOWFLAKE_ACCOUNT"),
            user=os.getenv("SNOWFLAKE_USER"),
            password=os.getenv("SNOWFLAKE_PASSWORD"),
            warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
            database=os.getenv("SNOWFLAKE_DATABASE"),
            schema=os.getenv("SNOWFLAKE_SCHEMA"),
            role=os.getenv("SNOWFLAKE_ROLE")
        )
        snowflake_client = SnowflakeClient(config)
        await snowflake_client.connect()
    return snowflake_client


async def get_openai_client() -> OpenAIClient:
    """Get or initialize OpenAI client"""
    global openai_client
    if openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        model = os.getenv("OPENAI_MODEL", "gpt-4")
        openai_client = OpenAIClient(api_key, model)
    return openai_client


# =============================================================================
# CORE DATABASE OPERATIONS - TOOLS
# =============================================================================

@mcp.tool()
async def execute_sql(request: SQLQueryRequest, ctx: Context) -> QueryResult:
    """Execute a SQL query on Snowflake and return results"""
    await ctx.info(f"Executing SQL query: {request.query[:100]}...")
    
    try:
        client = await get_snowflake_client()
        result = await client.execute_query(
            request.query, 
            request.limit, 
            request.warehouse
        )
        
        if result.success:
            await ctx.info(f"Query executed successfully. {result.row_count} rows returned.")
        else:
            await ctx.error(f"Query failed: {result.error}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error executing SQL: {str(e)}")
        await ctx.error(f"Failed to execute query: {str(e)}")
        return QueryResult(
            success=False,
            data=[],
            columns=[],
            row_count=0,
            error=str(e)
        )


@mcp.tool()
async def list_databases(ctx: Context) -> List[str]:
    """List all databases available to the user"""
    await ctx.info("Retrieving list of databases...")
    
    try:
        client = await get_snowflake_client()
        databases = await client.list_databases()
        await ctx.info(f"Found {len(databases)} databases")
        return databases
        
    except Exception as e:
        logger.error(f"Error listing databases: {str(e)}")
        await ctx.error(f"Failed to list databases: {str(e)}")
        return []


@mcp.tool()
async def list_schemas(database: str, ctx: Context) -> List[str]:
    """List all schemas in a database"""
    await ctx.info(f"Retrieving schemas for database: {database}")
    
    try:
        client = await get_snowflake_client()
        schemas = await client.list_schemas(database)
        await ctx.info(f"Found {len(schemas)} schemas in {database}")
        return schemas
        
    except Exception as e:
        logger.error(f"Error listing schemas: {str(e)}")
        await ctx.error(f"Failed to list schemas: {str(e)}")
        return []


@mcp.tool()
async def list_tables(database: Optional[str] = None, schema: Optional[str] = None, ctx: Context = None) -> List[Dict[str, Any]]:
    """List all tables in a database/schema"""
    context_msg = f"Retrieving tables"
    if database:
        context_msg += f" from database: {database}"
    if schema:
        context_msg += f", schema: {schema}"
    
    await ctx.info(context_msg)
    
    try:
        client = await get_snowflake_client()
        tables = await client.list_tables(database, schema)
        
        # Convert to dict for JSON serialization
        result = []
        for table in tables:
            result.append({
                "table_name": table.table_name,
                "schema_name": table.schema_name,
                "database_name": table.database_name,
                "table_type": table.table_type,
                "row_count": table.row_count,
                "bytes": table.bytes,
                "comment": table.comment
            })
        
        await ctx.info(f"Found {len(result)} tables")
        return result
        
    except Exception as e:
        logger.error(f"Error listing tables: {str(e)}")
        await ctx.error(f"Failed to list tables: {str(e)}")
        return []


@mcp.tool()
async def describe_table(table_name: str, database: Optional[str] = None, schema: Optional[str] = None, ctx: Context = None) -> List[Dict[str, Any]]:
    """Get detailed information about a table's columns"""
    await ctx.info(f"Describing table: {table_name}")
    
    try:
        client = await get_snowflake_client()
        columns = await client.describe_table(table_name, database, schema)
        
        # Convert to dict for JSON serialization
        result = []
        for col in columns:
            result.append({
                "column_name": col.column_name,
                "data_type": col.data_type,
                "is_nullable": col.is_nullable,
                "default_value": col.default_value,
                "comment": col.comment
            })
        
        await ctx.info(f"Table {table_name} has {len(result)} columns")
        return result
        
    except Exception as e:
        logger.error(f"Error describing table: {str(e)}")
        await ctx.error(f"Failed to describe table: {str(e)}")
        return []


@mcp.tool()
async def get_table_sample(table_name: str, limit: int = 10, ctx: Context = None) -> QueryResult:
    """Get a sample of data from a table"""
    await ctx.info(f"Getting sample data from table: {table_name} (limit: {limit})")
    
    try:
        client = await get_snowflake_client()
        result = await client.get_table_sample(table_name, limit)
        
        if result.success:
            await ctx.info(f"Retrieved {result.row_count} sample rows")
        else:
            await ctx.error(f"Failed to get sample: {result.error}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting table sample: {str(e)}")
        await ctx.error(f"Failed to get table sample: {str(e)}")
        return QueryResult(
            success=False,
            data=[],
            columns=[],
            row_count=0,
            error=str(e)
        )


# =============================================================================
# WAREHOUSE MANAGEMENT - TOOLS
# =============================================================================

@mcp.tool()
async def list_warehouses(ctx: Context) -> List[Dict[str, Any]]:
    """List all warehouses available to the user"""
    await ctx.info("Retrieving list of warehouses...")
    
    try:
        client = await get_snowflake_client()
        warehouses = await client.list_warehouses()
        await ctx.info(f"Found {len(warehouses)} warehouses")
        return warehouses
        
    except Exception as e:
        logger.error(f"Error listing warehouses: {str(e)}")
        await ctx.error(f"Failed to list warehouses: {str(e)}")
        return []


@mcp.tool()
async def get_warehouse_status(ctx: Context) -> Dict[str, Any]:
    """Get current warehouse, database, and schema status"""
    await ctx.info("Getting current warehouse status...")
    
    try:
        client = await get_snowflake_client()
        status = await client.get_warehouse_status()
        await ctx.info("Retrieved warehouse status")
        return status
        
    except Exception as e:
        logger.error(f"Error getting warehouse status: {str(e)}")
        await ctx.error(f"Failed to get warehouse status: {str(e)}")
        return {}


# =============================================================================
# AI-POWERED FEATURES - TOOLS
# =============================================================================

@mcp.tool()
async def natural_language_to_sql(request: NaturalLanguageRequest, ctx: Context) -> str:
    """Convert natural language question to SQL query using AI"""
    await ctx.info(f"Converting natural language to SQL: {request.question}")
    
    try:
        openai = await get_openai_client()
        
        # Get schema context for better SQL generation
        table_schemas = []
        if request.database or request.schema:
            snowflake = await get_snowflake_client()
            tables = await snowflake.list_tables(request.database, request.schema)
            
            for table in tables[:5]:  # Limit to first 5 tables for context
                columns = await snowflake.describe_table(
                    table.table_name, 
                    request.database or table.database_name,
                    request.schema or table.schema_name
                )
                table_schemas.append({
                    'table_name': table.table_name,
                    'columns': [{'name': col.column_name, 'type': col.data_type} for col in columns]
                })
        
        sql_query = await openai.natural_language_to_sql(request, table_schemas)
        await ctx.info("Successfully generated SQL query")
        return sql_query
        
    except Exception as e:
        logger.error(f"Error converting to SQL: {str(e)}")
        await ctx.error(f"Failed to convert to SQL: {str(e)}")
        raise


@mcp.tool()
async def analyze_query_results(query: str, results_limit: int = 100, analysis_type: str = "summary", ctx: Context = None) -> str:
    """Execute a query and analyze its results using AI"""
    await ctx.info(f"Analyzing query results for: {query[:100]}...")
    
    try:
        # Execute the query first
        snowflake = await get_snowflake_client()
        result = await snowflake.execute_query(query, results_limit)
        
        if not result.success:
            await ctx.error(f"Query failed: {result.error}")
            return f"Query execution failed: {result.error}"
        
        # Analyze the results
        openai = await get_openai_client()
        analysis = await openai.analyze_query_results(query, result.data, analysis_type)
        
        await ctx.info("Successfully analyzed query results")
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing query results: {str(e)}")
        await ctx.error(f"Failed to analyze query results: {str(e)}")
        raise


@mcp.tool()
async def suggest_query_optimizations(query: str, ctx: Context) -> str:
    """Get AI-powered suggestions for optimizing a SQL query"""
    await ctx.info(f"Analyzing query for optimization: {query[:100]}...")
    
    try:
        openai = await get_openai_client()
        optimizations = await openai.suggest_optimizations(query)
        await ctx.info("Generated optimization suggestions")
        return optimizations
        
    except Exception as e:
        logger.error(f"Error suggesting optimizations: {str(e)}")
        await ctx.error(f"Failed to suggest optimizations: {str(e)}")
        raise


@mcp.tool()
async def explain_query(query: str, ctx: Context) -> str:
    """Explain what a SQL query does in plain English"""
    await ctx.info(f"Explaining query: {query[:100]}...")
    
    try:
        openai = await get_openai_client()
        explanation = await openai.explain_query(query)
        await ctx.info("Generated query explanation")
        return explanation
        
    except Exception as e:
        logger.error(f"Error explaining query: {str(e)}")
        await ctx.error(f"Failed to explain query: {str(e)}")
        raise


@mcp.tool()
async def generate_table_insights(table_name: str, sample_limit: int = 20, ctx: Context = None) -> str:
    """Generate AI-powered insights about a table's data"""
    await ctx.info(f"Generating insights for table: {table_name}")
    
    try:
        snowflake = await get_snowflake_client()
        
        # Get table schema
        columns = await snowflake.describe_table(table_name)
        
        # Get sample data
        sample_result = await snowflake.get_table_sample(table_name, sample_limit)
        
        if not sample_result.success:
            await ctx.error(f"Failed to get sample data: {sample_result.error}")
            return f"Failed to get sample data: {sample_result.error}"
        
        # Generate insights
        openai = await get_openai_client()
        insights = await openai.generate_data_insights(table_name, columns, sample_result.data)
        
        await ctx.info(f"Generated insights for table {table_name}")
        return insights
        
    except Exception as e:
        logger.error(f"Error generating table insights: {str(e)}")
        await ctx.error(f"Failed to generate table insights: {str(e)}")
        raise


# =============================================================================
# RESOURCES - DATA ACCESS
# =============================================================================

@mcp.resource("snowflake://databases")
async def get_databases_resource() -> List[str]:
    """Resource to get list of databases"""
    try:
        client = await get_snowflake_client()
        return await client.list_databases()
    except Exception as e:
        logger.error(f"Error getting databases resource: {str(e)}")
        return []


@mcp.resource("snowflake://schemas/{database}")
async def get_schemas_resource(database: str) -> List[str]:
    """Resource to get list of schemas in a database"""
    try:
        client = await get_snowflake_client()
        return await client.list_schemas(database)
    except Exception as e:
        logger.error(f"Error getting schemas resource: {str(e)}")
        return []


@mcp.resource("snowflake://tables/{database}/{schema}")
async def get_tables_resource(database: str, schema: str) -> List[Dict[str, Any]]:
    """Resource to get list of tables in a database/schema"""
    try:
        client = await get_snowflake_client()
        tables = await client.list_tables(database, schema)
        return [
            {
                "table_name": table.table_name,
                "schema_name": table.schema_name,
                "database_name": table.database_name,
                "table_type": table.table_type,
                "row_count": table.row_count,
                "bytes": table.bytes,
                "comment": table.comment
            }
            for table in tables
        ]
    except Exception as e:
        logger.error(f"Error getting tables resource: {str(e)}")
        return []


@mcp.resource("snowflake://table/{database}/{schema}/{table}")
async def get_table_info_resource(database: str, schema: str, table: str) -> Dict[str, Any]:
    """Resource to get detailed information about a specific table"""
    try:
        client = await get_snowflake_client()
        columns = await client.describe_table(table, database, schema)
        sample = await client.get_table_sample(f"{database}.{schema}.{table}", 5)
        
        return {
            "table_name": table,
            "database": database,
            "schema": schema,
            "columns": [
                {
                    "column_name": col.column_name,
                    "data_type": col.data_type,
                    "is_nullable": col.is_nullable,
                    "default_value": col.default_value,
                    "comment": col.comment
                }
                for col in columns
            ],
            "sample_data": sample.data if sample.success else [],
            "column_count": len(columns)
        }
    except Exception as e:
        logger.error(f"Error getting table info resource: {str(e)}")
        return {}


# =============================================================================
# PROMPTS - REUSABLE TEMPLATES
# =============================================================================

@mcp.prompt()
async def sql_analysis_prompt(query: str, context: str = "") -> str:
    """Generate a prompt for analyzing SQL query results"""
    return f"""
Analyze the following SQL query and its results:

Query: {query}

Context: {context}

Please provide:
1. A summary of what the query does
2. Key insights from the results
3. Any patterns or anomalies you notice
4. Recommendations for further analysis

Format your response in a clear, structured way that would be helpful for a business user.
"""


@mcp.prompt()
async def data_exploration_prompt(table_name: str, business_context: str = "") -> str:
    """Generate a prompt for exploring a data table"""
    return f"""
You are a data analyst exploring the table: {table_name}

Business context: {business_context}

Please analyze this table and provide:
1. Data quality assessment
2. Key business insights
3. Potential use cases for this data
4. Recommended queries for further analysis
5. Any data quality issues or concerns

Focus on actionable insights that would be valuable for business decision-making.
"""


@mcp.prompt()
async def sql_optimization_prompt(query: str, performance_context: str = "") -> str:
    """Generate a prompt for SQL query optimization"""
    return f"""
Analyze the following SQL query for optimization opportunities:

Query: {query}

Performance context: {performance_context}

Please provide:
1. Performance analysis of the current query
2. Specific optimization recommendations
3. Snowflake-specific optimizations (clustering, materialized views, etc.)
4. Warehouse sizing recommendations
5. Estimated performance improvement

Focus on practical, implementable optimizations that will have measurable impact.
"""


# =============================================================================
# SERVER LIFECYCLE
# =============================================================================

async def cleanup():
    """Cleanup resources on server shutdown"""
    global snowflake_client
    if snowflake_client:
        await snowflake_client.disconnect()
        logger.info("Snowflake connection closed")


def create_server():
    """Create and return the MCP server instance"""
    return mcp


def main():
    """Main entry point for the MCP server"""
    print("🚀 Starting DataPilot MCP Server...")
    print("📊 Core Database Operations:")
    print("   - execute_sql - Execute SQL queries")
    print("   - list_databases - List available databases")
    print("   - list_schemas - List schemas in a database")
    print("   - list_tables - List tables in a database/schema")
    print("   - describe_table - Get table column information")
    print("   - get_table_sample - Get sample data from a table")
    print("🏭 Warehouse Management:")
    print("   - list_warehouses - List available warehouses")
    print("   - get_warehouse_status - Get current warehouse status")
    print("🤖 AI-Powered Features:")
    print("   - natural_language_to_sql - Convert questions to SQL")
    print("   - analyze_query_results - AI analysis of query results")
    print("   - suggest_query_optimizations - SQL optimization suggestions")
    print("   - explain_query - Plain English query explanations")
    print("   - generate_table_insights - AI insights about table data")
    print("📋 Resources:")
    print("   - snowflake://databases - Database list")
    print("   - snowflake://schemas/{database} - Schema list")
    print("   - snowflake://tables/{database}/{schema} - Table list")
    print("   - snowflake://table/{database}/{schema}/{table} - Table details")
    print("📝 Prompts:")
    print("   - sql_analysis_prompt - Analysis templates")
    print("   - data_exploration_prompt - Data exploration templates")
    print("   - sql_optimization_prompt - Optimization templates")
    print("\n✅ Server ready for connections!")
    print("🔧 Make sure to set your environment variables:")
    print("   - SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD")
    print("   - OPENAI_API_KEY")
    print("   - Optional: SNOWFLAKE_WAREHOUSE, SNOWFLAKE_DATABASE, SNOWFLAKE_SCHEMA, SNOWFLAKE_ROLE")
    
    try:
        # Run the server
        mcp.run()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    finally:
        # Cleanup
        asyncio.run(cleanup())


if __name__ == "__main__":
    main() 