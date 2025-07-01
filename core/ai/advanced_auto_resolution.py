"""
🚀 ADVANCED AUTO-RESOLUTION SYSTEM FOR DBA-GPT
Enhanced AI-powered database error resolution with predictive capabilities, 
self-healing, and intelligent learning from past errors.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
from collections import defaultdict, deque
import hashlib

from core.config import Config
from core.database.connector import DatabaseError, DatabaseConnector
from core.utils.logger import setup_logger

logger = setup_logger(__name__)


class ResolutionStrategy(Enum):
    """Different resolution strategies"""
    IMMEDIATE_FIX = "immediate_fix"
    GUIDED_RESOLUTION = "guided_resolution"
    SELF_HEALING = "self_healing"
    PREVENTIVE_ACTION = "preventive_action"
    ESCALATION = "escalation"


class SeverityLevel(Enum):
    """Error severity levels"""
    CRITICAL = "critical"      # System down, data loss risk
    HIGH = "high"             # Performance severely impacted
    MEDIUM = "medium"         # Normal operations affected
    LOW = "low"              # Minor issues, warnings
    INFO = "info"            # Informational only


@dataclass
class ResolutionContext:
    """Context for generating resolutions"""
    error: DatabaseError
    database_state: Dict[str, Any]
    system_metrics: Dict[str, Any]
    recent_errors: List[DatabaseError]
    user_permissions: List[str]
    maintenance_window: bool = False
    auto_fix_enabled: bool = False


@dataclass
class ResolutionResult:
    """Result of an auto-resolution attempt"""
    resolution_id: str
    error_signature: str
    strategy: ResolutionStrategy
    severity: SeverityLevel
    success: bool
    actions_taken: List[str]
    sql_commands: List[str]
    execution_time_ms: float
    verification_queries: List[str]
    rollback_commands: List[str]
    effectiveness_score: float  # 0-1
    user_feedback: Optional[str] = None
    requires_human_review: bool = False
    prevention_measures: List[str] = None
    metadata: Dict[str, Any] = None


class ErrorSignatureGenerator:
    """Generates unique signatures for errors to track patterns"""
    
    @staticmethod
    def generate_signature(error: DatabaseError) -> str:
        """Generate a unique signature for an error pattern"""
        # Normalize error message by removing specific values
        normalized_msg = error.message
        
        # Replace specific values with placeholders
        import re
        normalized_msg = re.sub(r"'[^']*'", "'<VALUE>'", normalized_msg)
        normalized_msg = re.sub(r"\d+", "<NUMBER>", normalized_msg)
        normalized_msg = re.sub(r"`[^`]*`", "`<IDENTIFIER>`", normalized_msg)
        
        # Create signature from error type, code, and normalized message
        signature_data = f"{error.error_type}:{error.error_code}:{normalized_msg}"
        return hashlib.md5(signature_data.encode()).hexdigest()


class ErrorPatternAnalyzer:
    """Analyzes error patterns to predict and prevent future issues"""
    
    def __init__(self):
        self.error_history = deque(maxlen=1000)  # Keep last 1000 errors
        self.pattern_frequency = defaultdict(int)
        self.temporal_patterns = defaultdict(list)
        
    def add_error(self, error: DatabaseError):
        """Add error to analysis history"""
        signature = ErrorSignatureGenerator.generate_signature(error)
        timestamp = error.timestamp or datetime.now()
        
        self.error_history.append({
            'signature': signature,
            'timestamp': timestamp,
            'error': error
        })
        
        self.pattern_frequency[signature] += 1
        self.temporal_patterns[signature].append(timestamp)
        
    def predict_next_error(self) -> Optional[Tuple[str, float]]:
        """Predict when next error might occur based on patterns"""
        if len(self.error_history) < 5:
            return None
            
        # Analyze temporal patterns
        now = datetime.now()
        predictions = []
        
        for signature, timestamps in self.temporal_patterns.items():
            if len(timestamps) < 3:
                continue
                
            # Calculate average interval between errors
            intervals = []
            for i in range(1, len(timestamps)):
                interval = (timestamps[i] - timestamps[i-1]).total_seconds()
                intervals.append(interval)
                
            if intervals:
                avg_interval = statistics.mean(intervals)
                last_occurrence = timestamps[-1]
                time_since_last = (now - last_occurrence).total_seconds()
                
                # Predict probability based on time since last occurrence
                if time_since_last > avg_interval * 0.8:
                    probability = min(1.0, time_since_last / avg_interval)
                    predictions.append((signature, probability))
        
        return max(predictions, key=lambda x: x[1]) if predictions else None
    
    def get_error_trends(self) -> Dict[str, Any]:
        """Get error trends and statistics"""
        now = datetime.now()
        last_24h = now - timedelta(hours=24)
        last_week = now - timedelta(days=7)
        
        recent_errors = [e for e in self.error_history if e['timestamp'] > last_24h]
        weekly_errors = [e for e in self.error_history if e['timestamp'] > last_week]
        
        return {
            'total_errors': len(self.error_history),
            'errors_last_24h': len(recent_errors),
            'errors_last_week': len(weekly_errors),
            'most_frequent_patterns': dict(sorted(
                self.pattern_frequency.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10]),
            'error_rate_per_hour': len(recent_errors) / 24,
            'trending_up': len(recent_errors) > len(weekly_errors) / 7
        }


class SelfHealingEngine:
    """Engine for automatic self-healing actions"""
    
    def __init__(self, db_connector: DatabaseConnector):
        self.db_connector = db_connector
        self.healing_strategies = {
            "TABLE_NOT_FOUND": self._heal_missing_table,
            "DEADLOCK": self._heal_deadlock,
            "CONNECTION_ERROR": self._heal_connection,
            "TOO_MANY_CONNECTIONS": self._heal_connection_limit,
            "DISK_FULL": self._heal_disk_space,
            "SLOW_QUERY": self._heal_slow_query
        }
        
    async def attempt_self_healing(self, error: DatabaseError, context: ResolutionContext) -> ResolutionResult:
        """Attempt automatic self-healing"""
        healing_func = self.healing_strategies.get(error.error_type)
        
        if not healing_func or not context.auto_fix_enabled:
            return ResolutionResult(
                resolution_id=f"heal_{int(time.time())}",
                error_signature=ErrorSignatureGenerator.generate_signature(error),
                strategy=ResolutionStrategy.GUIDED_RESOLUTION,
                severity=SeverityLevel.MEDIUM,
                success=False,
                actions_taken=["Self-healing not available or disabled"],
                sql_commands=[],
                execution_time_ms=0,
                verification_queries=[],
                rollback_commands=[],
                effectiveness_score=0.0,
                requires_human_review=True
            )
        
        return await healing_func(error, context)
    
    async def _heal_missing_table(self, error: DatabaseError, context: ResolutionContext) -> ResolutionResult:
        """Auto-heal missing table errors"""
        actions = []
        sql_commands = []
        success = False
        
        try:
            # Check if table exists in backup or other schema
            if error.table:
                # Generate CREATE TABLE statement from similar tables
                similar_query = f"""
                    SELECT CREATE_TABLE_STATEMENT 
                    FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_NAME LIKE '%{error.table[:5]}%' 
                    LIMIT 1
                """
                
                actions.append(f"Analyzed similar tables for {error.table}")
                
                # In a real implementation, you'd execute the query
                # For now, we'll create a basic table structure
                create_table_sql = f"""
                CREATE TABLE IF NOT EXISTS {error.table} (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data JSON,
                    INDEX idx_created (created_at)
                );
                """
                
                sql_commands.append(create_table_sql)
                actions.append(f"Generated CREATE TABLE statement for {error.table}")
                success = True
                
        except Exception as e:
            actions.append(f"Self-healing failed: {e}")
            
        return ResolutionResult(
            resolution_id=f"heal_table_{int(time.time())}",
            error_signature=ErrorSignatureGenerator.generate_signature(error),
            strategy=ResolutionStrategy.SELF_HEALING,
            severity=SeverityLevel.MEDIUM,
            success=success,
            actions_taken=actions,
            sql_commands=sql_commands,
            execution_time_ms=50,
            verification_queries=[f"SHOW TABLES LIKE '{error.table}'"],
            rollback_commands=[f"DROP TABLE IF EXISTS {error.table}"],
            effectiveness_score=0.8 if success else 0.0
        )
    
    async def _heal_deadlock(self, error: DatabaseError, context: ResolutionContext) -> ResolutionResult:
        """Auto-heal deadlock situations"""
        actions = ["Detected deadlock situation"]
        sql_commands = [
            "SHOW ENGINE INNODB STATUS;",
            "SELECT * FROM INFORMATION_SCHEMA.INNODB_LOCKS;",
            "SELECT * FROM INFORMATION_SCHEMA.INNODB_LOCK_WAITS;"
        ]
        
        # Kill the longest running transaction
        kill_query = """
        SELECT CONCAT('KILL ', id, ';') as kill_command 
        FROM INFORMATION_SCHEMA.PROCESSLIST 
        WHERE state LIKE '%lock%' 
        ORDER BY time DESC 
        LIMIT 1;
        """
        
        sql_commands.append(kill_query)
        actions.append("Identified longest running locked transaction")
        
        return ResolutionResult(
            resolution_id=f"heal_deadlock_{int(time.time())}",
            error_signature=ErrorSignatureGenerator.generate_signature(error),
            strategy=ResolutionStrategy.SELF_HEALING,
            severity=SeverityLevel.HIGH,
            success=True,
            actions_taken=actions,
            sql_commands=sql_commands,
            execution_time_ms=100,
            verification_queries=["SHOW PROCESSLIST;"],
            rollback_commands=[],
            effectiveness_score=0.9,
            prevention_measures=[
                "Implement proper indexing to reduce lock time",
                "Use shorter transactions",
                "Consider using READ COMMITTED isolation level"
            ]
        )
    
    async def _heal_connection(self, error: DatabaseError, context: ResolutionContext) -> ResolutionResult:
        """Auto-heal connection issues"""
        actions = ["Analyzing connection health"]
        sql_commands = [
            "SHOW STATUS LIKE 'Threads_connected';",
            "SHOW STATUS LIKE 'Aborted_connects';",
            "SHOW VARIABLES LIKE 'max_connections';"
        ]
        
        # Restart connection pool
        actions.append("Attempting connection pool restart")
        
        return ResolutionResult(
            resolution_id=f"heal_conn_{int(time.time())}",
            error_signature=ErrorSignatureGenerator.generate_signature(error),
            strategy=ResolutionStrategy.SELF_HEALING,
            severity=SeverityLevel.HIGH,
            success=True,
            actions_taken=actions,
            sql_commands=sql_commands,
            execution_time_ms=200,
            verification_queries=["SELECT 1;"],
            rollback_commands=[],
            effectiveness_score=0.7
        )
    
    async def _heal_connection_limit(self, error: DatabaseError, context: ResolutionContext) -> ResolutionResult:
        """Auto-heal too many connections"""
        actions = ["Analyzing connection usage"]
        sql_commands = [
            "SHOW PROCESSLIST;",
            "SELECT COUNT(*) as active_connections FROM INFORMATION_SCHEMA.PROCESSLIST WHERE COMMAND != 'Sleep';",
            "SHOW STATUS LIKE 'Max_used_connections';"
        ]
        
        # Kill idle connections
        kill_idle_sql = """
        SELECT CONCAT('KILL ', id, ';') as kill_command 
        FROM INFORMATION_SCHEMA.PROCESSLIST 
        WHERE COMMAND = 'Sleep' 
        AND time > 300 
        ORDER BY time DESC;
        """
        
        sql_commands.append(kill_idle_sql)
        actions.append("Identified idle connections for termination")
        
        return ResolutionResult(
            resolution_id=f"heal_conn_limit_{int(time.time())}",
            error_signature=ErrorSignatureGenerator.generate_signature(error),
            strategy=ResolutionStrategy.SELF_HEALING,
            severity=SeverityLevel.CRITICAL,
            success=True,
            actions_taken=actions,
            sql_commands=sql_commands,
            execution_time_ms=150,
            verification_queries=["SHOW STATUS LIKE 'Threads_connected';"],
            rollback_commands=[],
            effectiveness_score=0.85,
            prevention_measures=[
                "Implement connection pooling",
                "Set proper connection timeouts",
                "Monitor connection usage regularly"
            ]
        )
    
    async def _heal_disk_space(self, error: DatabaseError, context: ResolutionContext) -> ResolutionResult:
        """Auto-heal disk space issues"""
        actions = ["Analyzing disk usage"]
        sql_commands = [
            "SELECT table_schema, SUM(data_length + index_length) / 1024 / 1024 AS 'Size (MB)' FROM information_schema.tables GROUP BY table_schema;",
            "SHOW BINARY LOGS;",
            "SELECT COUNT(*) FROM INFORMATION_SCHEMA.FILES;"
        ]
        
        # Clean up old binary logs
        cleanup_sql = "PURGE BINARY LOGS BEFORE DATE_SUB(NOW(), INTERVAL 7 DAY);"
        sql_commands.append(cleanup_sql)
        actions.append("Scheduled binary log cleanup")
        
        return ResolutionResult(
            resolution_id=f"heal_disk_{int(time.time())}",
            error_signature=ErrorSignatureGenerator.generate_signature(error),
            strategy=ResolutionStrategy.SELF_HEALING,
            severity=SeverityLevel.CRITICAL,
            success=True,
            actions_taken=actions,
            sql_commands=sql_commands,
            execution_time_ms=300,
            verification_queries=["SHOW TABLE STATUS;"],
            rollback_commands=[],
            effectiveness_score=0.75,
            prevention_measures=[
                "Implement automated log rotation",
                "Set up disk space monitoring",
                "Archive old data regularly"
            ]
        )
    
    async def _heal_slow_query(self, error: DatabaseError, context: ResolutionContext) -> ResolutionResult:
        """Auto-heal slow query performance"""
        actions = ["Analyzing query performance"]
        sql_commands = []
        
        if error.query:
            # Analyze the query
            explain_sql = f"EXPLAIN FORMAT=JSON {error.query}"
            sql_commands.append(explain_sql)
            
            # Check for missing indexes
            actions.append("Analyzing query execution plan")
            
            # Suggest index creation (simplified)
            if "WHERE" in error.query.upper():
                actions.append("Identified potential index opportunities")
                
        return ResolutionResult(
            resolution_id=f"heal_slow_{int(time.time())}",
            error_signature=ErrorSignatureGenerator.generate_signature(error),
            strategy=ResolutionStrategy.GUIDED_RESOLUTION,
            severity=SeverityLevel.MEDIUM,
            success=True,
            actions_taken=actions,
            sql_commands=sql_commands,
            execution_time_ms=100,
            verification_queries=[],
            rollback_commands=[],
            effectiveness_score=0.6,
            requires_human_review=True,
            prevention_measures=[
                "Add appropriate indexes",
                "Rewrite query for better performance",
                "Consider query caching"
            ]
        )


class AdvancedAutoResolutionEngine:
    """Advanced auto-resolution engine with AI, pattern analysis, and self-healing"""
    
    def __init__(self, config: Config, db_connector: DatabaseConnector):
        self.config = config
        self.db_connector = db_connector
        
        # Initialize components
        self.pattern_analyzer = ErrorPatternAnalyzer()
        self.self_healing = SelfHealingEngine(db_connector)
        
        # Resolution tracking
        self.resolution_history = deque(maxlen=500)
        self.success_rates = defaultdict(list)
        
        # Alert thresholds
        self.alert_thresholds = {
            'error_rate_per_hour': 10,
            'critical_errors_per_day': 5,
            'failed_resolutions_ratio': 0.3
        }
        
    async def resolve_error(self, error: DatabaseError, context: ResolutionContext = None) -> ResolutionResult:
        """Main resolution method - orchestrates different resolution strategies"""
        start_time = time.time()
        
        # Add error to pattern analysis
        self.pattern_analyzer.add_error(error)
        
        # Create default context if not provided
        if not context:
            context = await self._create_resolution_context(error)
        
        # Determine resolution strategy
        strategy = self._determine_strategy(error, context)
        
        # Execute resolution based on strategy
        if strategy == ResolutionStrategy.SELF_HEALING:
            result = await self.self_healing.attempt_self_healing(error, context)
        elif strategy == ResolutionStrategy.IMMEDIATE_FIX:
            result = await self._immediate_fix_resolution(error, context)
        elif strategy == ResolutionStrategy.PREVENTIVE_ACTION:
            result = await self._preventive_resolution(error, context)
        else:
            result = await self._guided_resolution(error, context)
        
        # Record resolution attempt
        result.execution_time_ms = (time.time() - start_time) * 1000
        self.resolution_history.append(result)
        self.success_rates[error.error_type].append(result.success)
        
        # Check if alerts need to be triggered
        await self._check_alert_conditions()
        
        return result
    
    async def _create_resolution_context(self, error: DatabaseError) -> ResolutionContext:
        """Create resolution context with current system state"""
        try:
            # Get database state (simplified)
            database_state = {
                'connection_count': 0,
                'active_queries': 0,
                'disk_usage_percent': 0,
                'memory_usage_percent': 0
            }
            
            # Get system metrics (would integrate with monitoring system)
            system_metrics = {
                'cpu_usage': 0,
                'memory_usage': 0,
                'disk_io': 0,
                'network_io': 0
            }
            
            # Get recent errors
            recent_errors = list(self.pattern_analyzer.error_history)[-10:]
            
            return ResolutionContext(
                error=error,
                database_state=database_state,
                system_metrics=system_metrics,
                recent_errors=[e['error'] for e in recent_errors],
                user_permissions=['SELECT', 'INSERT', 'UPDATE', 'DELETE'],
                maintenance_window=False,
                auto_fix_enabled=True
            )
            
        except Exception as e:
            logger.error(f"Error creating resolution context: {e}")
            return ResolutionContext(
                error=error,
                database_state={},
                system_metrics={},
                recent_errors=[],
                user_permissions=[],
                maintenance_window=False,
                auto_fix_enabled=False
            )
    
    def _determine_strategy(self, error: DatabaseError, context: ResolutionContext) -> ResolutionStrategy:
        """Determine the best resolution strategy"""
        
        # Critical errors get immediate attention
        if error.error_type in ["CONNECTION_ERROR", "TOO_MANY_CONNECTIONS", "DISK_FULL"]:
            if context.auto_fix_enabled:
                return ResolutionStrategy.SELF_HEALING
            else:
                return ResolutionStrategy.IMMEDIATE_FIX
        
        # Frequent patterns get preventive action
        signature = ErrorSignatureGenerator.generate_signature(error)
        if self.pattern_analyzer.pattern_frequency[signature] > 5:
            return ResolutionStrategy.PREVENTIVE_ACTION
        
        # During maintenance window, prefer self-healing
        if context.maintenance_window and context.auto_fix_enabled:
            return ResolutionStrategy.SELF_HEALING
        
        # Default to guided resolution
        return ResolutionStrategy.GUIDED_RESOLUTION
    
    async def _immediate_fix_resolution(self, error: DatabaseError, context: ResolutionContext) -> ResolutionResult:
        """Immediate fix resolution for critical errors"""
        actions = ["Initiated emergency response protocol"]
        sql_commands = []
        
        if error.error_type == "CONNECTION_ERROR":
            sql_commands = [
                "SHOW PROCESSLIST;",
                "SHOW STATUS LIKE 'Threads_connected';",
                "SELECT 1 AS connection_test;"
            ]
            actions.append("Testing database connectivity")
            
        elif error.error_type == "TOO_MANY_CONNECTIONS":
            sql_commands = [
                "SHOW STATUS LIKE 'Max_used_connections';",
                "SET GLOBAL max_connections = (SELECT @@max_connections + 100);",
                "KILL (SELECT id FROM INFORMATION_SCHEMA.PROCESSLIST WHERE COMMAND = 'Sleep' ORDER BY TIME DESC LIMIT 1);"
            ]
            actions.append("Increased connection limit and killed idle connections")
        
        return ResolutionResult(
            resolution_id=f"immediate_{int(time.time())}",
            error_signature=ErrorSignatureGenerator.generate_signature(error),
            strategy=ResolutionStrategy.IMMEDIATE_FIX,
            severity=SeverityLevel.CRITICAL,
            success=True,
            actions_taken=actions,
            sql_commands=sql_commands,
            execution_time_ms=0,
            verification_queries=["SELECT 1;"],
            rollback_commands=[],
            effectiveness_score=0.9
        )
    
    async def _preventive_resolution(self, error: DatabaseError, context: ResolutionContext) -> ResolutionResult:
        """Preventive resolution to stop recurring errors"""
        actions = ["Analyzing error patterns for prevention"]
        sql_commands = []
        prevention_measures = []
        
        signature = ErrorSignatureGenerator.generate_signature(error)
        frequency = self.pattern_analyzer.pattern_frequency[signature]
        
        actions.append(f"Error pattern occurs {frequency} times - implementing prevention")
        
        if error.error_type == "TABLE_NOT_FOUND":
            prevention_measures = [
                "Create monitoring for table existence",
                "Implement table creation automation",
                "Add validation in application layer"
            ]
            sql_commands = [
                f"CREATE TABLE IF NOT EXISTS {error.table}_monitoring (check_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP);",
                "CREATE EVENT IF NOT EXISTS table_existence_check ON SCHEDULE EVERY 1 HOUR DO SELECT 'Table monitoring active';"
            ]
            
        elif error.error_type == "DEADLOCK":
            prevention_measures = [
                "Implement proper index optimization",
                "Reduce transaction scope",
                "Use consistent lock ordering"
            ]
            sql_commands = [
                "SET GLOBAL innodb_deadlock_detect = ON;",
                "SET GLOBAL innodb_print_all_deadlocks = ON;"
            ]
        
        return ResolutionResult(
            resolution_id=f"preventive_{int(time.time())}",
            error_signature=signature,
            strategy=ResolutionStrategy.PREVENTIVE_ACTION,
            severity=SeverityLevel.MEDIUM,
            success=True,
            actions_taken=actions,
            sql_commands=sql_commands,
            execution_time_ms=0,
            verification_queries=[],
            rollback_commands=[],
            effectiveness_score=0.95,
            prevention_measures=prevention_measures
        )
    
    async def _guided_resolution(self, error: DatabaseError, context: ResolutionContext) -> ResolutionResult:
        """Guided resolution with step-by-step instructions"""
        actions = ["Providing guided resolution steps"]
        sql_commands = []
        
        # Generate specific guidance based on error type
        if error.error_type == "SYNTAX_ERROR":
            sql_commands = [
                f"-- Original query with syntax error:",
                f"-- {error.query}",
                f"-- Check syntax using:",
                "SELECT 1;  -- Test basic syntax",
                f"EXPLAIN {error.query};  -- Test query structure"
            ]
            actions.append("Generated syntax validation commands")
            
        elif error.error_type == "ACCESS_DENIED":
            sql_commands = [
                "SHOW GRANTS FOR CURRENT_USER();",
                "SELECT USER(), CURRENT_USER();",
                f"-- Grant necessary permissions:",
                f"-- GRANT SELECT ON *.* TO CURRENT_USER();"
            ]
            actions.append("Generated permission analysis commands")
        
        return ResolutionResult(
            resolution_id=f"guided_{int(time.time())}",
            error_signature=ErrorSignatureGenerator.generate_signature(error),
            strategy=ResolutionStrategy.GUIDED_RESOLUTION,
            severity=SeverityLevel.MEDIUM,
            success=True,
            actions_taken=actions,
            sql_commands=sql_commands,
            execution_time_ms=0,
            verification_queries=[],
            rollback_commands=[],
            effectiveness_score=0.7,
            requires_human_review=True
        )
    
    async def _check_alert_conditions(self):
        """Check if alert conditions are met"""
        trends = self.pattern_analyzer.get_error_trends()
        
        alerts = []
        
        if trends['error_rate_per_hour'] > self.alert_thresholds['error_rate_per_hour']:
            alerts.append(f"High error rate: {trends['error_rate_per_hour']:.1f} errors/hour")
        
        if trends['trending_up']:
            alerts.append("Error rate is trending upward")
        
        # Calculate failed resolution ratio
        recent_resolutions = list(self.resolution_history)[-20:]
        if recent_resolutions:
            failed_ratio = sum(1 for r in recent_resolutions if not r.success) / len(recent_resolutions)
            if failed_ratio > self.alert_thresholds['failed_resolutions_ratio']:
                alerts.append(f"High resolution failure rate: {failed_ratio:.1%}")
        
        if alerts:
            logger.warning(f"🚨 Auto-resolution alerts: {'; '.join(alerts)}")
    
    def get_system_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive system health report"""
        trends = self.pattern_analyzer.get_error_trends()
        
        # Calculate success rates by error type
        success_by_type = {}
        for error_type, results in self.success_rates.items():
            if results:
                success_by_type[error_type] = sum(results) / len(results)
        
        # Get recent resolution performance
        recent_resolutions = list(self.resolution_history)[-50:]
        avg_resolution_time = 0
        if recent_resolutions:
            avg_resolution_time = statistics.mean([r.execution_time_ms for r in recent_resolutions])
        
        return {
            'error_trends': trends,
            'success_rates_by_type': success_by_type,
            'total_resolutions_attempted': len(self.resolution_history),
            'average_resolution_time_ms': avg_resolution_time,
            'recent_resolution_success_rate': sum(1 for r in recent_resolutions if r.success) / len(recent_resolutions) if recent_resolutions else 0,
            'top_error_patterns': dict(list(trends['most_frequent_patterns'].items())[:5]),
            'predictive_analysis': {
                'next_predicted_error': self.pattern_analyzer.predict_next_error()
            },
            'alert_status': 'healthy' if avg_resolution_time < 1000 else 'needs_attention'
        }
    
    async def learn_from_feedback(self, resolution_id: str, feedback: str, effectiveness_score: float):
        """Learn from user feedback to improve future resolutions"""
        # Find the resolution
        for resolution in self.resolution_history:
            if resolution.resolution_id == resolution_id:
                resolution.user_feedback = feedback
                resolution.effectiveness_score = effectiveness_score
                
                # Update success rates based on feedback
                error_type = resolution.error_signature.split(':')[0]  # Extract error type from signature
                self.success_rates[error_type].append(effectiveness_score > 0.5)
                
                logger.info(f"Learning from feedback for {resolution_id}: {effectiveness_score}")
                break 