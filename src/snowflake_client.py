import snowflake.connector
from snowflake.connector import DictCursor
from contextlib import asynccontextmanager
import asyncio
import time
from typing import List, Dict, Any, Optional, AsyncGenerator
import logging
from src.models import SnowflakeConnection, QueryResult, TableInfo, ColumnInfo

logger = logging.getLogger(__name__)


class SnowflakeClient:
    """Async Snowflake client with connection management"""
    
    def __init__(self, connection_config: SnowflakeConnection):
        self.config = connection_config
        self._connection = None
        self._connection_lock = asyncio.Lock()
    
    async def connect(self) -> None:
        """Establish connection to Snowflake"""
        async with self._connection_lock:
            if self._connection is None:
                logger.info("Connecting to Snowflake...")
                self._connection = await asyncio.to_thread(
                    snowflake.connector.connect,
                    account=self.config.account,
                    user=self.config.user,
                    password=self.config.password,
                    warehouse=self.config.warehouse,
                    database=self.config.database,
                    schema=self.config.schema,
                    role=self.config.role
                )
                logger.info("Connected to Snowflake successfully")
    
    async def disconnect(self) -> None:
        """Close connection to Snowflake"""
        async with self._connection_lock:
            if self._connection:
                await asyncio.to_thread(self._connection.close)
                self._connection = None
                logger.info("Disconnected from Snowflake")
    
    @asynccontextmanager
    async def get_cursor(self) -> AsyncGenerator[Any, None]:
        """Context manager for getting a cursor"""
        if not self._connection:
            await self.connect()
        
        cursor = await asyncio.to_thread(self._connection.cursor, DictCursor)
        try:
            yield cursor
        finally:
            await asyncio.to_thread(cursor.close)
    
    async def execute_query(
        self, 
        query: str, 
        limit: Optional[int] = None,
        warehouse: Optional[str] = None
    ) -> QueryResult:
        """Execute a SQL query and return results"""
        start_time = time.time()
        
        try:
            # Switch warehouse if specified
            if warehouse:
                await self._use_warehouse(warehouse)
            
            # Add limit if specified
            if limit and not query.strip().upper().startswith('SELECT'):
                logger.warning("LIMIT can only be applied to SELECT queries")
            elif limit and 'LIMIT' not in query.upper():
                query = f"{query.rstrip(';')} LIMIT {limit}"
            
            async with self.get_cursor() as cursor:
                logger.info(f"Executing query: {query[:100]}...")
                
                await asyncio.to_thread(cursor.execute, query)
                results = await asyncio.to_thread(cursor.fetchall)
                
                # Get column names
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                
                # Convert results to list of dictionaries
                data = []
                for row in results:
                    if isinstance(row, dict):
                        data.append(row)
                    else:
                        data.append(dict(zip(columns, row)))
                
                execution_time_ms = int((time.time() - start_time) * 1000)
                
                return QueryResult(
                    success=True,
                    data=data,
                    columns=columns,
                    row_count=len(data),
                    execution_time_ms=execution_time_ms,
                    query_id=cursor.sfqid if hasattr(cursor, 'sfqid') else None,
                    warehouse_used=warehouse or self.config.warehouse
                )
                
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            return QueryResult(
                success=False,
                data=[],
                columns=[],
                row_count=0,
                execution_time_ms=execution_time_ms,
                error=str(e)
            )
    
    async def _use_warehouse(self, warehouse: str) -> None:
        """Switch to a different warehouse"""
        async with self.get_cursor() as cursor:
            await asyncio.to_thread(cursor.execute, f"USE WAREHOUSE {warehouse}")
    
    async def list_databases(self) -> List[str]:
        """List all databases user has access to"""
        result = await self.execute_query("SHOW DATABASES")
        return [row.get('name', '') for row in result.data if result.success]
    
    async def list_schemas(self, database: str) -> List[str]:
        """List all schemas in a database"""
        result = await self.execute_query(f"SHOW SCHEMAS IN DATABASE {database}")
        return [row.get('name', '') for row in result.data if result.success]
    
    async def list_tables(self, database: Optional[str] = None, schema: Optional[str] = None) -> List[TableInfo]:
        """List all tables in a database/schema"""
        query = "SHOW TABLES"
        if database and schema:
            query += f" IN SCHEMA {database}.{schema}"
        elif database:
            query += f" IN DATABASE {database}"
        
        result = await self.execute_query(query)
        
        tables = []
        for row in result.data:
            if result.success:
                tables.append(TableInfo(
                    table_name=row.get('name', ''),
                    schema_name=row.get('schema_name', ''),
                    database_name=row.get('database_name', ''),
                    table_type=row.get('kind', ''),
                    row_count=row.get('rows'),
                    bytes=row.get('bytes'),
                    comment=row.get('comment')
                ))
        
        return tables
    
    async def describe_table(self, table_name: str, database: Optional[str] = None, schema: Optional[str] = None) -> List[ColumnInfo]:
        """Get detailed information about a table's columns"""
        full_table_name = table_name
        if database and schema:
            full_table_name = f"{database}.{schema}.{table_name}"
        elif schema:
            full_table_name = f"{schema}.{table_name}"
        
        result = await self.execute_query(f"DESCRIBE TABLE {full_table_name}")
        
        columns = []
        for row in result.data:
            if result.success:
                columns.append(ColumnInfo(
                    column_name=row.get('name', ''),
                    data_type=row.get('type', ''),
                    is_nullable=row.get('null?', 'Y') == 'Y',
                    default_value=row.get('default'),
                    comment=row.get('comment')
                ))
        
        return columns
    
    async def get_table_sample(self, table_name: str, limit: int = 10) -> QueryResult:
        """Get a sample of data from a table"""
        query = f"SELECT * FROM {table_name} LIMIT {limit}"
        return await self.execute_query(query)
    
    async def list_warehouses(self) -> List[Dict[str, Any]]:
        """List all warehouses user has access to"""
        result = await self.execute_query("SHOW WAREHOUSES")
        return result.data if result.success else []
    
    async def get_warehouse_status(self) -> Dict[str, Any]:
        """Get current warehouse status"""
        result = await self.execute_query("SELECT CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_SCHEMA()")
        if result.success and result.data:
            row = result.data[0]
            return {
                'current_warehouse': row.get('CURRENT_WAREHOUSE()', ''),
                'current_database': row.get('CURRENT_DATABASE()', ''),
                'current_schema': row.get('CURRENT_SCHEMA()', '')
            }
        return {}
    
    async def analyze_table_stats(self, table_name: str) -> Dict[str, Any]:
        """Get basic statistics about a table"""
        stats_query = f"""
        SELECT 
            COUNT(*) as row_count,
            COUNT(DISTINCT *) as distinct_rows
        FROM {table_name}
        """
        
        result = await self.execute_query(stats_query)
        if result.success and result.data:
            return result.data[0]
        return {} 