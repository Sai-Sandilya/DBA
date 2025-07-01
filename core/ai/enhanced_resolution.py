"""
Enhanced Auto-Resolution System for DBA-GPT
Advanced AI-powered database error resolution with self-healing capabilities
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import hashlib
from collections import defaultdict, deque

from core.config import Config
from core.database.connector import DatabaseError, DatabaseConnector
from core.utils.logger import setup_logger

logger = setup_logger(__name__)


class ResolutionStrategy(Enum):
    IMMEDIATE_FIX = "immediate_fix"
    SELF_HEALING = "self_healing"
    PREVENTIVE_ACTION = "preventive_action"
    GUIDED_RESOLUTION = "guided_resolution"


@dataclass
class EnhancedResolution:
    """Enhanced resolution with more intelligence"""
    resolution_id: str
    error_signature: str
    strategy: ResolutionStrategy
    success: bool
    actions_taken: List[str]
    sql_commands: List[str]
    execution_time_ms: float
    verification_queries: List[str]
    rollback_commands: List[str]
    effectiveness_score: float
    prevention_measures: List[str]
    requires_human_review: bool = False
    auto_executed: bool = False


class ErrorPatternAnalyzer:
    """Analyzes error patterns to improve resolution"""
    
    def __init__(self):
        self.error_history = deque(maxlen=1000)
        self.pattern_frequency = defaultdict(int)
        
    def add_error(self, error: DatabaseError):
        """Add error to analysis"""
        signature = self._generate_signature(error)
        self.error_history.append({
            'signature': signature,
            'timestamp': datetime.now(),
            'error': error
        })
        self.pattern_frequency[signature] += 1
        
    def _generate_signature(self, error: DatabaseError) -> str:
        """Generate unique signature for error pattern"""
        import re
        normalized_msg = error.message
        normalized_msg = re.sub(r"'[^']*'", "'<VALUE>'", normalized_msg)
        normalized_msg = re.sub(r"\d+", "<NUMBER>", normalized_msg)
        
        signature_data = f"{error.error_type}:{error.error_code}:{normalized_msg}"
        return hashlib.md5(signature_data.encode()).hexdigest()[:12]
    
    def get_error_trends(self) -> Dict[str, Any]:
        """Get error trends and statistics"""
        now = datetime.now()
        last_24h = now - timedelta(hours=24)
        
        recent_errors = [e for e in self.error_history if e['timestamp'] > last_24h]
        
        return {
            'total_errors': len(self.error_history),
            'errors_last_24h': len(recent_errors),
            'most_frequent_patterns': dict(sorted(
                self.pattern_frequency.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]),
            'error_rate_per_hour': len(recent_errors) / 24,
        }


class SelfHealingEngine:
    """Engine for automatic self-healing actions"""
    
    def __init__(self, db_connector: DatabaseConnector):
        self.db_connector = db_connector
        
    async def attempt_healing(self, error: DatabaseError) -> EnhancedResolution:
        """Attempt automatic self-healing"""
        start_time = time.time()
        
        if error.error_type == "TABLE_NOT_FOUND":
            return await self._heal_missing_table(error, start_time)
        elif error.error_type == "DEADLOCK":
            return await self._heal_deadlock(error, start_time)
        elif error.error_type == "CONNECTION_ERROR":
            return await self._heal_connection(error, start_time)
        elif error.error_type == "TOO_MANY_CONNECTIONS":
            return await self._heal_connection_limit(error, start_time)
        else:
            return await self._default_healing(error, start_time)
    
    async def _heal_missing_table(self, error: DatabaseError, start_time: float) -> EnhancedResolution:
        """Auto-heal missing table errors"""
        actions = [f"Detected missing table: {error.table}"]
        sql_commands = []
        
        if error.table:
            # Create basic table structure
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
            
        return EnhancedResolution(
            resolution_id=f"heal_table_{int(time.time())}",
            error_signature=self._generate_signature(error),
            strategy=ResolutionStrategy.SELF_HEALING,
            success=True,
            actions_taken=actions,
            sql_commands=sql_commands,
            execution_time_ms=(time.time() - start_time) * 1000,
            verification_queries=[f"SHOW TABLES LIKE '{error.table}'"],
            rollback_commands=[f"DROP TABLE IF EXISTS {error.table}"],
            effectiveness_score=0.8,
            prevention_measures=[
                "Implement table existence validation",
                "Add application-level checks",
                "Create table creation automation"
            ],
            auto_executed=False
        )
    
    async def _heal_deadlock(self, error: DatabaseError, start_time: float) -> EnhancedResolution:
        """Auto-heal deadlock situations"""
        actions = ["Detected deadlock situation", "Analyzing lock dependencies"]
        sql_commands = [
            "SHOW ENGINE INNODB STATUS;",
            "SELECT * FROM INFORMATION_SCHEMA.INNODB_LOCKS;",
            "SELECT * FROM INFORMATION_SCHEMA.INNODB_LOCK_WAITS;",
            """
            SELECT CONCAT('KILL ', id, ';') as kill_command 
            FROM INFORMATION_SCHEMA.PROCESSLIST 
            WHERE state LIKE '%lock%' 
            ORDER BY time DESC 
            LIMIT 1;
            """
        ]
        
        return EnhancedResolution(
            resolution_id=f"heal_deadlock_{int(time.time())}",
            error_signature=self._generate_signature(error),
            strategy=ResolutionStrategy.SELF_HEALING,
            success=True,
            actions_taken=actions,
            sql_commands=sql_commands,
            execution_time_ms=(time.time() - start_time) * 1000,
            verification_queries=["SHOW PROCESSLIST;"],
            rollback_commands=[],
            effectiveness_score=0.9,
            prevention_measures=[
                "Optimize indexing to reduce lock time",
                "Use shorter transactions", 
                "Implement consistent lock ordering",
                "Consider READ COMMITTED isolation level"
            ]
        )
    
    async def _heal_connection(self, error: DatabaseError, start_time: float) -> EnhancedResolution:
        """Auto-heal connection issues"""
        actions = ["Analyzing connection health", "Testing connectivity"]
        sql_commands = [
            "SELECT 1 AS connection_test;",
            "SHOW STATUS LIKE 'Threads_connected';",
            "SHOW STATUS LIKE 'Aborted_connects';",
            "SHOW VARIABLES LIKE 'max_connections';"
        ]
        
        return EnhancedResolution(
            resolution_id=f"heal_conn_{int(time.time())}",
            error_signature=self._generate_signature(error),
            strategy=ResolutionStrategy.SELF_HEALING,
            success=True,
            actions_taken=actions,
            sql_commands=sql_commands,
            execution_time_ms=(time.time() - start_time) * 1000,
            verification_queries=["SELECT 1;"],
            rollback_commands=[],
            effectiveness_score=0.7,
            prevention_measures=[
                "Implement connection pooling",
                "Set proper connection timeouts",
                "Monitor connection health regularly"
            ]
        )
    
    async def _heal_connection_limit(self, error: DatabaseError, start_time: float) -> EnhancedResolution:
        """Auto-heal too many connections"""
        actions = ["Connection limit exceeded", "Analyzing connection usage"]
        sql_commands = [
            "SHOW PROCESSLIST;",
            "SELECT COUNT(*) as active_connections FROM INFORMATION_SCHEMA.PROCESSLIST WHERE COMMAND != 'Sleep';",
            "SHOW STATUS LIKE 'Max_used_connections';",
            """
            SELECT CONCAT('KILL ', id, ';') as kill_command 
            FROM INFORMATION_SCHEMA.PROCESSLIST 
            WHERE COMMAND = 'Sleep' 
            AND time > 300 
            ORDER BY time DESC 
            LIMIT 5;
            """
        ]
        
        return EnhancedResolution(
            resolution_id=f"heal_conn_limit_{int(time.time())}",
            error_signature=self._generate_signature(error),
            strategy=ResolutionStrategy.SELF_HEALING,
            success=True,
            actions_taken=actions,
            sql_commands=sql_commands,
            execution_time_ms=(time.time() - start_time) * 1000,
            verification_queries=["SHOW STATUS LIKE 'Threads_connected';"],
            rollback_commands=[],
            effectiveness_score=0.85,
            prevention_measures=[
                "Implement connection pooling",
                "Set connection limits per user",
                "Kill idle connections automatically",
                "Monitor connection usage patterns"
            ]
        )
    
    async def _default_healing(self, error: DatabaseError, start_time: float) -> EnhancedResolution:
        """Default healing for unsupported error types"""
        return EnhancedResolution(
            resolution_id=f"heal_default_{int(time.time())}",
            error_signature=self._generate_signature(error),
            strategy=ResolutionStrategy.GUIDED_RESOLUTION,
            success=False,
            actions_taken=["Self-healing not available for this error type"],
            sql_commands=[],
            execution_time_ms=(time.time() - start_time) * 1000,
            verification_queries=[],
            rollback_commands=[],
            effectiveness_score=0.0,
            prevention_measures=[],
            requires_human_review=True
        )
    
    def _generate_signature(self, error: DatabaseError) -> str:
        """Generate signature for error"""
        import re
        normalized_msg = error.message
        normalized_msg = re.sub(r"'[^']*'", "'<VALUE>'", normalized_msg)
        normalized_msg = re.sub(r"\d+", "<NUMBER>", normalized_msg)
        
        signature_data = f"{error.error_type}:{error.error_code}:{normalized_msg}"
        return hashlib.md5(signature_data.encode()).hexdigest()[:12]


class EnhancedAutoResolution:
    """Enhanced auto-resolution system with advanced capabilities"""
    
    def __init__(self, config: Config, db_connector: DatabaseConnector):
        self.config = config
        self.db_connector = db_connector
        self.pattern_analyzer = ErrorPatternAnalyzer()
        self.self_healing = SelfHealingEngine(db_connector)
        self.resolution_history = deque(maxlen=200)
        
        # Success tracking
        self.success_rates = defaultdict(list)
        
        # Configuration
        self.auto_healing_enabled = True
        self.alert_threshold = 5  # errors per hour
        
    async def resolve_error_enhanced(self, error: DatabaseError) -> EnhancedResolution:
        """Enhanced error resolution with multiple strategies"""
        
        # Add to pattern analysis
        self.pattern_analyzer.add_error(error)
        
        # Determine resolution strategy
        strategy = self._determine_strategy(error)
        
        # Execute resolution
        if strategy == ResolutionStrategy.SELF_HEALING and self.auto_healing_enabled:
            result = await self.self_healing.attempt_healing(error)
        elif strategy == ResolutionStrategy.PREVENTIVE_ACTION:
            result = await self._preventive_resolution(error)
        elif strategy == ResolutionStrategy.IMMEDIATE_FIX:
            result = await self._immediate_fix_resolution(error)
        else:
            result = await self._guided_resolution(error)
        
        # Track resolution
        self.resolution_history.append(result)
        self.success_rates[error.error_type].append(result.success)
        
        # Check for alerts
        await self._check_alerts()
        
        return result
    
    def _determine_strategy(self, error: DatabaseError) -> ResolutionStrategy:
        """Determine best resolution strategy"""
        
        # Critical errors get immediate attention
        if error.error_type in ["CONNECTION_ERROR", "TOO_MANY_CONNECTIONS"]:
            return ResolutionStrategy.SELF_HEALING
        
        # Check if this is a frequent pattern
        signature = self.pattern_analyzer._generate_signature(error)
        frequency = self.pattern_analyzer.pattern_frequency[signature]
        
        if frequency > 3:  # Frequent pattern
            return ResolutionStrategy.PREVENTIVE_ACTION
        
        # Self-healing for known fixable errors
        if error.error_type in ["TABLE_NOT_FOUND", "DEADLOCK"]:
            return ResolutionStrategy.SELF_HEALING
        
        # Default to guided resolution
        return ResolutionStrategy.GUIDED_RESOLUTION
    
    async def _preventive_resolution(self, error: DatabaseError) -> EnhancedResolution:
        """Preventive resolution for recurring errors"""
        start_time = time.time()
        
        actions = ["Implementing preventive measures for recurring error"]
        sql_commands = []
        prevention_measures = []
        
        if error.error_type == "TABLE_NOT_FOUND":
            prevention_measures = [
                "Create table existence monitoring",
                "Implement automatic table creation",
                "Add application validation layer"
            ]
            sql_commands = [
                f"CREATE EVENT IF NOT EXISTS monitor_{error.table} ON SCHEDULE EVERY 1 HOUR DO SELECT 'Monitoring {error.table}';",
                f"CREATE TABLE IF NOT EXISTS {error.table}_backup LIKE {error.table};" if error.table else ""
            ]
        
        elif error.error_type == "DEADLOCK":
            prevention_measures = [
                "Optimize query execution plans",
                "Implement consistent resource ordering",
                "Add deadlock detection monitoring"
            ]
            sql_commands = [
                "SET GLOBAL innodb_deadlock_detect = ON;",
                "SET GLOBAL innodb_print_all_deadlocks = ON;",
                "CREATE EVENT deadlock_monitor ON SCHEDULE EVERY 15 MINUTE DO SELECT 'Deadlock monitoring active';"
            ]
        
        return EnhancedResolution(
            resolution_id=f"preventive_{int(time.time())}",
            error_signature=self.pattern_analyzer._generate_signature(error),
            strategy=ResolutionStrategy.PREVENTIVE_ACTION,
            success=True,
            actions_taken=actions,
            sql_commands=sql_commands,
            execution_time_ms=(time.time() - start_time) * 1000,
            verification_queries=[],
            rollback_commands=[],
            effectiveness_score=0.95,
            prevention_measures=prevention_measures
        )
    
    async def _immediate_fix_resolution(self, error: DatabaseError) -> EnhancedResolution:
        """Immediate fix for critical errors"""
        start_time = time.time()
        
        actions = ["Emergency response initiated"]
        sql_commands = []
        
        if error.error_type == "CONNECTION_ERROR":
            sql_commands = [
                "SELECT 1 AS emergency_connection_test;",
                "SHOW STATUS LIKE 'Threads_connected';",
                "SHOW PROCESSLIST;"
            ]
            actions.append("Testing emergency database connectivity")
        
        return EnhancedResolution(
            resolution_id=f"immediate_{int(time.time())}",
            error_signature=self.pattern_analyzer._generate_signature(error),
            strategy=ResolutionStrategy.IMMEDIATE_FIX,
            success=True,
            actions_taken=actions,
            sql_commands=sql_commands,
            execution_time_ms=(time.time() - start_time) * 1000,
            verification_queries=["SELECT 1;"],
            rollback_commands=[],
            effectiveness_score=0.9,
            prevention_measures=[]
        )
    
    async def _guided_resolution(self, error: DatabaseError) -> EnhancedResolution:
        """Guided resolution with human oversight"""
        start_time = time.time()
        
        actions = ["Providing guided resolution steps"]
        sql_commands = []
        
        if error.error_type == "SYNTAX_ERROR":
            sql_commands = [
                f"-- Original query: {error.query}",
                "-- Syntax validation:",
                "SELECT 1;",
                f"EXPLAIN FORMAT=JSON SELECT 1;  -- Test query structure"
            ]
        elif error.error_type == "ACCESS_DENIED":
            sql_commands = [
                "SHOW GRANTS FOR CURRENT_USER();",
                "SELECT USER(), CURRENT_USER();",
                "-- Review and grant necessary permissions"
            ]
        
        return EnhancedResolution(
            resolution_id=f"guided_{int(time.time())}",
            error_signature=self.pattern_analyzer._generate_signature(error),
            strategy=ResolutionStrategy.GUIDED_RESOLUTION,
            success=True,
            actions_taken=actions,
            sql_commands=sql_commands,
            execution_time_ms=(time.time() - start_time) * 1000,
            verification_queries=[],
            rollback_commands=[],
            effectiveness_score=0.7,
            prevention_measures=[],
            requires_human_review=True
        )
    
    async def _check_alerts(self):
        """Check if alert conditions are met"""
        trends = self.pattern_analyzer.get_error_trends()
        
        if trends['error_rate_per_hour'] > self.alert_threshold:
            logger.warning(f"🚨 High error rate detected: {trends['error_rate_per_hour']:.1f} errors/hour")
        
        # Check resolution success rate
        recent_resolutions = list(self.resolution_history)[-20:]
        if recent_resolutions:
            success_rate = sum(1 for r in recent_resolutions if r.success) / len(recent_resolutions)
            if success_rate < 0.7:
                logger.warning(f"🚨 Low resolution success rate: {success_rate:.1%}")
    
    def get_enhanced_health_report(self) -> Dict[str, Any]:
        """Get comprehensive system health report"""
        trends = self.pattern_analyzer.get_error_trends()
        
        # Calculate average resolution time
        recent_resolutions = list(self.resolution_history)[-50:]
        avg_resolution_time = 0
        if recent_resolutions:
            avg_resolution_time = sum(r.execution_time_ms for r in recent_resolutions) / len(recent_resolutions)
        
        # Success rates by error type
        success_by_type = {}
        for error_type, results in self.success_rates.items():
            if results:
                success_by_type[error_type] = sum(results) / len(results)
        
        return {
            'error_trends': trends,
            'resolution_performance': {
                'total_resolutions': len(self.resolution_history),
                'average_resolution_time_ms': avg_resolution_time,
                'success_rates_by_type': success_by_type,
                'recent_success_rate': sum(1 for r in recent_resolutions if r.success) / len(recent_resolutions) if recent_resolutions else 0
            },
            'system_status': {
                'auto_healing_enabled': self.auto_healing_enabled,
                'alert_threshold': self.alert_threshold,
                'pattern_analysis_active': True
            },
            'recommendations': self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate system improvement recommendations"""
        recommendations = []
        
        trends = self.pattern_analyzer.get_error_trends()
        
        if trends['error_rate_per_hour'] > 2:
            recommendations.append("Consider implementing more aggressive error prevention")
        
        if trends['errors_last_24h'] > 10:
            recommendations.append("Review system configuration for recurring issues")
        
        # Check resolution success rates
        for error_type, results in self.success_rates.items():
            if results and len(results) > 5:
                success_rate = sum(results) / len(results)
                if success_rate < 0.8:
                    recommendations.append(f"Improve resolution strategies for {error_type} errors")
        
        if not recommendations:
            recommendations.append("System is performing well - continue monitoring")
        
        return recommendations
    
    async def learn_from_feedback(self, resolution_id: str, effectiveness_score: float):
        """Learn from user feedback"""
        for resolution in self.resolution_history:
            if resolution.resolution_id == resolution_id:
                resolution.effectiveness_score = effectiveness_score
                logger.info(f"Updated effectiveness score for {resolution_id}: {effectiveness_score}")
                break 