#!/usr/bin/env python3
"""
Azure SQL Database Connector for DBA-GPT
Provides seamless integration with Azure SQL Database
"""

import asyncio
import pyodbc
from azure.identity import DefaultAzureCredential
from typing import List, Dict, Any, Optional
import logging
import json

logger = logging.getLogger(__name__)

class AzureSQLConnection:
    """Azure SQL Database connection wrapper"""
    
    def __init__(self, config: Dict[str, Any]):
        self.server = config.get('server')
        self.database = config.get('database')
        self.authentication = config.get('authentication', 'sql')  # sql, msi, service_principal
        self.port = config.get('port', 1433)
        
        # Authentication setup
        if self.authentication == 'msi':
            # Managed Identity
            self.credential = DefaultAzureCredential()
        elif self.authentication == 'service_principal':
            # Service Principal
            self.tenant_id = config.get('tenant_id')
            self.client_id = config.get('client_id')
            self.client_secret = config.get('client_secret')
            self.credential = DefaultAzureCredential(
                tenant_id=self.tenant_id,
                client_id=self.client_id,
                client_secret=self.client_secret
            )
        else:
            # SQL Authentication
            self.username = config.get('username')
            self.password = config.get('password')
        
        # Connection string components
        self.driver = "{ODBC Driver 17 for SQL Server}"
        self.connection_string = self._build_connection_string()
        
    def _build_connection_string(self) -> str:
        """Build the connection string based on authentication method"""
        if self.authentication == 'sql':
            conn_str = (
                f"DRIVER={self.driver};"
                f"SERVER={self.server};"
                f"DATABASE={self.database};"
                f"UID={self.username};"
                f"PWD={self.password};"
                f"PORT={self.port};"
                "Encrypt=yes;"
                "TrustServerCertificate=no;"
                "Connection Timeout=30;"
            )
        else:
            # Azure AD authentication
            conn_str = (
                f"DRIVER={self.driver};"
                f"SERVER={self.server};"
                f"DATABASE={self.database};"
                f"PORT={self.port};"
                "Authentication=ActiveDirectoryDefault;"
                "Encrypt=yes;"
                "TrustServerCertificate=no;"
                "Connection Timeout=30;"
            )
        
        return conn_str
    
    async def execute_query(self, query: str, **kwargs) -> List[Dict]:
        """Execute Azure SQL query"""
        try:
            logger.info(f"Executing Azure SQL query: {query[:100]}...")
            
            # Execute query in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None, self._execute_sync, query
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Azure SQL query failed: {str(e)}")
            raise Exception(f"Azure SQL query failed: {str(e)}")
    
    def _execute_sync(self, query: str) -> List[Dict]:
        """Execute query synchronously (called from thread pool)"""
        try:
            with pyodbc.connect(self.connection_string) as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                
                # Get column names
                columns = [column[0] for column in cursor.description] if cursor.description else []
                
                # Fetch results
                rows = cursor.fetchall()
                
                # Convert to list of dictionaries
                results = []
                for row in rows:
                    row_dict = {}
                    for i, value in enumerate(row):
                        # Handle special data types
                        if hasattr(value, 'isoformat'):  # datetime objects
                            value = value.isoformat()
                        elif isinstance(value, (bytes, bytearray)):
                            value = value.hex()
                        row_dict[columns[i]] = value
                    results.append(row_dict)
                
                return results
                
        except Exception as e:
            logger.error(f"Sync query execution failed: {str(e)}")
            raise e
    
    async def get_tables(self) -> List[str]:
        """Get list of tables in the database"""
        try:
            query = """
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
            """
            results = await self.execute_query(query)
            return [row['TABLE_NAME'] for row in results]
        except Exception as e:
            logger.error(f"Failed to get tables: {str(e)}")
            return []
    
    async def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Get table schema information"""
        try:
            query = f"""
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                IS_NULLABLE,
                COLUMN_DEFAULT,
                CHARACTER_MAXIMUM_LENGTH,
                NUMERIC_PRECISION,
                NUMERIC_SCALE
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = '{table_name}'
            ORDER BY ORDINAL_POSITION
            """
            results = await self.execute_query(query)
            
            schema = {
                'table_name': table_name,
                'columns': results,
                'total_columns': len(results)
            }
            return schema
        except Exception as e:
            logger.error(f"Failed to get schema for {table_name}: {str(e)}")
            return {'table_name': table_name, 'columns': [], 'total_columns': 0}
    
    async def get_table_stats(self, table_name: str) -> Dict[str, Any]:
        """Get table statistics"""
        try:
            # Get row count
            count_query = f"SELECT COUNT(*) as row_count FROM [{table_name}]"
            count_result = await self.execute_query(count_query)
            row_count = count_result[0]['row_count'] if count_result else 0
            
            # Get table size
            size_query = f"""
            SELECT 
                p.rows as row_count,
                CAST(ROUND((SUM(a.total_pages) * 8) / 1024.00, 2) AS DECIMAL(36, 2)) AS total_space_mb
            FROM sys.tables t
            INNER JOIN sys.indexes i ON t.OBJECT_ID = i.object_id
            INNER JOIN sys.partitions p ON i.object_id = p.OBJECT_ID AND i.index_id = p.index_id
            INNER JOIN sys.allocation_units a ON p.partition_id = a.container_id
            WHERE t.NAME = '{table_name}'
            GROUP BY t.NAME, p.Rows
            """
            size_result = await self.execute_query(size_query)
            
            stats = {
                'table_name': table_name,
                'row_count': row_count,
                'total_space_mb': size_result[0].get('total_space_mb', 0) if size_result else 0
            }
            return stats
        except Exception as e:
            logger.error(f"Failed to get stats for {table_name}: {str(e)}")
            return {'table_name': table_name, 'row_count': 0, 'total_space_mb': 0}
    
    async def get_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """Get table indexes"""
        try:
            query = f"""
            SELECT 
                i.name as index_name,
                i.type_desc as index_type,
                i.is_unique,
                i.is_primary_key,
                STRING_AGG(c.name, ', ') WITHIN GROUP (ORDER BY ic.key_ordinal) as columns
            FROM sys.indexes i
            INNER JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
            INNER JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
            WHERE i.object_id = OBJECT_ID('{table_name}')
            GROUP BY i.name, i.type_desc, i.is_unique, i.is_primary_key
            ORDER BY i.name
            """
            results = await self.execute_query(query)
            return results
        except Exception as e:
            logger.error(f"Failed to get indexes for {table_name}: {str(e)}")
            return []
    
    async def get_database_info(self) -> Dict[str, Any]:
        """Get database information"""
        try:
            query = """
            SELECT 
                DB_NAME() as database_name,
                DATABASEPROPERTYEX(DB_NAME(), 'Status') as status,
                DATABASEPROPERTYEX(DB_NAME(), 'Recovery') as recovery_model,
                DATABASEPROPERTYEX(DB_NAME(), 'UserAccess') as user_access,
                DATABASEPROPERTYEX(DB_NAME(), 'Updateability') as updateability
            """
            results = await self.execute_query(query)
            return results[0] if results else {}
        except Exception as e:
            logger.error(f"Failed to get database info: {str(e)}")
            return {}
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get database performance metrics"""
        try:
            # Get active connections
            connections_query = "SELECT COUNT(*) as active_connections FROM sys.dm_exec_sessions WHERE status = 'running'"
            connections_result = await self.execute_query(connections_query)
            active_connections = connections_result[0]['active_connections'] if connections_result else 0
            
            # Get database size
            size_query = """
            SELECT 
                CAST(ROUND(SUM(size) * 8.0 / 1024, 2) AS DECIMAL(36, 2)) AS database_size_mb
            FROM sys.database_files
            """
            size_result = await self.execute_query(size_query)
            database_size = size_result[0]['database_size_mb'] if size_result else 0
            
            return {
                'active_connections': active_connections,
                'database_size_mb': database_size,
                'timestamp': asyncio.get_event_loop().time()
            }
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {str(e)}")
            return {'error': str(e)}
    
    async def optimize_query(self, query: str) -> str:
        """Optimize SQL for Azure SQL performance"""
        optimized = query
        
        # Add Azure SQL-specific optimizations
        if "SELECT *" in query.upper():
            optimized += " -- Consider selecting only needed columns for better performance"
        
        if "WHERE" in query.upper() and "INDEX" not in query.upper():
            optimized += " -- Ensure WHERE clause columns are indexed"
        
        if "ORDER BY" in query.upper():
            optimized += " -- Consider adding covering indexes for ORDER BY columns"
            
        return optimized
    
    async def close(self):
        """Close the connection"""
        # Connections are managed by context manager, no cleanup needed
        pass
