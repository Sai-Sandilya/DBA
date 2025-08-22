"""
Performance analyzer for DBA-GPT
"""

import asyncio
import psutil
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import hashlib
import re

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
        # Optimizer utilities (initialized lazily to avoid circular/import cost)
        self.optimizer = QueryOptimizer(config, self.db_connector)
        
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
                # Route to QueryOptimizer's MySQL recommendation helper if present
                try:
                    report["recommendations"].extend(await self.optimizer._get_mysql_recommendations(metrics))
                except Exception:
                    # Fallback to local method if available
                    if hasattr(self, "_get_mysql_recommendations"):
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
        

class QueryOptimizer:
    """MySQL-focused query optimizer: slow query capture, EXPLAIN parsing, and suggestions."""

    def __init__(self, config: Config, db_connector: DatabaseConnector):
        self.config = config
        self.db_connector = db_connector

    # ---------- Public APIs ----------
    async def capture_slow_queries(self, db_config: DatabaseConfig, window_minutes: int = 60, top_n: int = 10) -> List[Dict[str, Any]]:
        """Return Top-N queries from MySQL Performance Schema ordered by total time.

        Requires MySQL Performance Schema enabled. Gracefully degrades if unavailable.
        Timers are returned in picoseconds by MySQL; convert to milliseconds.
        """
        if db_config.db_type.lower() != "mysql":
            return []

        try:
            conn = await self.db_connector.get_connection(db_config)
            # Filter by last seen within window; Performance Schema rows are cumulative.
            # We will sort by SUM_TIMER_WAIT and take Top-N.
            query = (
                """
                SELECT 
                  DIGEST,
                  DIGEST_TEXT,
                  COUNT_STAR,
                  SUM_TIMER_WAIT,
                  AVG_TIMER_WAIT,
                  SUM_ROWS_EXAMINED,
                  SUM_ROWS_SENT,
                  FIRST_SEEN,
                  LAST_SEEN
                FROM performance_schema.events_statements_summary_by_digest
                WHERE DIGEST_TEXT IS NOT NULL
                ORDER BY SUM_TIMER_WAIT DESC
                LIMIT %s
                """
            )
            rows = await conn.execute_query(query, (top_n,))
            results: List[Dict[str, Any]] = []
            for r in rows:
                digest, text, count_star, sum_timer_ps, avg_timer_ps, rows_examined, rows_sent, first_seen, last_seen = r
                results.append({
                    "digest": digest,
                    "query": text,
                    "calls": int(count_star or 0),
                    "total_time_ms": self._ps_to_ms(sum_timer_ps),
                    "avg_time_ms": self._ps_to_ms(avg_timer_ps),
                    "rows_examined": int(rows_examined or 0),
                    "rows_sent": int(rows_sent or 0),
                    "first_seen": str(first_seen) if first_seen is not None else None,
                    "last_seen": str(last_seen) if last_seen is not None else None,
                })
            return results
        except Exception as error:
            logger.error(f"Failed to capture slow queries (MySQL): {error}")
            return []

    async def get_top_queries(self, db_config: DatabaseConfig, top_n: int = 10, sort_by: str = "total_time_ms") -> List[Dict[str, Any]]:
        """Wrapper for capture_slow_queries; sort client-side by a given key if needed."""
        items = await self.capture_slow_queries(db_config, top_n=top_n)
        try:
            return sorted(items, key=lambda x: x.get(sort_by, 0), reverse=True)[:top_n]
        except Exception:
            return items

    async def explain_query(self, db_config: DatabaseConfig, sql: str, analyze: bool = False) -> Dict[str, Any]:
        """Run EXPLAIN (FORMAT=JSON) for MySQL. If analyze=True, we still use EXPLAIN only for safety."""
        if db_config.db_type.lower() != "mysql":
            return {"error": "Only MySQL supported in this optimizer"}

        try:
            conn = await self.db_connector.get_connection(db_config)
            explain_sql = f"EXPLAIN FORMAT=JSON {sql}"
            result = await conn.execute_query(explain_sql)
            # MySQL returns a single row with a JSON string in column 0
            plan_json_str = result[0][0] if result and result[0] and len(result[0]) > 0 else "{}"
            plan = json.loads(plan_json_str)
            normalized = self._normalize_mysql_plan(plan)
            normalized["plan_hash"] = self.plan_hash(plan)
            return normalized
        except Exception as error:
            logger.error(f"EXPLAIN failed: {error}")
            return {"error": str(error)}

    async def analyze_query(self, db_config: DatabaseConfig, sql: str) -> Dict[str, Any]:
        """Provide heuristics-based analysis combining EXPLAIN insights and SQL linting."""
        plan = await self.explain_query(db_config, sql, analyze=False)
        issues: List[str] = []
        if plan.get("error"):
            return {"issues": [f"EXPLAIN error: {plan['error']}"], "suggested_rewrites": [], "suggested_indexes": []}

        issues.extend(self._find_plan_antipatterns(plan))
        rewrites = self.suggest_rewrites(db_config, sql, plan)
        indexes = await self.suggest_indexes(db_config, sql, plan)
        return {"issues": issues, "suggested_rewrites": rewrites, "suggested_indexes": indexes, "plan": plan}

    def suggest_rewrites(self, db_config: DatabaseConfig, sql: str, plan: Dict[str, Any] = None) -> List[str]:
        """Static SQL lint rules for common MySQL issues. Returns human-readable suggestions."""
        suggestions: List[str] = []
        sql_compact = re.sub(r"\s+", " ", sql.strip()).lower()

        # Leading wildcard LIKE
        if re.search(r"like\s+'%[\w]", sql_compact):
            suggestions.append("Avoid leading wildcard LIKE; consider full-text index or trigram search.")

        # Functions on columns in WHERE (non-sargable)
        if re.search(r"where\s+.*(lower\(|upper\(|date\(|substr\(|substring\(|cast\()", sql_compact):
            suggestions.append("Avoid functions on indexed columns in WHERE; precompute or index computed value.")

        # ORDER BY + LIMIT without covering index (hint via plan flags)
        if plan:
            for t in plan.get("tables", []):
                if t.get("using_filesort") or t.get("using_temporary"):
                    suggestions.append("ORDER BY/aggregation causes filesort/temp table; add suitable composite index.")
                    break

        # SELECT *
        if re.search(r"select\s+\*\s", sql_compact):
            suggestions.append("Avoid SELECT *; select only needed columns to enable covering indexes.")

        # IN with many literals
        if re.search(r"\sin\s*\((?:\s*\d+\s*,\s*){10,}\d+\s*\)", sql_compact):
            suggestions.append("Large IN (...) list detected; consider temporary table join or batching.")

        return suggestions

    async def suggest_indexes(self, db_config: DatabaseConfig, sql: str, plan: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Suggest basic indexes from plan and WHERE/JOIN conditions.

        Output: list of {ddl, reason, table, columns}
        """
        if db_config.db_type.lower() != "mysql":
            return []

        proposed: List[Dict[str, Any]] = []
        conditions_by_table = self._extract_where_conditions(sql)
        if plan:
            for t in plan.get("tables", []):
                table_name = t.get("table_name")
                access_type = t.get("access_type")
                used_key = t.get("key")
                using_full_scan = (access_type or "").upper() == "ALL"
                using_temp = bool(t.get("using_temporary"))
                using_filesort = bool(t.get("using_filesort"))

                cond_cols = conditions_by_table.get(table_name, [])
                # If full scan and we have equality filter columns, propose index
                if using_full_scan and cond_cols:
                    ddl = self._build_index_ddl(table_name, cond_cols[:3])
                    proposed.append({
                        "table": table_name,
                        "columns": cond_cols[:3],
                        "ddl": ddl,
                        "reason": "Full scan detected with filter; add index on filter columns",
                    })

                # ORDER BY/LIMIT hints
                if using_filesort or using_temp:
                    order_cols = self._extract_order_by_columns(sql)
                    if order_cols:
                        ddl = self._build_index_ddl(table_name, (cond_cols + order_cols)[:3])
                        proposed.append({
                            "table": table_name,
                            "columns": (cond_cols + order_cols)[:3],
                            "ddl": ddl,
                            "reason": "Filesort/temp table; composite index with filter + order columns",
                        })

                # JOIN suggestions: if access_type ALL and attached_condition references equality on join col
                join_cols = self._extract_join_columns(sql, table_name)
                if using_full_scan and join_cols:
                    ddl = self._build_index_ddl(table_name, join_cols[:3])
                    proposed.append({
                        "table": table_name,
                        "columns": join_cols[:3],
                        "ddl": ddl,
                        "reason": "Join on unindexed columns; add index",
                    })

        # Deduplicate by DDL string
        unique: Dict[str, Dict[str, Any]] = {}
        for p in proposed:
            unique[p["ddl"]] = p
        return list(unique.values())

    def plan_hash(self, plan_json: Dict[str, Any]) -> str:
        """Stable hash for a MySQL plan by removing volatile fields."""
        def strip(d: Any) -> Any:
            if isinstance(d, dict):
                clean = {}
                for k, v in d.items():
                    if k in {"query_cost", "cost_info", "est_prefix_rows", "est_rows", "r_loops", "r_total_time_ms"}:
                        continue
                    clean[k] = strip(v)
                return clean
            if isinstance(d, list):
                return [strip(x) for x in d]
            return d

        normalized = json.dumps(strip(plan_json), sort_keys=True)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]

    # ---------- Helpers ----------
    def _ps_to_ms(self, picoseconds: Optional[int]) -> float:
        try:
            return (float(picoseconds) / 1_000_000_000_000.0) if picoseconds is not None else 0.0
        except Exception:
            return 0.0

    def _normalize_mysql_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Flatten MySQL EXPLAIN JSON into a friendly dict with table nodes."""
        tables: List[Dict[str, Any]] = []

        def visit(node: Any):
            if isinstance(node, dict):
                if "table_name" in node or "table" in node:
                    tbl = node.get("table", node)
                    if isinstance(tbl, dict) and (tbl.get("table_name") or node.get("table_name")):
                        tinfo = tbl if "table_name" in tbl else node
                        tables.append({
                            "table_name": tinfo.get("table_name"),
                            "access_type": tinfo.get("access_type"),
                            "key": tinfo.get("key"),
                            "possible_keys": tinfo.get("possible_keys"),
                            "rows_examined_per_scan": tinfo.get("rows_examined_per_scan"),
                            "rows_produced_per_join": tinfo.get("rows_produced_per_join"),
                            "using_temporary": tinfo.get("using_temporary"),
                            "using_filesort": tinfo.get("using_filesort"),
                            "attached_condition": tinfo.get("attached_condition"),
                            "used_key_parts": tinfo.get("used_key_parts"),
                        })
                for v in node.values():
                    visit(v)
            elif isinstance(node, list):
                for item in node:
                    visit(item)

        visit(plan)
        return {"tables": tables, "raw": plan}

    def _extract_where_conditions(self, sql: str) -> Dict[str, List[str]]:
        """Very simple parser to map table -> condition columns (equality preferred)."""
        try:
            where_match = re.search(r"where\s+(.+)$", sql, re.IGNORECASE | re.DOTALL)
            if not where_match:
                return {}
            where = where_match.group(1)
            # stop at ORDER BY / GROUP BY / LIMIT
            where = re.split(r"\border\s+by\b|\bgroup\s+by\b|\blimit\b", where, flags=re.IGNORECASE)[0]
            conds = re.split(r"\band\b|\bor\b", where, flags=re.IGNORECASE)
            table_to_cols: Dict[str, List[str]] = {}
            for c in conds:
                # match alias.column or table.column
                m = re.search(r"([a-zA-Z_][\w]*)\.([a-zA-Z_][\w]*)\s*(=|>|<|>=|<=|in\b)", c)
                if m:
                    table, col = m.group(1), m.group(2)
                    table_to_cols.setdefault(table, []).append(col)
                else:
                    # match standalone column names (less precise)
                    m2 = re.search(r"\b([a-zA-Z_][\w]*)\s*(=|>|<|>=|<=|in\b)", c)
                    if m2:
                        col = m2.group(1)
                        table_to_cols.setdefault("", []).append(col)
            return table_to_cols
        except Exception:
            return {}

    def _extract_order_by_columns(self, sql: str) -> List[str]:
        try:
            m = re.search(r"order\s+by\s+(.+)$", sql, re.IGNORECASE)
            if not m:
                return []
            expr = m.group(1)
            expr = re.split(r"\blimit\b|\bwhere\b|\bgroup\s+by\b", expr, flags=re.IGNORECASE)[0]
            cols = []
            for part in expr.split(','):
                name = part.strip().split()[0]
                # remove alias qualifier if present
                if '.' in name:
                    name = name.split('.')[-1]
                # remove function wrappers
                name = re.sub(r"[()`]", "", name)
                cols.append(name)
            return [c for c in cols if c]
        except Exception:
            return []

    def _extract_join_columns(self, sql: str, table_name: str) -> List[str]:
        try:
            cols: List[str] = []
            # Find ON clauses referencing the table
            for m in re.finditer(r"join\s+([a-zA-Z_][\w]*)\s*(?:as\s*[a-zA-Z_][\w]*)?\s*on\s*([^\n]+)", sql, re.IGNORECASE):
                join_tbl, on_expr = m.group(1), m.group(2)
                if join_tbl.lower() == table_name.lower() or table_name.lower() in on_expr.lower():
                    # capture equality columns: a.col = b.col
                    for eq in re.finditer(r"([a-zA-Z_][\w]*)\.([a-zA-Z_][\w]*)\s*=\s*([a-zA-Z_][\w]*)\.([a-zA-Z_][\w]*)", on_expr):
                        # add the column that belongs to the current table
                        if eq.group(1).lower() == table_name.lower():
                            cols.append(eq.group(2))
                        if eq.group(3).lower() == table_name.lower():
                            cols.append(eq.group(4))
            return cols
        except Exception:
            return []

    def _build_index_ddl(self, table: str, columns: List[str]) -> str:
        cols = ", ".join(f"`{c}`" for c in columns if c)
        idx_name = f"idx_{table}_{'_'.join(columns)[:40]}".replace("`", "")
        return f"CREATE INDEX `{idx_name}` ON `{table}` ({cols});"

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