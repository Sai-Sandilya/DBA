"""
Configuration management for DBA-GPT
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    """Database connection configuration"""
    host: str
    port: int
    database: str
    username: str
    password: str
    db_type: str  # postgresql, mysql, mongodb, redis
    ssl_mode: str = "prefer"
    connection_pool_size: int = 10
    timeout: int = 30
    db_name: str = ""  # Add db_name attribute


@dataclass
class AIConfig:
    """AI model configuration"""
    model: str = "llama2:13b"
    temperature: float = 0.7
    max_tokens: int = 2048
    context_window: int = 4096
    ollama_host: str = "http://localhost:11434"
    system_prompt: str = "You are DBA-GPT, an expert database administrator AI assistant."


@dataclass
class MonitoringConfig:
    """Monitoring configuration"""
    enabled: bool = True
    interval: int = 60  # seconds
    metrics_retention_days: int = 30
    alert_thresholds: Dict[str, float] = None
    auto_remediation: bool = True


class Config:
    """Main configuration class"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration"""
        self.config_path = config_path or self._get_default_config_path()
        self._load_config()
        
    def _get_default_config_path(self) -> str:
        """Get default configuration file path"""
        config_dir = Path(__file__).parent.parent / "config"
        config_dir.mkdir(exist_ok=True)
        return str(config_dir / "config.yaml")
        
    def _load_config(self):
        """Load configuration from file"""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                config_data = yaml.safe_load(f)
        else:
            config_data = self._get_default_config()
            self._save_config(config_data)
            
        self._parse_config(config_data)
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "ai": {
                "model": "llama2:13b",
                "temperature": 0.7,
                "max_tokens": 2048,
                "context_window": 4096,
                "ollama_host": "http://localhost:11434",
                "system_prompt": "You are DBA-GPT, an expert database administrator AI assistant."
            },
            "monitoring": {
                "enabled": True,
                "interval": 60,
                "metrics_retention_days": 30,
                "auto_remediation": True,
                "alert_thresholds": {
                    "cpu_usage": 80.0,
                    "memory_usage": 85.0,
                    "disk_usage": 90.0,
                    "slow_query_threshold": 5.0
                }
            },
            "databases": {
                "postgresql": {
                    "host": "localhost",
                    "port": 5432,
                    "database": "postgres",
                    "username": "postgres",
                    "password": "",
                    "db_type": "postgresql"
                },
                "mysql": {
                    "host": "localhost",
                    "port": 3306,
                    "database": "mysql",
                    "username": "root",
                    "password": "",
                    "db_type": "mysql"
                }
            },
            "logging": {
                "level": "INFO",
                "file": "logs/dbagpt.log",
                "max_size": "10MB",
                "backup_count": 5
            },
            "web": {
                "host": "0.0.0.0",
                "port": 8000,
                "web_port": 8501
            }
        }
        
    def _save_config(self, config_data: Dict[str, Any]):
        """Save configuration to file"""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False, indent=2)
            
    def _parse_config(self, config_data: Dict[str, Any]):
        """Parse configuration data"""
        # AI Configuration
        ai_data = config_data.get("ai", {})
        self.ai = AIConfig(
            model=ai_data.get("model", "llama2:13b"),
            temperature=ai_data.get("temperature", 0.7),
            max_tokens=ai_data.get("max_tokens", 2048),
            context_window=ai_data.get("context_window", 4096),
            ollama_host=ai_data.get("ollama_host", "http://localhost:11434"),
            system_prompt=ai_data.get("system_prompt", "You are DBA-GPT, an expert database administrator AI assistant.")
        )
        
        # Monitoring Configuration
        monitoring_data = config_data.get("monitoring", {})
        self.monitoring = MonitoringConfig(
            enabled=monitoring_data.get("enabled", True),
            interval=monitoring_data.get("interval", 60),
            metrics_retention_days=monitoring_data.get("metrics_retention_days", 30),
            auto_remediation=monitoring_data.get("auto_remediation", True),
            alert_thresholds=monitoring_data.get("alert_thresholds", {})
        )
        
        # Database Configurations
        self.databases = {}
        databases_data = config_data.get("databases", {})
        if databases_data is not None:
            for db_name, db_data in databases_data.items():
                self.databases[db_name] = DatabaseConfig(
                    host=db_data.get("host", "localhost"),
                    port=db_data.get("port", 5432),
                    database=db_data.get("database", ""),
                    username=db_data.get("username", ""),
                    password=db_data.get("password", ""),
                    db_type=db_data.get("db_type", "postgresql"),
                    ssl_mode=db_data.get("ssl_mode", "prefer"),
                    connection_pool_size=db_data.get("connection_pool_size", 10),
                    timeout=db_data.get("timeout", 30),
                    db_name=db_name  # Set the db_name from the config key
                )
        
        # Other configurations
        self.logging = config_data.get("logging", {})
        self.web = config_data.get("web", {})
        
    def get_database_config(self, db_name: str) -> Optional[DatabaseConfig]:
        """Get database configuration by name"""
        return self.databases.get(db_name)
        
    def add_database(self, name: str, config: DatabaseConfig):
        """Add a new database configuration"""
        self.databases[name] = config
        self._save_current_config()
        
    def _save_current_config(self):
        """Save current configuration to file"""
        config_data = {
            "ai": {
                "model": self.ai.model,
                "temperature": self.ai.temperature,
                "max_tokens": self.ai.max_tokens,
                "context_window": self.ai.context_window,
                "ollama_host": self.ai.ollama_host,
                "system_prompt": self.ai.system_prompt
            },
            "monitoring": {
                "enabled": self.monitoring.enabled,
                "interval": self.monitoring.interval,
                "metrics_retention_days": self.monitoring.metrics_retention_days,
                "auto_remediation": self.monitoring.auto_remediation,
                "alert_thresholds": self.monitoring.alert_thresholds
            },
            "databases": {
                name: {
                    "host": config.host,
                    "port": config.port,
                    "database": config.database,
                    "username": config.username,
                    "password": config.password,
                    "db_type": config.db_type,
                    "ssl_mode": config.ssl_mode,
                    "connection_pool_size": config.connection_pool_size,
                    "timeout": config.timeout
                }
                for name, config in self.databases.items()
            },
            "logging": self.logging,
            "web": self.web
        }
        self._save_config(config_data) 