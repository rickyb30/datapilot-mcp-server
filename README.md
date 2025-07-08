# DataPilot MCP Server

[![CI/CD Pipeline](https://github.com/rickyb30/datapilot-mcp-server/actions/workflows/ci.yml/badge.svg)](https://github.com/rickyb30/datapilot-mcp-server/actions/workflows/ci.yml)
[![Coverage Status](https://codecov.io/gh/rickyb30/datapilot-mcp-server/branch/main/graph/badge.svg)](https://codecov.io/gh/rickyb30/datapilot-mcp-server)
[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Security: bandit](https://img.shields.io/badge/security-bandit-green.svg)](https://github.com/PyCQA/bandit)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)

Navigate your data with AI guidance. A comprehensive Model Context Protocol (MCP) server for interacting with Snowflake using natural language and AI. Built with FastMCP 2.0 and OpenAI integration.

## Features

### 🗄️ Core Database Operations
- **execute_sql** - Execute SQL queries with results
- **list_databases** - List all accessible databases
- **list_schemas** - List schemas in a database
- **list_tables** - List tables in a database/schema
- **describe_table** - Get detailed table column information
- **get_table_sample** - Retrieve sample data from tables

### 🏭 Warehouse Management
- **list_warehouses** - List all available warehouses
- **get_warehouse_status** - Get current warehouse, database, and schema status

### 🤖 AI-Powered Features
- **natural_language_to_sql** - Convert natural language questions to SQL queries
- **analyze_query_results** - AI-powered analysis of query results
- **suggest_query_optimizations** - Get optimization suggestions for SQL queries
- **explain_query** - Plain English explanations of SQL queries
- **generate_table_insights** - AI-generated insights about table data

### 📊 Resources (Data Access)
- `snowflake://databases` - Access database list
- `snowflake://schemas/{database}` - Access schema list
- `snowflake://tables/{database}/{schema}` - Access table list
- `snowflake://table/{database}/{schema}/{table}` - Access table details

### 📝 Prompts (Templates)
- **sql_analysis_prompt** - Templates for SQL analysis
- **data_exploration_prompt** - Templates for data exploration
- **sql_optimization_prompt** - Templates for query optimization

## Installation

1. **Clone and setup the project:**
   ```bash
   git clone <repository-url>
   cd datapilot
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   ```bash
   cp env.template .env
   # Edit .env with your credentials
   ```

## Configuration

### Environment Variables

Create a `.env` file with the following configuration:

```env
# Required: Snowflake Connection
# Account examples:
# - ACCOUNT-LOCATOR.snowflakecomputing.com (recommended)
# - ACCOUNT-LOCATOR.region.cloud
# - organization-account_name
SNOWFLAKE_ACCOUNT=ACCOUNT-LOCATOR.snowflakecomputing.com
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password

# Optional: Default Snowflake Context
SNOWFLAKE_WAREHOUSE=your_warehouse_name
SNOWFLAKE_DATABASE=your_database_name
SNOWFLAKE_SCHEMA=your_schema_name
SNOWFLAKE_ROLE=your_role_name

# Required: OpenAI API
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4  # Optional, defaults to gpt-4
```

### Snowflake Account Setup

1. **Get your Snowflake account identifier** - Multiple formats supported:
   - **Recommended**: `ACCOUNT-LOCATOR.snowflakecomputing.com` (e.g., `SCGEENJ-UR66679.snowflakecomputing.com`)
   - **Regional**: `ACCOUNT-LOCATOR.region.cloud` (e.g., `xy12345.us-east-1.aws`)
   - **Legacy**: `organization-account_name`

2. Ensure your user has appropriate permissions:
   - `USAGE` on warehouses, databases, and schemas
   - `SELECT` on tables for querying
   - `SHOW` privileges for listing objects

## Usage

### Running the Server

#### Method 1: Direct execution
```bash
python -m src.main
```

#### Method 2: Using FastMCP CLI
```bash
fastmcp run src/main.py
```

#### Method 3: Development mode with auto-reload
```bash
fastmcp dev src/main.py
```

### Connecting to MCP Clients

#### Claude Desktop
Add to your Claude Desktop configuration:
```json
{
  "mcpServers": {
    "datapilot": {
      "command": "python",
      "args": ["-m", "src.main"],
      "cwd": "/path/to/datapilot",
      "env": {
        "SNOWFLAKE_ACCOUNT": "your_account",
        "SNOWFLAKE_USER": "your_user",
        "SNOWFLAKE_PASSWORD": "your_password",
        "OPENAI_API_KEY": "your_openai_key"
      }
    }
  }
}
```

#### Using FastMCP Client
```python
from fastmcp import Client

async def main():
    async with Client("python -m src.main") as client:
        # List databases
        databases = await client.call_tool("list_databases")
        print("Databases:", databases)
        
        # Natural language to SQL
        result = await client.call_tool("natural_language_to_sql", {
            "question": "Show me the top 10 customers by revenue",
            "database": "SALES_DB",
            "schema": "PUBLIC"
        })
        print("Generated SQL:", result)
```

## Example Usage

### 1. Natural Language Query
```python
# Ask a question in natural language
question = "What are the top 5 products by sales volume last month?"
sql = await client.call_tool("natural_language_to_sql", {
    "question": question,
    "database": "SALES_DB",
    "schema": "PUBLIC"
})
print(f"Generated SQL: {sql}")
```

### 2. Execute and Analyze
```python
# Execute a query and get AI analysis
analysis = await client.call_tool("analyze_query_results", {
    "query": "SELECT product_name, SUM(quantity) as total_sales FROM sales GROUP BY product_name ORDER BY total_sales DESC LIMIT 10",
    "results_limit": 100,
    "analysis_type": "summary"
})
print(f"Analysis: {analysis}")
```

### 3. Table Insights
```python
# Get AI-powered insights about a table
insights = await client.call_tool("generate_table_insights", {
    "table_name": "SALES_DB.PUBLIC.CUSTOMERS",
    "sample_limit": 50
})
print(f"Table insights: {insights}")
```

### 4. Query Optimization
```python
# Get optimization suggestions
optimizations = await client.call_tool("suggest_query_optimizations", {
    "query": "SELECT * FROM large_table WHERE date_column > '2023-01-01'"
})
print(f"Optimization suggestions: {optimizations}")
```

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MCP Client    │    │   FastMCP       │    │   Snowflake     │
│   (Claude/etc)  │◄──►│   Server        │◄──►│   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   OpenAI API    │
                       │   (GPT-4)       │
                       └─────────────────┘
```

## Project Structure

```
datapilot/
├── src/
│   ├── __init__.py
│   ├── main.py              # Main FastMCP server
│   ├── models.py            # Pydantic data models
│   ├── snowflake_client.py  # Snowflake connection & operations
│   └── openai_client.py     # OpenAI integration
├── requirements.txt         # Python dependencies
├── env.template            # Environment variables template
└── README.md              # This file
```

## Development

### Adding New Tools

1. Define your tool function in `src/main.py`:
```python
@mcp.tool()
async def my_new_tool(param: str, ctx: Context) -> str:
    """Description of what the tool does"""
    await ctx.info(f"Processing: {param}")
    # Your logic here
    return "result"
```

2. Add appropriate error handling and logging
3. Test with FastMCP dev mode: `fastmcp dev src/main.py`

### Adding New Resources

```python
@mcp.resource("snowflake://my-resource/{param}")
async def my_resource(param: str) -> Dict[str, Any]:
    """Resource description"""
    # Your logic here
    return {"data": "value"}
```

## Troubleshooting

### Common Issues

1. **Connection Errors**
   - Verify Snowflake credentials in `.env`
   - Check network connectivity
   - Ensure user has required permissions

2. **OpenAI Errors**
   - Verify `OPENAI_API_KEY` is set correctly
   - Check API quota and billing
   - Ensure model name is correct

3. **Import Errors**
   - Activate virtual environment
   - Install all requirements: `pip install -r requirements.txt`
   - Run from project root directory

### Logging

Enable debug logging:
```env
LOG_LEVEL=DEBUG
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- Check the troubleshooting section
- Review FastMCP documentation: https://gofastmcp.com/
- Open an issue in the repository 