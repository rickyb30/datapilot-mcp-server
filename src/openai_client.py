from openai import AsyncOpenAI
import json
import logging
from typing import Dict, Any, List, Optional
from src.models import NaturalLanguageRequest, TableInfo, ColumnInfo

logger = logging.getLogger(__name__)


class OpenAIClient:
    """OpenAI client for natural language processing and AI-powered features"""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
    
    async def natural_language_to_sql(
        self,
        request: NaturalLanguageRequest,
        table_schemas: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Convert natural language question to SQL query"""
        
        # Build context about available tables and schemas
        context = self._build_schema_context(table_schemas)
        
        system_prompt = f"""
        You are a Snowflake SQL expert. Convert natural language questions to SQL queries.
        
        Guidelines:
        - Use proper Snowflake SQL syntax
        - Include appropriate WHERE clauses for filters
        - Use proper JOIN syntax when needed
        - Always include LIMIT clause for safety (default 100)
        - Use uppercase for SQL keywords
        - Be precise with column names and table names
        - Handle date/time functions appropriately for Snowflake
        
        Available schema context:
        {context}
        
        Return only the SQL query without any explanation or markdown formatting.
        """
        
        user_prompt = f"""
        Question: {request.question}
        
        Additional context: {request.context or 'None'}
        Database: {request.database or 'Use current database'}
        Schema: {request.schema or 'Use current schema'}
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            sql_query = response.choices[0].message.content.strip()
            # Remove any markdown formatting
            sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
            
            logger.info(f"Generated SQL query: {sql_query}")
            return sql_query
            
        except Exception as e:
            logger.error(f"Error generating SQL: {str(e)}")
            raise Exception(f"Failed to generate SQL query: {str(e)}")
    
    async def analyze_query_results(
        self,
        query: str,
        results: List[Dict[str, Any]],
        analysis_type: str = "summary"
    ) -> str:
        """Analyze query results using AI"""
        
        # Limit data for analysis to avoid token limits
        sample_data = results[:10] if len(results) > 10 else results
        
        system_prompt = f"""
        You are a data analyst. Analyze the provided query results and provide insights.
        
        Analysis type: {analysis_type}
        
        Provide a clear, concise analysis with:
        - Key findings and patterns
        - Statistical insights if applicable
        - Recommendations or next steps
        - Any anomalies or interesting observations
        
        Format your response in a clear, professional manner.
        """
        
        user_prompt = f"""
        SQL Query: {query}
        
        Results ({len(results)} rows total, showing sample):
        {json.dumps(sample_data, indent=2, default=str)}
        
        Please analyze these results and provide insights.
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            analysis = response.choices[0].message.content.strip()
            logger.info("Generated data analysis")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing data: {str(e)}")
            raise Exception(f"Failed to analyze data: {str(e)}")
    
    async def suggest_optimizations(self, query: str) -> str:
        """Suggest optimizations for a SQL query"""
        
        system_prompt = """
        You are a Snowflake SQL performance expert. Analyze the provided query and suggest optimizations.
        
        Consider:
        - Index usage and clustering keys
        - JOIN optimization
        - WHERE clause efficiency
        - Warehouse sizing recommendations
        - Query structure improvements
        - Snowflake-specific optimizations (clustering, materialized views, etc.)
        
        Provide specific, actionable recommendations.
        """
        
        user_prompt = f"""
        SQL Query to optimize:
        {query}
        
        Please provide optimization suggestions.
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=800
            )
            
            optimization_suggestions = response.choices[0].message.content.strip()
            logger.info("Generated optimization suggestions")
            return optimization_suggestions
            
        except Exception as e:
            logger.error(f"Error generating optimizations: {str(e)}")
            raise Exception(f"Failed to generate optimization suggestions: {str(e)}")
    
    async def explain_query(self, query: str) -> str:
        """Explain what a SQL query does in plain English"""
        
        system_prompt = """
        You are a SQL educator. Explain the provided SQL query in plain English.
        
        Your explanation should:
        - Describe what the query does step by step
        - Explain complex operations in simple terms
        - Mention any important performance considerations
        - Be accessible to both technical and non-technical users
        
        Use clear, friendly language.
        """
        
        user_prompt = f"""
        SQL Query to explain:
        {query}
        
        Please explain what this query does.
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=600
            )
            
            explanation = response.choices[0].message.content.strip()
            logger.info("Generated query explanation")
            return explanation
            
        except Exception as e:
            logger.error(f"Error explaining query: {str(e)}")
            raise Exception(f"Failed to explain query: {str(e)}")
    
    async def generate_data_insights(
        self,
        table_name: str,
        columns: List[ColumnInfo],
        sample_data: List[Dict[str, Any]]
    ) -> str:
        """Generate insights about a table's data"""
        
        # Build column information
        column_info = []
        for col in columns:
            column_info.append({
                'name': col.column_name,
                'type': col.data_type,
                'nullable': col.is_nullable,
                'comment': col.comment
            })
        
        system_prompt = """
        You are a data analyst. Analyze the provided table schema and sample data to generate insights.
        
        Provide:
        - Data quality assessment
        - Patterns and trends in the data
        - Potential use cases for this data
        - Recommendations for analysis
        - Any data quality issues you notice
        
        Be specific and actionable in your insights.
        """
        
        user_prompt = f"""
        Table: {table_name}
        
        Column Schema:
        {json.dumps(column_info, indent=2)}
        
        Sample Data:
        {json.dumps(sample_data, indent=2, default=str)}
        
        Please provide insights about this data.
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.4,
                max_tokens=1000
            )
            
            insights = response.choices[0].message.content.strip()
            logger.info(f"Generated insights for table {table_name}")
            return insights
            
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            raise Exception(f"Failed to generate insights: {str(e)}")
    
    def _build_schema_context(self, table_schemas: Optional[List[Dict[str, Any]]]) -> str:
        """Build context string from table schemas"""
        if not table_schemas:
            return "No schema information available"
        
        context_parts = []
        for schema in table_schemas:
            table_name = schema.get('table_name', 'unknown')
            columns = schema.get('columns', [])
            
            column_list = []
            for col in columns:
                if isinstance(col, dict):
                    col_desc = f"{col.get('name', 'unknown')} ({col.get('type', 'unknown')})"
                else:
                    col_desc = str(col)
                column_list.append(col_desc)
            
            context_parts.append(f"Table {table_name}: {', '.join(column_list)}")
        
        return "\n".join(context_parts) 