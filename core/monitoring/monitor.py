"""
Database monitoring system for DBA-GPT
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from core.config import Config
from core.database.connector import DatabaseConnector
from core.analysis.analyzer import PerformanceAnalyzer
from core.remediation.remediator import AutoRemediator
from core.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class MonitoringAlert:
    """Monitoring alert structure"""
    timestamp: datetime
    database: str
    alert_type: str
    severity: str
    message: str
    metrics: Dict[str, Any]
    resolved: bool = False


class DatabaseMonitor:
    """Main database monitoring system"""
    
    def __init__(self, config: Config):
        """Initialize database monitor"""
        self.config = config
        self.db_connector = DatabaseConnector(config)
        self.analyzer = PerformanceAnalyzer(config)
        self.remediator = AutoRemediator(config)
        self.running = False
        self.alerts = []
        self.metrics_history = {}
        
    async def start(self):
        """Start the monitoring system"""
        self.running = True
        logger.info("Starting DBA-GPT monitoring system...")
        
        try:
            while self.running:
                await self._monitoring_cycle()
                await asyncio.sleep(self.config.monitoring.interval)
        except Exception as e:
            logger.error(f"Monitoring error: {e}")
            self.running = False
            
    async def stop(self):
        """Stop the monitoring system"""
        self.running = False
        logger.info("Stopping DBA-GPT monitoring system...")
        
    async def _monitoring_cycle(self):
        """Execute one monitoring cycle"""
        for db_name, db_config in self.config.databases.items():
            try:
                await self._monitor_database(db_name, db_config)
            except Exception as e:
                logger.error(f"Error monitoring {db_name}: {e}")
                
    async def _monitor_database(self, db_name: str, db_config):
        """Monitor a specific database"""
        logger.debug(f"Monitoring database: {db_name}")
        
        # Get current metrics
        metrics = await self._collect_metrics(db_name, db_config)
        
        # Store metrics in history
        if db_name not in self.metrics_history:
            self.metrics_history[db_name] = []
        self.metrics_history[db_name].append({
            "timestamp": datetime.now(),
            "metrics": metrics
        })
        
        # Clean old metrics
        await self._cleanup_old_metrics(db_name)
        
        # Check for alerts
        alerts = await self._check_alerts(db_name, metrics)
        
        # Handle alerts
        for alert in alerts:
            await self._handle_alert(alert)
            
        # Auto-remediation if enabled
        if self.config.monitoring.auto_remediation:
            await self._auto_remediate(db_name, metrics)
            
    async def _collect_metrics(self, db_name: str, db_config) -> Dict[str, Any]:
        """Collect database metrics"""
        metrics = {
            "timestamp": datetime.now(),
            "database": db_name,
            "connection_status": "unknown",
            "performance": {},
            "system": {},
            "errors": []
        }
        
        try:
            # Test connection
            connector = await self.db_connector.get_connection(db_config)
            metrics["connection_status"] = "connected"
            
            # Get performance metrics
            metrics["performance"] = await self.analyzer.get_current_metrics(db_config)
            
            # Get system health
            metrics["system"] = await self.analyzer.get_system_health(db_config)
            
        except Exception as e:
            metrics["connection_status"] = "error"
            metrics["errors"].append(str(e))
            logger.error(f"Error collecting metrics for {db_name}: {e}")
            
        return metrics
        
    async def _check_alerts(self, db_name: str, metrics: Dict[str, Any]) -> List[MonitoringAlert]:
        """Check for monitoring alerts"""
        alerts = []
        thresholds = self.config.monitoring.alert_thresholds or {}
        
        # Connection alerts
        if metrics["connection_status"] != "connected":
            alerts.append(MonitoringAlert(
                timestamp=datetime.now(),
                database=db_name,
                alert_type="connection_error",
                severity="critical",
                message=f"Database {db_name} connection failed",
                metrics=metrics
            ))
            
        # Performance alerts
        performance = metrics.get("performance", {})
        
        # CPU usage alert
        cpu_usage = performance.get("cpu_usage", 0)
        if cpu_usage > thresholds.get("cpu_usage", 80):
            alerts.append(MonitoringAlert(
                timestamp=datetime.now(),
                database=db_name,
                alert_type="high_cpu",
                severity="high" if cpu_usage > 90 else "medium",
                message=f"High CPU usage: {cpu_usage}%",
                metrics=metrics
            ))
            
        # Memory usage alert
        memory_usage = performance.get("memory_usage", 0)
        if memory_usage > thresholds.get("memory_usage", 85):
            alerts.append(MonitoringAlert(
                timestamp=datetime.now(),
                database=db_name,
                alert_type="high_memory",
                severity="high" if memory_usage > 95 else "medium",
                message=f"High memory usage: {memory_usage}%",
                metrics=metrics
            ))
            
        # Disk usage alert
        disk_usage = performance.get("disk_usage", 0)
        if disk_usage > thresholds.get("disk_usage", 90):
            alerts.append(MonitoringAlert(
                timestamp=datetime.now(),
                database=db_name,
                alert_type="high_disk",
                severity="critical" if disk_usage > 95 else "high",
                message=f"High disk usage: {disk_usage}%",
                metrics=metrics
            ))
            
        # Slow query alert
        slow_queries = performance.get("slow_queries", 0)
        if slow_queries > 0:
            alerts.append(MonitoringAlert(
                timestamp=datetime.now(),
                database=db_name,
                alert_type="slow_queries",
                severity="medium",
                message=f"Detected {slow_queries} slow queries",
                metrics=metrics
            ))
            
        # Connection pool alert
        connection_pool = performance.get("connection_pool", {})
        pool_usage = connection_pool.get("usage_percent", 0)
        if pool_usage > 80:
            alerts.append(MonitoringAlert(
                timestamp=datetime.now(),
                database=db_name,
                alert_type="connection_pool",
                severity="medium",
                message=f"High connection pool usage: {pool_usage}%",
                metrics=metrics
            ))
            
        return alerts
        
    async def _handle_alert(self, alert: MonitoringAlert):
        """Handle a monitoring alert"""
        logger.warning(f"Alert: {alert.alert_type} - {alert.message}")
        
        # Store alert
        self.alerts.append(alert)
        
        # Log alert details
        alert_data = {
            "timestamp": alert.timestamp.isoformat(),
            "database": alert.database,
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "message": alert.message
        }
        
        if alert.severity in ["critical", "high"]:
            logger.critical(f"Critical alert: {alert_data}")
        else:
            logger.warning(f"Alert: {alert_data}")
            
        # Send notification (placeholder for future implementation)
        await self._send_notification(alert)
        
    async def _send_notification(self, alert: MonitoringAlert):
        """Send notification for alert (placeholder)"""
        # TODO: Implement notification system (email, Slack, etc.)
        pass
        
    async def _auto_remediate(self, db_name: str, metrics: Dict[str, Any]):
        """Attempt automatic remediation"""
        try:
            await self.remediator.remediate_issues(db_name, metrics)
        except Exception as e:
            logger.error(f"Auto-remediation failed for {db_name}: {e}")
            
    async def _cleanup_old_metrics(self, db_name: str):
        """Clean up old metrics data"""
        retention_days = self.config.monitoring.metrics_retention_days
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        if db_name in self.metrics_history:
            self.metrics_history[db_name] = [
                entry for entry in self.metrics_history[db_name]
                if entry["timestamp"] > cutoff_date
            ]
            
    async def get_current_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        status = {
            "running": self.running,
            "databases": {},
            "alerts": [],
            "metrics_summary": {}
        }
        
        # Get status for each database
        for db_name, db_config in self.config.databases.items():
            try:
                metrics = await self._collect_metrics(db_name, db_config)
                status["databases"][db_name] = {
                    "status": metrics["connection_status"],
                    "last_check": datetime.now().isoformat(),
                    "performance": metrics.get("performance", {}),
                    "system": metrics.get("system", {})
                }
            except Exception as e:
                status["databases"][db_name] = {
                    "status": "error",
                    "error": str(e),
                    "last_check": datetime.now().isoformat()
                }
                
        # Get recent alerts
        recent_alerts = [
            alert for alert in self.alerts
            if alert.timestamp > datetime.now() - timedelta(hours=24)
        ]
        status["alerts"] = [
            {
                "timestamp": alert.timestamp.isoformat(),
                "database": alert.database,
                "alert_type": alert.alert_type,
                "severity": alert.severity,
                "message": alert.message,
                "resolved": alert.resolved
            }
            for alert in recent_alerts
        ]
        
        # Get metrics summary
        for db_name in self.metrics_history:
            if self.metrics_history[db_name]:
                latest = self.metrics_history[db_name][-1]
                status["metrics_summary"][db_name] = {
                    "last_update": latest["timestamp"].isoformat(),
                    "metrics_count": len(self.metrics_history[db_name])
                }
                
        return status
        
    async def get_metrics_history(self, db_name: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get metrics history for a database"""
        if db_name not in self.metrics_history:
            return []
            
        cutoff_time = datetime.now() - timedelta(hours=hours)
        history = [
            entry for entry in self.metrics_history[db_name]
            if entry["timestamp"] > cutoff_time
        ]
        
        return [
            {
                "timestamp": entry["timestamp"].isoformat(),
                "metrics": entry["metrics"]
            }
            for entry in history
        ]
        
    async def resolve_alert(self, alert_index: int):
        """Mark an alert as resolved"""
        if 0 <= alert_index < len(self.alerts):
            self.alerts[alert_index].resolved = True
            logger.info(f"Alert {alert_index} marked as resolved")
            
    async def get_performance_report(self, db_name: str) -> Dict[str, Any]:
        """Generate performance report for a database"""
        try:
            db_config = self.config.get_database_config(db_name)
            if not db_config:
                return {"error": f"Database {db_name} not found in configuration"}
                
            return await self.analyzer.generate_performance_report(db_config)
            
        except Exception as e:
            logger.error(f"Error generating performance report for {db_name}: {e}")
            return {"error": str(e)} 