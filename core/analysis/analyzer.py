"""
Performance analyzer for DBA-GPT
"""

import asyncio
import psutil
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from core.config import Config, DatabaseConfig
from core.database.connector import DatabaseConnector
from core.utils.logger import setup_logger

logger = setup_logger(__name__)


class PerformanceAnalyzer:
    """Analyzes database performance and system health"""
    
    def __init__(self, config: Config):
        """Initialize Performance Analyzer"""
        self.config = config
        self.db_connector = DatabaseConnector(config)
        
    async def get_database_info(self, db_config: DatabaseConfig) -> Dict[str, Any]:
        """Get database schema and version information."""
        info = {"db_type": db_config.db_type}
        try:
            connector = await self.db_connector.get_connection(db_config)
            if db_config.db_type == "mysql":
                version_res = await connector.execute_query("SELECT VERSION();")
                info["version"] = version_res[0][0] if version_res else "Unknown"

                tables_res = await connector.execute_query("SHOW TABLES;")
                tables = [row[0] for row in tables_res]
                info["tables"] = tables
                
                schema = {}
                for table_name in tables:
                    cols_res = await connector.execute_query(f"DESCRIBE `{table_name}`;")
                    schema[table_name] = [row[0] for row in cols_res]
                info["schema"] = schema
            # Add logic for other DB types like postgresql if needed
        except Exception as e:
            logger.error(f"Error getting database info for {db_config.db_name}: {e}")
            info["error"] = str(e)
        return info
        
    async def get_current_metrics(self, db_config: DatabaseConfig) -> Dict[str, Any]:
        """Get current performance metrics"""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "cpu_usage": 0,
            "memory_usage": 0,
            "disk_usage": 0,
            "connection_pool": {},
            "slow_queries": 0,
            "active_connections": 0,
            "database_size": 0,
            "query_performance": {}
        }
        
        try:
            # Get system metrics
            metrics.update(await self._get_system_metrics())
            
            # Get database-specific metrics
            db_metrics = await self._get_database_metrics(db_config)
            metrics.update(db_metrics)
            
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            metrics["error"] = str(e)
            
        return metrics
        
    async def _get_system_metrics(self) -> Dict[str, Any]:
        """Get system-level metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            return {
                "cpu_usage": cpu_percent,
                "memory_usage": memory_percent,
                "disk_usage": disk_percent,
                "memory_total": memory.total,
                "memory_available": memory.available,
                "disk_total": disk.total,
                "disk_free": disk.free
            }
            
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {
                "cpu_usage": 0,
                "memory_usage": 0,
                "disk_usage": 0
            }
            
    async def _get_database_metrics(self, db_config: DatabaseConfig) -> Dict[str, Any]:
        """Get database-specific metrics"""
        try:
            connector = await self.db_connector.get_connection(db_config)
            
            if db_config.db_type == "postgresql":
                return await self._get_postgresql_metrics(connector)
            elif db_config.db_type == "mysql":
                return await self._get_mysql_metrics(connector)
            elif db_config.db_type == "mongodb":
                return await self._get_mongodb_metrics(connector)
            elif db_config.db_type == "redis":
                return await self._get_redis_metrics(connector)
            else:
                return {"error": f"Unsupported database type: {db_config.db_type}"}
                
        except Exception as e:
            logger.error(f"Error getting database metrics: {e}")
            return {"error": str(e)}
            
    async def _get_postgresql_metrics(self, connector) -> Dict[str, Any]:
        """Get PostgreSQL specific metrics"""
        metrics = {}
        
        try:
            # Active connections
            result = await connector.execute_query(
                "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';"
            )
            metrics["active_connections"] = result[0][0] if result else 0
            
            # Database size
            result = await connector.execute_query(
                "SELECT pg_size_pretty(pg_database_size(current_database()));"
            )
            metrics["database_size"] = result[0][0] if result else "0 MB"
            
            # Slow queries (queries running longer than 5 seconds)
            result = await connector.execute_query("""
                SELECT count(*) FROM pg_stat_activity 
                WHERE state = 'active' AND now() - query_start > interval '5 seconds';
            """)
            metrics["slow_queries"] = result[0][0] if result else 0
            
            # Connection pool info
            result = await connector.execute_query("""
                SELECT setting::int as max_connections 
                FROM pg_settings WHERE name = 'max_connections';
            """)
            max_connections = result[0][0] if result else 100
            
            metrics["connection_pool"] = {
                "active": metrics["active_connections"],
                "max": max_connections,
                "usage_percent": (metrics["active_connections"] / max_connections) * 100
            }
            
            # Query performance stats
            result = await connector.execute_query("""
                SELECT 
                    schemaname,
                    tablename,
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes,
                    n_live_tup as live_tuples,
                    n_dead_tup as dead_tuples
                FROM pg_stat_user_tables 
                ORDER BY n_tup_ins + n_tup_upd + n_tup_del DESC 
                LIMIT 10;
            """)
            metrics["query_performance"] = {
                "table_stats": result if result else []
            }
            
        except Exception as e:
            logger.error(f"Error getting PostgreSQL metrics: {e}")
            metrics["error"] = str(e)
            
        return metrics
        
    async def _get_mysql_metrics(self, connector) -> Dict[str, Any]:
        """Get MySQL specific metrics"""
        metrics = {}
        
        try:
            # Active connections
            result = await connector.execute_query("SHOW STATUS LIKE 'Threads_connected';")
            metrics["active_connections"] = int(result[0][1]) if result else 0
            
            # Database size
            result = await connector.execute_query("""
                SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 1) AS 'DB Size in MB' 
                FROM information_schema.tables 
                WHERE table_schema = DATABASE();
            """)
            metrics["database_size"] = f"{result[0][0]} MB" if result else "0 MB"
            
            # Slow queries
            result = await connector.execute_query("SHOW STATUS LIKE 'Slow_queries';")
            metrics["slow_queries"] = int(result[0][1]) if result else 0
            
            # Connection pool info
            result = await connector.execute_query("SHOW VARIABLES LIKE 'max_connections';")
            max_connections = int(result[0][1]) if result else 100
            
            metrics["connection_pool"] = {
                "active": metrics["active_connections"],
                "max": max_connections,
                "usage_percent": (metrics["active_connections"] / max_connections) * 100
            }
            
            # Query performance stats
            result = await connector.execute_query("SHOW ENGINE INNODB STATUS;")
            metrics["query_performance"] = {
                "innodb_status": result[0][2] if result else ""
            }
            
        except Exception as e:
            logger.error(f"Error getting MySQL metrics: {e}")
            metrics["error"] = str(e)
            
        return metrics
        
    async def _get_mongodb_metrics(self, connector) -> Dict[str, Any]:
        """Get MongoDB specific metrics"""
        metrics = {}
        
        try:
            # Get collection stats
            collections = await connector.execute_query("SHOW TABLES", "system.namespaces")
            metrics["collections"] = len(collections) if collections else 0
            
            # Get database stats
            stats = await connector.get_collection_info("system.namespaces")
            metrics["database_size"] = stats.get("collection_stats", {}).get("storageSize", 0)
            
            # Connection info
            metrics["connection_pool"] = {
                "active": 0,  # MongoDB doesn't expose this easily
                "max": 0,
                "usage_percent": 0
            }
            
            metrics["query_performance"] = {
                "collections": collections if collections else []
            }
            
        except Exception as e:
            logger.error(f"Error getting MongoDB metrics: {e}")
            metrics["error"] = str(e)
            
        return metrics
        
    async def _get_redis_metrics(self, connector) -> Dict[str, Any]:
        """Get Redis specific metrics"""
        metrics = {}
        
        try:
            # Get Redis info
            info = await connector.get_info()
            
            metrics["active_connections"] = info.get("clients", {}).get("connected_clients", 0)
            metrics["database_size"] = info.get("memory", {}).get("used_memory_human", "0 B")
            
            # Connection pool info
            max_clients = info.get("clients", {}).get("maxclients", 10000)
            metrics["connection_pool"] = {
                "active": metrics["active_connections"],
                "max": max_clients,
                "usage_percent": (metrics["active_connections"] / max_clients) * 100
            }
            
            metrics["query_performance"] = {
                "commands_processed": info.get("stats", {}).get("total_commands_processed", 0),
                "keyspace_hits": info.get("stats", {}).get("keyspace_hits", 0),
                "keyspace_misses": info.get("stats", {}).get("keyspace_misses", 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting Redis metrics: {e}")
            metrics["error"] = str(e)
            
        return metrics
        
    async def get_system_health(self, db_config: DatabaseConfig) -> Dict[str, Any]:
        """Get system health information"""
        health = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "checks": {},
            "recommendations": []
        }
        
        try:
            # Get current metrics
            metrics = await self.get_current_metrics(db_config)
            
            # Check CPU health
            cpu_usage = metrics.get("cpu_usage", 0)
            if cpu_usage > 90:
                health["checks"]["cpu"] = {"status": "critical", "value": cpu_usage}
                health["recommendations"].append("CPU usage is critically high. Consider scaling or optimization.")
            elif cpu_usage > 80:
                health["checks"]["cpu"] = {"status": "warning", "value": cpu_usage}
                health["recommendations"].append("CPU usage is high. Monitor for potential issues.")
            else:
                health["checks"]["cpu"] = {"status": "healthy", "value": cpu_usage}
                
            # Check memory health
            memory_usage = metrics.get("memory_usage", 0)
            if memory_usage > 95:
                health["checks"]["memory"] = {"status": "critical", "value": memory_usage}
                health["recommendations"].append("Memory usage is critically high. Immediate action required.")
            elif memory_usage > 85:
                health["checks"]["memory"] = {"status": "warning", "value": memory_usage}
                health["recommendations"].append("Memory usage is high. Consider cleanup or scaling.")
            else:
                health["checks"]["memory"] = {"status": "healthy", "value": memory_usage}
                
            # Check disk health
            disk_usage = metrics.get("disk_usage", 0)
            if disk_usage > 95:
                health["checks"]["disk"] = {"status": "critical", "value": disk_usage}
                health["recommendations"].append("Disk usage is critically high. Immediate cleanup required.")
            elif disk_usage > 90:
                health["checks"]["disk"] = {"status": "warning", "value": disk_usage}
                health["recommendations"].append("Disk usage is high. Plan for cleanup or expansion.")
            else:
                health["checks"]["disk"] = {"status": "healthy", "value": disk_usage}
                
            # Check connection pool health
            connection_pool = metrics.get("connection_pool", {})
            pool_usage = connection_pool.get("usage_percent", 0)
            if pool_usage > 90:
                health["checks"]["connections"] = {"status": "critical", "value": pool_usage}
                health["recommendations"].append("Connection pool usage is critically high. Increase pool size.")
            elif pool_usage > 80:
                health["checks"]["connections"] = {"status": "warning", "value": pool_usage}
                health["recommendations"].append("Connection pool usage is high. Monitor and consider optimization.")
            else:
                health["checks"]["connections"] = {"status": "healthy", "value": pool_usage}
                
            # Check slow queries
            slow_queries = metrics.get("slow_queries", 0)
            if slow_queries > 10:
                health["checks"]["slow_queries"] = {"status": "critical", "value": slow_queries}
                health["recommendations"].append("High number of slow queries detected. Review and optimize queries.")
            elif slow_queries > 0:
                health["checks"]["slow_queries"] = {"status": "warning", "value": slow_queries}
                health["recommendations"].append("Some slow queries detected. Monitor query performance.")
            else:
                health["checks"]["slow_queries"] = {"status": "healthy", "value": slow_queries}
                
            # Determine overall status
            critical_count = sum(1 for check in health["checks"].values() if check["status"] == "critical")
            warning_count = sum(1 for check in health["checks"].values() if check["status"] == "warning")
            
            if critical_count > 0:
                health["overall_status"] = "critical"
            elif warning_count > 0:
                health["overall_status"] = "warning"
            else:
                health["overall_status"] = "healthy"
                
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            health["overall_status"] = "error"
            health["error"] = str(e)
            
        return health
        
    async def generate_performance_report(self, db_config: DatabaseConfig) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "database": db_config.database,
            "database_type": db_config.db_type,
            "summary": {},
            "metrics": {},
            "health": {},
            "recommendations": []
        }
        
        try:
            # Get current metrics
            metrics = await self.get_current_metrics(db_config)
            report["metrics"] = metrics
            
            # Get system health
            health = await self.get_system_health(db_config)
            report["health"] = health
            
            # Generate summary
            report["summary"] = {
                "status": health["overall_status"],
                "cpu_usage": metrics.get("cpu_usage", 0),
                "memory_usage": metrics.get("memory_usage", 0),
                "disk_usage": metrics.get("disk_usage", 0),
                "active_connections": metrics.get("active_connections", 0),
                "slow_queries": metrics.get("slow_queries", 0)
            }
            
            # Generate recommendations
            report["recommendations"] = health.get("recommendations", [])
            
            # Add database-specific recommendations
            if db_config.db_type == "postgresql":
                report["recommendations"].extend(await self._get_postgresql_recommendations(metrics))
            elif db_config.db_type == "mysql":
                report["recommendations"].extend(await self._get_mysql_recommendations(metrics))
                
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            report["error"] = str(e)
            
        return report
        
    async def _get_postgresql_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """Get PostgreSQL specific recommendations"""
        recommendations = []
        
        # Check for dead tuples
        query_performance = metrics.get("query_performance", {})
        table_stats = query_performance.get("table_stats", [])
        
        for table_stat in table_stats:
            if len(table_stat) >= 7:
                dead_tuples = table_stat[6]  # n_dead_tup
                live_tuples = table_stat[5]  # n_live_tup
                
                if dead_tuples > 0 and live_tuples > 0:
                    dead_ratio = dead_tuples / (dead_tuples + live_tuples)
                    if dead_ratio > 0.1:  # More than 10% dead tuples
                        table_name = table_stat[1]  # tablename
                        recommendations.append(
                            f"Table '{table_name}' has high dead tuple ratio ({dead_ratio:.1%}). Consider running VACUUM."
                        )
                        
        return recommendations
        
    async def _get_mysql_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """Get MySQL specific recommendations"""
        recommendations = []
        
        # Check InnoDB buffer pool usage
        query_performance = metrics.get("query_performance", {})
        innodb_status = query_performance.get("innodb_status", "")
        
        if "Buffer pool hit rate" in innodb_status:
            # Parse buffer pool hit rate
            try:
                hit_rate_line = [line for line in innodb_status.split('\n') if 'Buffer pool hit rate' in line][0]
                hit_rate = float(hit_rate_line.split('/')[0].strip())
                if hit_rate < 95:
                    recommendations.append(
                        f"InnoDB buffer pool hit rate is low ({hit_rate:.1f}%). Consider increasing buffer pool size."
                    )
            except (IndexError, ValueError):
                pass
                
        return recommendations 