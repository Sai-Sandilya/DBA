"""
Auto-remediation system for DBA-GPT
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from core.config import Config
from core.database.connector import DatabaseConnector
from core.utils.logger import setup_logger

logger = setup_logger(__name__)


class AutoRemediator:
    """Automatic database issue remediation"""
    
    def __init__(self, config: Config):
        """Initialize auto-remediator"""
        self.config = config
        self.db_connector = DatabaseConnector(config)
        self.remediation_history = []
        
    async def remediate_issues(self, db_name: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to remediate detected issues"""
        remediation_results = {
            "timestamp": datetime.now().isoformat(),
            "database": db_name,
            "issues_found": [],
            "remediations_applied": [],
            "success_count": 0,
            "error_count": 0
        }
        
        try:
            db_config = self.config.get_database_config(db_name)
            if not db_config:
                remediation_results["error"] = f"Database {db_name} not found in configuration"
                return remediation_results
                
            # Get connector
            connector = await self.db_connector.get_connection(db_config)
            
            # Check for specific issues and apply remediations
            issues = await self._identify_issues(metrics)
            remediation_results["issues_found"] = issues
            
            for issue in issues:
                try:
                    result = await self._apply_remediation(connector, db_config, issue)
                    remediation_results["remediations_applied"].append(result)
                    
                    if result["success"]:
                        remediation_results["success_count"] += 1
                    else:
                        remediation_results["error_count"] += 1
                        
                except Exception as e:
                    logger.error(f"Error applying remediation for {issue['type']}: {e}")
                    remediation_results["error_count"] += 1
                    remediation_results["remediations_applied"].append({
                        "issue_type": issue["type"],
                        "success": False,
                        "error": str(e)
                    })
                    
            # Store remediation history
            self.remediation_history.append(remediation_results)
            
        except Exception as e:
            logger.error(f"Error in remediation for {db_name}: {e}")
            remediation_results["error"] = str(e)
            
        return remediation_results
        
    async def _identify_issues(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify issues from metrics"""
        issues = []
        
        # Check for high CPU usage
        cpu_usage = metrics.get("performance", {}).get("cpu_usage", 0)
        if cpu_usage > 90:
            issues.append({
                "type": "high_cpu",
                "severity": "critical",
                "value": cpu_usage,
                "description": f"CPU usage is critically high: {cpu_usage}%"
            })
        elif cpu_usage > 80:
            issues.append({
                "type": "high_cpu",
                "severity": "warning",
                "value": cpu_usage,
                "description": f"CPU usage is high: {cpu_usage}%"
            })
            
        # Check for high memory usage
        memory_usage = metrics.get("performance", {}).get("memory_usage", 0)
        if memory_usage > 95:
            issues.append({
                "type": "high_memory",
                "severity": "critical",
                "value": memory_usage,
                "description": f"Memory usage is critically high: {memory_usage}%"
            })
        elif memory_usage > 85:
            issues.append({
                "type": "high_memory",
                "severity": "warning",
                "value": memory_usage,
                "description": f"Memory usage is high: {memory_usage}%"
            })
            
        # Check for high disk usage
        disk_usage = metrics.get("performance", {}).get("disk_usage", 0)
        if disk_usage > 95:
            issues.append({
                "type": "high_disk",
                "severity": "critical",
                "value": disk_usage,
                "description": f"Disk usage is critically high: {disk_usage}%"
            })
        elif disk_usage > 90:
            issues.append({
                "type": "high_disk",
                "severity": "warning",
                "value": disk_usage,
                "description": f"Disk usage is high: {disk_usage}%"
            })
            
        # Check for slow queries
        slow_queries = metrics.get("performance", {}).get("slow_queries", 0)
        if slow_queries > 10:
            issues.append({
                "type": "slow_queries",
                "severity": "critical",
                "value": slow_queries,
                "description": f"High number of slow queries: {slow_queries}"
            })
        elif slow_queries > 0:
            issues.append({
                "type": "slow_queries",
                "severity": "warning",
                "value": slow_queries,
                "description": f"Some slow queries detected: {slow_queries}"
            })
            
        # Check for connection pool issues
        connection_pool = metrics.get("performance", {}).get("connection_pool", {})
        pool_usage = connection_pool.get("usage_percent", 0)
        if pool_usage > 90:
            issues.append({
                "type": "connection_pool",
                "severity": "critical",
                "value": pool_usage,
                "description": f"Connection pool usage is critically high: {pool_usage}%"
            })
        elif pool_usage > 80:
            issues.append({
                "type": "connection_pool",
                "severity": "warning",
                "value": pool_usage,
                "description": f"Connection pool usage is high: {pool_usage}%"
            })
            
        return issues
        
    async def _apply_remediation(self, connector, db_config, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Apply specific remediation based on issue type"""
        issue_type = issue["type"]
        result = {
            "issue_type": issue_type,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "action_taken": "",
            "details": {}
        }
        
        try:
            if issue_type == "high_cpu":
                result = await self._remediate_high_cpu(connector, db_config, issue)
            elif issue_type == "high_memory":
                result = await self._remediate_high_memory(connector, db_config, issue)
            elif issue_type == "high_disk":
                result = await self._remediate_high_disk(connector, db_config, issue)
            elif issue_type == "slow_queries":
                result = await self._remediate_slow_queries(connector, db_config, issue)
            elif issue_type == "connection_pool":
                result = await self._remediate_connection_pool(connector, db_config, issue)
            else:
                result["action_taken"] = f"No remediation available for issue type: {issue_type}"
                
        except Exception as e:
            logger.error(f"Error in remediation {issue_type}: {e}")
            result["error"] = str(e)
            
        return result
        
    async def _remediate_high_cpu(self, connector, db_config, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Remediate high CPU usage"""
        result = {
            "issue_type": "high_cpu",
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "action_taken": "Attempted to optimize database operations",
            "details": {}
        }
        
        try:
            if db_config.db_type == "postgresql":
                # Kill long-running queries
                long_queries = await connector.execute_query("""
                    SELECT pid, query_start, state, query 
                    FROM pg_stat_activity 
                    WHERE state = 'active' AND now() - query_start > interval '30 seconds';
                """)
                
                if long_queries:
                    for query in long_queries:
                        try:
                            await connector.execute_command(f"SELECT pg_terminate_backend({query[0]});")
                            result["details"]["terminated_queries"] = result["details"].get("terminated_queries", 0) + 1
                        except Exception as e:
                            logger.warning(f"Could not terminate query {query[0]}: {e}")
                            
                # Run maintenance operations
                await connector.execute_command("CHECKPOINT;")
                result["details"]["checkpoint_run"] = True
                
            elif db_config.db_type == "mysql":
                # Kill long-running queries
                long_queries = await connector.execute_query("""
                    SELECT id, time, state, info 
                    FROM information_schema.processlist 
                    WHERE command != 'Sleep' AND time > 30;
                """)
                
                if long_queries:
                    for query in long_queries:
                        try:
                            await connector.execute_command(f"KILL {query[0]};")
                            result["details"]["terminated_queries"] = result["details"].get("terminated_queries", 0) + 1
                        except Exception as e:
                            logger.warning(f"Could not kill query {query[0]}: {e}")
                            
            result["success"] = True
            
        except Exception as e:
            result["error"] = str(e)
            
        return result
        
    async def _remediate_high_memory(self, connector, db_config, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Remediate high memory usage"""
        result = {
            "issue_type": "high_memory",
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "action_taken": "Attempted to free memory",
            "details": {}
        }
        
        try:
            if db_config.db_type == "postgresql":
                # Run VACUUM to free memory
                await connector.execute_command("VACUUM;")
                result["details"]["vacuum_run"] = True
                
                # Clear query cache
                await connector.execute_command("DISCARD ALL;")
                result["details"]["cache_cleared"] = True
                
            elif db_config.db_type == "mysql":
                # Flush tables
                await connector.execute_command("FLUSH TABLES;")
                result["details"]["tables_flushed"] = True
                
                # Clear query cache
                await connector.execute_command("FLUSH QUERY CACHE;")
                result["details"]["query_cache_cleared"] = True
                
            result["success"] = True
            
        except Exception as e:
            result["error"] = str(e)
            
        return result
        
    async def _remediate_high_disk(self, connector, db_config, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Remediate high disk usage"""
        result = {
            "issue_type": "high_disk",
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "action_taken": "Attempted to free disk space",
            "details": {}
        }
        
        try:
            if db_config.db_type == "postgresql":
                # Run aggressive VACUUM
                await connector.execute_command("VACUUM FULL;")
                result["details"]["vacuum_full_run"] = True
                
                # Clean up old WAL files
                await connector.execute_command("SELECT pg_switch_wal();")
                result["details"]["wal_switched"] = True
                
            elif db_config.db_type == "mysql":
                # Optimize tables
                tables = await connector.execute_query("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = DATABASE();
                """)
                
                for table in tables:
                    try:
                        await connector.execute_command(f"OPTIMIZE TABLE {table[0]};")
                        result["details"]["optimized_tables"] = result["details"].get("optimized_tables", 0) + 1
                    except Exception as e:
                        logger.warning(f"Could not optimize table {table[0]}: {e}")
                        
            result["success"] = True
            
        except Exception as e:
            result["error"] = str(e)
            
        return result
        
    async def _remediate_slow_queries(self, connector, db_config, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Remediate slow queries"""
        result = {
            "issue_type": "slow_queries",
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "action_taken": "Attempted to optimize slow queries",
            "details": {}
        }
        
        try:
            if db_config.db_type == "postgresql":
                # Update table statistics
                await connector.execute_command("ANALYZE;")
                result["details"]["analyze_run"] = True
                
                # Check for missing indexes
                missing_indexes = await connector.execute_query("""
                    SELECT schemaname, tablename, attname, n_distinct, correlation
                    FROM pg_stats 
                    WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
                    AND n_distinct > 1000 AND correlation < 0.1;
                """)
                
                if missing_indexes:
                    result["details"]["potential_missing_indexes"] = len(missing_indexes)
                    
            elif db_config.db_type == "mysql":
                # Analyze tables
                tables = await connector.execute_query("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = DATABASE();
                """)
                
                for table in tables:
                    try:
                        await connector.execute_command(f"ANALYZE TABLE {table[0]};")
                        result["details"]["analyzed_tables"] = result["details"].get("analyzed_tables", 0) + 1
                    except Exception as e:
                        logger.warning(f"Could not analyze table {table[0]}: {e}")
                        
            result["success"] = True
            
        except Exception as e:
            result["error"] = str(e)
            
        return result
        
    async def _remediate_connection_pool(self, connector, db_config, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Remediate connection pool issues"""
        result = {
            "issue_type": "connection_pool",
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "action_taken": "Attempted to optimize connection usage",
            "details": {}
        }
        
        try:
            if db_config.db_type == "postgresql":
                # Terminate idle connections
                idle_connections = await connector.execute_query("""
                    SELECT pid FROM pg_stat_activity 
                    WHERE state = 'idle' AND now() - state_change > interval '5 minutes';
                """)
                
                for conn in idle_connections:
                    try:
                        await connector.execute_command(f"SELECT pg_terminate_backend({conn[0]});")
                        result["details"]["terminated_idle_connections"] = result["details"].get("terminated_idle_connections", 0) + 1
                    except Exception as e:
                        logger.warning(f"Could not terminate idle connection {conn[0]}: {e}")
                        
            elif db_config.db_type == "mysql":
                # Kill idle connections
                idle_connections = await connector.execute_query("""
                    SELECT id FROM information_schema.processlist 
                    WHERE command = 'Sleep' AND time > 300;
                """)
                
                for conn in idle_connections:
                    try:
                        await connector.execute_command(f"KILL {conn[0]};")
                        result["details"]["killed_idle_connections"] = result["details"].get("killed_idle_connections", 0) + 1
                    except Exception as e:
                        logger.warning(f"Could not kill idle connection {conn[0]}: {e}")
                        
            result["success"] = True
            
        except Exception as e:
            result["error"] = str(e)
            
        return result
        
    async def get_remediation_history(self, db_name: str = None, hours: int = 24) -> List[Dict[str, Any]]:
        """Get remediation history"""
        cutoff_time = datetime.now().replace(hour=datetime.now().hour - hours)
        
        history = [
            entry for entry in self.remediation_history
            if datetime.fromisoformat(entry["timestamp"]) > cutoff_time
        ]
        
        if db_name:
            history = [
                entry for entry in history
                if entry.get("database") == db_name
            ]
            
        return history
        
    async def get_remediation_stats(self) -> Dict[str, Any]:
        """Get remediation statistics"""
        if not self.remediation_history:
            return {"total_remediations": 0, "success_rate": 0}
            
        total_remediations = len(self.remediation_history)
        successful_remediations = sum(
            1 for entry in self.remediation_history
            if entry.get("success_count", 0) > 0
        )
        
        return {
            "total_remediations": total_remediations,
            "successful_remediations": successful_remediations,
            "success_rate": (successful_remediations / total_remediations) * 100 if total_remediations > 0 else 0,
            "last_remediation": self.remediation_history[-1]["timestamp"] if self.remediation_history else None
        } 