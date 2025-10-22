"""
Configuration management for the Training Job Orchestrator
"""

import os
import yaml
from typing import Any, Dict, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class Config:
    """Configuration manager"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or os.getenv('CONFIG_FILE', 'config.yaml')
        self.config: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self):
        """Load configuration from file"""
        if Path(self.config_file).exists():
            with open(self.config_file, 'r') as f:
                self.config = yaml.safe_load(f) or {}
            logger.info(f"Loaded configuration from {self.config_file}")
        else:
            logger.warning(f"Config file {self.config_file} not found, using defaults")
            self.config = self.get_default_config()
        
        # Override with environment variables
        self._apply_env_overrides()
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'orchestrator': {
                'max_workers': 5,
                'default_retry_count': 3,
                'retry_backoff_base': 60,
                'job_timeout': 86400
            },
            'kubernetes': {
                'namespace': 'training',
                'service_account': 'training-orchestrator'
            },
            'storage': {
                'checkpoint_dir': '/checkpoints',
                'pvc_name': 'training-checkpoints'
            },
            'database': {
                'host': os.getenv('POSTGRES_HOST', 'postgres'),
                'port': int(os.getenv('POSTGRES_PORT', 5432)),
                'name': os.getenv('POSTGRES_DB', 'training_jobs'),
                'user': os.getenv('POSTGRES_USER', 'orchestrator'),
                'password': os.getenv('POSTGRES_PASSWORD', '')
            },
            'redis': {
                'host': os.getenv('REDIS_HOST', 'redis'),
                'port': int(os.getenv('REDIS_PORT', 6379)),
                'db': 0
            },
            'notifications': {
                'slack': {
                    'enabled': bool(os.getenv('SLACK_WEBHOOK_URL')),
                    'webhook_url': os.getenv('SLACK_WEBHOOK_URL', '')
                },
                'email': {
                    'enabled': bool(os.getenv('SENDER_EMAIL')),
                    'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
                    'smtp_port': int(os.getenv('SMTP_PORT', 587)),
                    'sender_email': os.getenv('SENDER_EMAIL', ''),
                    'sender_password': os.getenv('SENDER_PASSWORD', ''),
                    'recipient_emails': os.getenv('RECIPIENT_EMAILS', '').split(',')
                }
            },
            'logging': {
                'level': os.getenv('LOG_LEVEL', 'INFO'),
                'format': 'json',
                'output': 'stdout'
            },
            'api': {
                'host': '0.0.0.0',
                'port': int(os.getenv('API_PORT', 8080))
            }
        }
    
    def _apply_env_overrides(self):
        """Apply environment variable overrides"""
        # Kubernetes
        if os.getenv('K8S_NAMESPACE'):
            self.config.setdefault('kubernetes', {})['namespace'] = os.getenv('K8S_NAMESPACE')
        
        # Workers
        if os.getenv('MAX_WORKERS'):
            self.config.setdefault('orchestrator', {})['max_workers'] = int(os.getenv('MAX_WORKERS'))
        
        # Database
        if os.getenv('POSTGRES_HOST'):
            self.config.setdefault('database', {})['host'] = os.getenv('POSTGRES_HOST')
        if os.getenv('POSTGRES_PASSWORD'):
            self.config.setdefault('database', {})['password'] = os.getenv('POSTGRES_PASSWORD')
        
        # Redis
        if os.getenv('REDIS_HOST'):
            self.config.setdefault('redis', {})['host'] = os.getenv('REDIS_HOST')
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot notation key"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value by dot notation key"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            config = config.setdefault(k, {})
        
        config[keys[-1]] = value
    
    def save(self, filepath: Optional[str] = None):
        """Save configuration to file"""
        filepath = filepath or self.config_file
        
        with open(filepath, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
        
        logger.info(f"Configuration saved to {filepath}")


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get global configuration instance"""
    global _config
    if _config is None:
        _config = Config()
    return _config


def reload_config():
    """Reload configuration"""
    global _config
    _config = Config()
    return _config