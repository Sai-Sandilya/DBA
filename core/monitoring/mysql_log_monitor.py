"""
MySQL Error Log Monitor for External Error Detection
Monitors MySQL error logs and general query logs for external errors
"""

import asyncio
import os
import re
from datetime import datetime
from typing import Optional, Callable
from pathlib import Path
import logging

from core.database.connector import DatabaseError
from core.utils.logger import setup_logger

logger = setup_logger(__name__)


class MySQLLogMonitor:
    """Monitor MySQL logs for external errors"""
    
    def __init__(self, error_callback: Optional[Callable] = None):
        self.error_callback = error_callback
        self.is_monitoring = False
        self.log_paths = self._detect_mysql_log_paths()
        
        # Error patterns to detect
        self.error_patterns = {
            r'Table \'[^\']+\' doesn\'t exist': 'TABLE_NOT_FOUND',
            r'Unknown column \'[^\']+\'': 'COLUMN_NOT_FOUND', 
            r'You have an error in your SQL syntax': 'SYNTAX_ERROR',
            r'Access denied for user': 'ACCESS_DENIED',
            r'Too many connections': 'TOO_MANY_CONNECTIONS',
            r'Deadlock found when trying to get lock': 'DEADLOCK',
            r'Lock wait timeout exceeded': 'LOCK_TIMEOUT'
        }
        
    def _detect_mysql_log_paths(self) -> list:
        """Detect common MySQL log file locations"""
        possible_paths = [
            # Windows paths
            "C:/ProgramData/MySQL/MySQL Server 8.0/Data/error.log",
            "C:/Program Files/MySQL/MySQL Server 8.0/data/error.log",
            "C:/xampp/mysql/data/error.log",
            
            # Linux paths
            "/var/log/mysql/error.log",
            "/var/log/mysqld.log",
            "/usr/local/mysql/data/error.log",
            
            # General query log
            "C:/ProgramData/MySQL/MySQL Server 8.0/Data/general.log",
            "/var/log/mysql/general.log"
        ]
        
        existing_paths = []
        for path in possible_paths:
            if Path(path).exists():
                existing_paths.append(path)
                logger.info(f"Found MySQL log: {path}")
                
        return existing_paths
    
    async def start_monitoring(self):
        """Start monitoring MySQL logs for external errors"""
        if not self.log_paths:
            logger.warning("No MySQL log files found. External error monitoring disabled.")
            return
            
        self.is_monitoring = True
        logger.info(f"Starting MySQL log monitoring on {len(self.log_paths)} files")
        
        # Start monitoring tasks for each log file
        tasks = []
        for log_path in self.log_paths:
            task = asyncio.create_task(self._monitor_log_file(log_path))
            tasks.append(task)
            
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Error in log monitoring: {e}")
        finally:
            self.is_monitoring = False
    
    async def _monitor_log_file(self, log_path: str):
        """Monitor a specific log file for errors"""
        logger.info(f"Monitoring MySQL log: {log_path}")
        
        try:
            # Get current file size to start monitoring from end
            current_size = os.path.getsize(log_path)
            
            while self.is_monitoring:
                try:
                    new_size = os.path.getsize(log_path)
                    
                    if new_size > current_size:
                        # Read new content
                        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                            f.seek(current_size)
                            new_content = f.read()
                            
                        # Process new log entries
                        await self._process_log_content(new_content, log_path)
                        current_size = new_size
                        
                except Exception as e:
                    logger.error(f"Error reading log file {log_path}: {e}")
                
                # Wait before next check
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error monitoring {log_path}: {e}")
    
    async def _process_log_content(self, content: str, log_path: str):
        """Process new log content for error patterns"""
        lines = content.strip().split('\n')
        
        for line in lines:
            if not line.strip():
                continue
                
            # Check for error patterns
            for pattern, error_type in self.error_patterns.items():
                if re.search(pattern, line, re.IGNORECASE):
                    await self._handle_detected_error(line, error_type, log_path)
                    break
    
    async def _handle_detected_error(self, log_line: str, error_type: str, log_path: str):
        """Handle detected external MySQL error"""
        logger.info(f"🚨 EXTERNAL ERROR DETECTED: {error_type}")
        logger.info(f"Source: {log_path}")
        logger.info(f"Log line: {log_line}")
        
        # Extract error details
        error_code = self._extract_error_code(log_line)
        query = self._extract_query(log_line)
        table = self._extract_table_name(log_line)
        
        # Create DatabaseError object
        db_error = DatabaseError(
            error_type=error_type,
            error_code=error_code,
            message=log_line.strip(),
            query=query,
            table=table,
            context={
                "source": "external_mysql",
                "log_path": log_path,
                "detection_time": datetime.now().isoformat()
            }
        )
        
        # Send to auto-resolution system
        if self.error_callback:
            try:
                if asyncio.iscoroutinefunction(self.error_callback):
                    await self.error_callback(db_error)
                else:
                    self.error_callback(db_error)
            except Exception as e:
                logger.error(f"Error in callback: {e}")
    
    def _extract_error_code(self, log_line: str) -> str:
        """Extract MySQL error code from log line"""
        # Look for pattern like [ERROR] [MY-001146]
        match = re.search(r'\[MY-(\d+)\]', log_line)
        if match:
            return match.group(1)
        
        # Look for traditional error codes
        match = re.search(r'(\d{4})', log_line)
        if match:
            return match.group(1)
            
        return "UNKNOWN"
    
    def _extract_query(self, log_line: str) -> Optional[str]:
        """Extract SQL query from log line if available"""
        # Look for query patterns
        query_patterns = [
            r'Query\s+(.+?)(?:\s+for|$)',
            r'Execute\s+(.+?)(?:\s+for|$)',
            r'(SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER).+',
        ]
        
        for pattern in query_patterns:
            match = re.search(pattern, log_line, re.IGNORECASE)
            if match:
                return match.group(1).strip()
                
        return None
    
    def _extract_table_name(self, log_line: str) -> Optional[str]:
        """Extract table name from error message"""
        # Common table extraction patterns
        patterns = [
            r'Table \'[^.]+\.([^\']+)\'',  # Database.table format
            r'Table \'([^\']+)\'',         # Simple table format
            r'table \'([^\']+)\'',         # Lowercase
            r'from\s+([^\s]+)',            # FROM clause
        ]
        
        for pattern in patterns:
            match = re.search(pattern, log_line, re.IGNORECASE)
            if match:
                return match.group(1)
                
        return None
    
    def stop_monitoring(self):
        """Stop log monitoring"""
        self.is_monitoring = False
        logger.info("MySQL log monitoring stopped")


# Integration function for DBA Assistant
async def start_external_error_monitoring(dba_assistant):
    """Start external MySQL error monitoring"""
    monitor = MySQLLogMonitor(error_callback=dba_assistant.handle_auto_error_resolution)
    await monitor.start_monitoring()
    return monitor 