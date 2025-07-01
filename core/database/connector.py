"""
Database connector for DBA-GPT
Supports multiple database types with async operations
Enhanced with Auto-Error Resolution System
"""

import asyncio
import asyncpg
import aiomysql
import redis.asyncio as aioredis
from pymongo import MongoClient
from typing import Dict, List, Any, Optional, Callable, Union, Awaitable
from contextlib import asynccontextmanager
import traceback
import re
from datetime import datetime

from core.config import DatabaseConfig
from core.utils.logger import setup_logger

logger = setup_logger(__name__)


class DatabaseError:
    """Structured database error for auto-resolution"""
    def __init__(self, error_type: str, error_code: str, message: str, 
                 query: Optional[str] = None, table: Optional[str] = None, context: Optional[Dict] = None):
        self.error_type = error_type
        self.error_code = error_code
        self.message = message
        self.query = query
        self.table = table
        self.context = context or {}
        self.timestamp = datetime.now()
        
    def to_ai_prompt(self) -> str:
        """Convert error to AI-readable prompt"""
        prompt = f"""
## 🚨 URGENT DATABASE ERROR - IMMEDIATE RESOLUTION NEEDED

**Error Type:** {self.error_type}
**Error Code:** {self.error_code}
**Error Message:** {self.message}
**Timestamp:** {self.timestamp}

"""
        if self.query:
            prompt += f"**Failed Query:** ```sql\n{self.query}\n```\n\n"
        
        if self.table:
            prompt += f"**Affected Table:** {self.table}\n\n"
            
        if self.context:
            prompt += f"**Context:** {self.context}\n\n"
            
        prompt += """
**REQUIRED:** Provide IMMEDIATE step-by-step resolution with:
1. 🔍 Root cause analysis
2. ⚡ Quick fix (SQL commands ready to execute)
3. 🛠️ Detailed resolution steps
4. 🚨 Prevention measures

Format response as actionable DBA commands.
"""
        return prompt


class ErrorAnalyzer:
    """Analyzes database errors and categorizes them"""
    
    @staticmethod
    def analyze_mysql_error(error: Exception, query: str = None) -> DatabaseError:
        """Analyze MySQL errors and create structured error object"""
        error_str = str(error)
        error_code = "UNKNOWN"
        error_type = "GENERAL"
        table_name = None
        
        # Extract MySQL error code
        code_match = re.search(r'\((\d+),', error_str)
        if code_match:
            error_code = code_match.group(1)
            
        # Extract table name from query or error
        if query:
            table_match = re.search(r'(?:FROM|INTO|TABLE|UPDATE|JOIN)\s+`?(\w+)`?', query, re.IGNORECASE)
            if table_match:
                table_name = table_match.group(1)
        
        # Categorize error types
        if "doesn't exist" in error_str.lower() or "1146" in error_code:
            error_type = "TABLE_NOT_FOUND"
        elif "access denied" in error_str.lower() or "1045" in error_code:
            error_type = "ACCESS_DENIED"
        elif "syntax error" in error_str.lower() or "1064" in error_code:
            error_type = "SYNTAX_ERROR"
        elif "connection" in error_str.lower():
            error_type = "CONNECTION_ERROR"
        elif "duplicate entry" in error_str.lower() or "1062" in error_code:
            error_type = "DUPLICATE_KEY"
        elif "deadlock" in error_str.lower() or "1213" in error_code:
            error_type = "DEADLOCK"
        elif "timeout" in error_str.lower():
            error_type = "TIMEOUT"
        elif "too many connections" in error_str.lower() or "1040" in error_code:
            error_type = "TOO_MANY_CONNECTIONS"
            
        return DatabaseError(
            error_type=error_type,
            error_code=error_code,
            message=error_str,
            query=query,
            table=table_name,
            context={"traceback": traceback.format_exc()}
        )


class DatabaseConnector:
    """Database connector supporting multiple database types with auto-error resolution"""
    
    def __init__(self, config, error_callback: Union[Callable[[DatabaseError], None], Callable[[DatabaseError], Awaitable[Any]]] = None):
        """Initialize database connector with error resolution callback"""
        self.config = config
        self.connections = {}
        self.connection_pools = {}
        self.error_callback = error_callback  # Callback to send errors to AI
        
    def set_error_callback(self, callback: Union[Callable[[DatabaseError], None], Callable[[DatabaseError], Awaitable[Any]]]):
        """Set callback function for auto-error resolution"""
        self.error_callback = callback
        
    async def handle_database_error(self, error: Exception, query: str = None, db_type: str = "mysql"):
        """Handle database errors and trigger auto-resolution"""
        logger.error(f"Database error occurred: {error}")
        
        if db_type == "mysql":
            db_error = ErrorAnalyzer.analyze_mysql_error(error, query)
        else:
            # Create generic error for other database types
            db_error = DatabaseError(
                error_type="GENERAL",
                error_code="UNKNOWN",
                message=str(error),
                query=query,
                context={"db_type": db_type, "traceback": traceback.format_exc()}
            )
        
        # Log the structured error
        logger.error(f"Structured Error: {db_error.error_type} - {db_error.message}")
        
        # Send to AI for auto-resolution if callback is set
        if self.error_callback:
            try:
                # Handle both sync and async callbacks
                import asyncio
                if asyncio.iscoroutinefunction(self.error_callback):
                    await self.error_callback(db_error)
                else:
                    self.error_callback(db_error)
            except Exception as callback_error:
                logger.error(f"Error in auto-resolution callback: {callback_error}")
        
        return db_error
        
    async def get_connection(self, db_config: DatabaseConfig):
        """Get database connection based on type"""
        db_type = db_config.db_type.lower()
        
        if db_type == "postgresql":
            return await self._get_postgresql_connection(db_config)
        elif db_type == "mysql":
            return await self._get_mysql_connection(db_config)
        elif db_type == "mongodb":
            return await self._get_mongodb_connection(db_config)
        elif db_type == "redis":
            return await self._get_redis_connection(db_config)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
            
    async def _get_postgresql_connection(self, db_config: DatabaseConfig):
        """Get PostgreSQL connection"""
        try:
            if db_config.db_type not in self.connection_pools:
                self.connection_pools[db_config.db_type] = await asyncpg.create_pool(
                    host=db_config.host,
                    port=db_config.port,
                    database=db_config.database,
                    user=db_config.username,
                    password=db_config.password,
                    min_size=1,
                    max_size=db_config.connection_pool_size,
                    command_timeout=db_config.timeout
                )
                
            return PostgreSQLConnection(self.connection_pools[db_config.db_type])
            
        except Exception as e:
            logger.error(f"Failed to create PostgreSQL connection: {e}")
            raise
            
    async def _get_mysql_connection(self, db_config: DatabaseConfig):
        """Get MySQL connection"""
        try:
            # Create individual connection instead of pool for better cleanup
            connection = await aiomysql.connect(
                host=db_config.host,
                port=db_config.port,
                db=db_config.database,
                user=db_config.username,
                password=db_config.password,
                autocommit=True
            )
            return MySQLConnection(connection, self)
            
        except Exception as e:
            logger.error(f"Failed to create MySQL connection: {e}")
            raise
            
    async def _get_mongodb_connection(self, db_config: DatabaseConfig):
        """Get MongoDB connection"""
        try:
            if db_config.db_type not in self.connections:
                connection_string = f"mongodb://{db_config.username}:{db_config.password}@{db_config.host}:{db_config.port}/{db_config.database}"
                self.connections[db_config.db_type] = MongoClient(connection_string)
                
            return MongoDBConnection(self.connections[db_config.db_type], db_config.database)
            
        except Exception as e:
            logger.error(f"Failed to create MongoDB connection: {e}")
            raise
            
    async def _get_redis_connection(self, db_config: DatabaseConfig):
        """Get Redis connection"""
        try:
            if db_config.db_type not in self.connections:
                self.connections[db_config.db_type] = aioredis.from_url(
                    f"redis://{db_config.host}:{db_config.port}",
                    password=db_config.password if db_config.password else None,
                    encoding="utf-8",
                    decode_responses=True
                )
            
            return RedisConnection(self.connections[db_config.db_type])
        
        except Exception as e:
            logger.error(f"Failed to create Redis connection: {e}")
            raise
            
    async def close_all_connections(self):
        """Close all database connections"""
        for pool in self.connection_pools.values():
            await pool.close()
            
        for conn in self.connections.values():
            if hasattr(conn, 'close'):
                await conn.close()
            else:
                conn.close()


class PostgreSQLConnection:
    """PostgreSQL connection wrapper"""
    
    def __init__(self, pool):
        self.pool = pool
        
    async def execute_query(self, query: str, params: tuple = None) -> List[tuple]:
        """Execute a query and return results"""
        async with self.pool.acquire() as conn:
            if params:
                result = await conn.fetch(query, *params)
            else:
                result = await conn.fetch(query)
            return [tuple(row) for row in result]
            
    async def execute_command(self, command: str, params: tuple = None) -> str:
        """Execute a command and return status"""
        async with self.pool.acquire() as conn:
            if params:
                result = await conn.execute(command, *params)
            else:
                result = await conn.execute(command)
            return result
            
    async def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get table information"""
        query = """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = $1 AND table_schema = 'public'
        ORDER BY ordinal_position;
        """
        result = await self.execute_query(query, (table_name,))
        return {"columns": result}
        
    async def get_index_info(self, table_name: str) -> Dict[str, Any]:
        """Get index information"""
        query = """
        SELECT indexname, indexdef
        FROM pg_indexes
        WHERE tablename = $1;
        """
        result = await self.execute_query(query, (table_name,))
        return {"indexes": result}


class MySQLConnection:
    """MySQL connection wrapper with auto-error resolution"""
    
    def __init__(self, connection, connector: DatabaseConnector = None):
        self.connection = connection
        self.connector = connector  # Reference to parent connector for error handling
        
    async def execute_query(self, query: str, params: tuple = None) -> List[tuple]:
        """Execute a query and return results with auto-error handling"""
        try:
            async with self.connection.cursor() as cursor:
                if params:
                    await cursor.execute(query, params)
                else:
                    await cursor.execute(query)
                result = await cursor.fetchall()
                return result
        except Exception as error:
            # Auto-handle database errors
            if self.connector:
                await self.connector.handle_database_error(error, query, "mysql")
            raise  # Re-raise after handling
                
    async def execute_command(self, command: str, params: tuple = None) -> str:
        """Execute a command and return status with auto-error handling"""
        try:
            async with self.connection.cursor() as cursor:
                if params:
                    await cursor.execute(command, params)
                else:
                    await cursor.execute(command)
                return f"Affected rows: {cursor.rowcount}"
        except Exception as error:
            # Auto-handle database errors
            if self.connector:
                await self.connector.handle_database_error(error, command, "mysql")
            raise  # Re-raise after handling
                
    async def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get table information with auto-error handling"""
        query = """
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = %s AND TABLE_SCHEMA = DATABASE()
        ORDER BY ORDINAL_POSITION;
        """
        try:
            result = await self.execute_query(query, (table_name,))
            return {"columns": result}
        except Exception as error:
            # Auto-handle database errors
            if self.connector:
                await self.connector.handle_database_error(error, query, "mysql")
            raise  # Re-raise after handling
        
    async def get_index_info(self, table_name: str) -> Dict[str, Any]:
        """Get index information with auto-error handling"""
        query = "SHOW INDEX FROM " + table_name
        try:
            result = await self.execute_query(query)
            return {"indexes": result}
        except Exception as error:
            # Auto-handle database errors
            if self.connector:
                await self.connector.handle_database_error(error, query, "mysql")
            raise  # Re-raise after handling
        
    async def close(self):
        """Close the MySQL connection"""
        if self.connection and not self.connection.closed:
            await self.connection.close()
            
    async def __aenter__(self):
        """Async context manager entry"""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()


class MongoDBConnection:
    """MongoDB connection wrapper"""
    
    def __init__(self, client, database_name: str):
        self.client = client
        self.db = client[database_name]
        
    async def execute_query(self, query: str, collection: str = None) -> List[Dict]:
        """Execute a MongoDB query"""
        if not collection:
            raise ValueError("Collection name required for MongoDB queries")
            
        # Simple query execution - in practice, you'd parse the query string
        # For now, return collection stats
        collection_obj = self.db[collection]
        stats = await collection_obj.aggregate([{"$collStats": {"storage": {}, "count": {}}}]).to_list(length=1)
        return stats
        
    async def execute_command(self, command: str, collection: str = None) -> str:
        """Execute a MongoDB command"""
        if not collection:
            raise ValueError("Collection name required for MongoDB commands")
            
        collection_obj = self.db[collection]
        # Execute command based on string (simplified)
        if "createIndex" in command.lower():
            return "Index creation command executed"
        elif "drop" in command.lower():
            return "Drop command executed"
        else:
            return "Command executed"
            
    async def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get collection information"""
        collection = self.db[collection_name]
        stats = await collection.aggregate([{"$collStats": {"storage": {}, "count": {}}}]).to_list(length=1)
        return {"collection_stats": stats[0] if stats else {}}


class RedisConnection:
    """Redis connection wrapper"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        
    async def execute_query(self, query: str) -> List[str]:
        """Execute a Redis query"""
        # Parse simple Redis commands
        parts = query.strip().split()
        if not parts:
            return []
            
        command = parts[0].upper()
        args = parts[1:]
        
        if command == "KEYS":
            pattern = args[0] if args else "*"
            result = await self.redis.keys(pattern)
            return result
        elif command == "INFO":
            section = args[0] if args else "default"
            result = await self.redis.info(section)
            return [str(result)]
        elif command == "MEMORY":
            result = await self.redis.memory_usage()
            return [str(result)]
        else:
            return [f"Command {command} not implemented in query mode"]
            
    async def execute_command(self, command: str) -> str:
        """Execute a Redis command"""
        parts = command.strip().split()
        if not parts:
            return "Empty command"
            
        cmd = parts[0].upper()
        args = parts[1:]
        
        try:
            if cmd == "SET":
                await self.redis.set(args[0], args[1])
                return "OK"
            elif cmd == "GET":
                result = await self.redis.get(args[0])
                return str(result)
            elif cmd == "DEL":
                result = await self.redis.delete(args[0])
                return f"Deleted {result} keys"
            elif cmd == "FLUSHDB":
                await self.redis.flushdb()
                return "Database flushed"
            else:
                return f"Command {cmd} not implemented"
        except Exception as e:
            return f"Error: {str(e)}"
            
    async def get_info(self) -> Dict[str, Any]:
        """Get Redis server information"""
        info = await self.redis.info()
        return {
            "server": info.get("server", {}),
            "clients": info.get("clients", {}),
            "memory": info.get("memory", {}),
            "stats": info.get("stats", {})
        } 