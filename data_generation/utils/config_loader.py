"""
Configuration loader utility for the data generation project.
Handles loading and validation of YAML configuration files.
"""

import os
import yaml
from typing import Any, Dict, Optional
from pathlib import Path


class ConfigLoader:
    """
    Configuration loader with validation and default value support.
    """
    
    def __init__(self, config_dir: str = "./config"):
        """
        Initialize the config loader.
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self._configs = {}
        
    def load_config(self, config_name: str, required_fields: Optional[list] = None) -> Dict[str, Any]:
        """
        Load a configuration file with caching.
        
        Args:
            config_name: Name of the config file (without .yaml extension)
            required_fields: List of required fields to validate
            
        Returns:
            Configuration dictionary
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If required fields are missing
        """
        if config_name in self._configs:
            return self._configs[config_name]
            
        config_path = self.config_dir / f"{config_name}.yaml"
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
            
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            
        # Validate required fields
        if required_fields:
            missing_fields = [field for field in required_fields if field not in config]
            if missing_fields:
                raise ValueError(f"Missing required fields in {config_name}: {missing_fields}")
                
        self._configs[config_name] = config
        return config
        
    def get_pipeline_config(self) -> Dict[str, Any]:
        """
        Load pipeline configuration with defaults.
        """
        config = self.load_config("pipeline")
        
        # Apply defaults
        defaults = {
            'thread_num': 4,
            'start_id': 0,
            'end_id': None,
            'continue_generation': True,
            'output_dir': './data',
            'log_dir': './logs',
            'max_retries': 3,
            'retry_delay': 2,
            'clue_dir': 'clue',
            'scene_dir': 'scene',
            'task_dir': 'task',
            'verify_dir': 'verify',
            'summary_file': 'summary.json'
        }
        
        for key, default_value in defaults.items():
            config.setdefault(key, default_value)
            
        return config
        
    def get_generator_config(self, generator_type: str) -> Dict[str, Any]:
        """
        Load generator-specific configuration.
        
        Args:
            generator_type: Type of generator ('clue', 'scene', 'task', 'verify', 'unified_task')
            
        Returns:
            Generator configuration dictionary
        """
        config_name = f"{generator_type}_gen_config"
        required_fields = ['api_key', 'model', 'system_prompt', 'user_prompt']
        
        config = self.load_config(config_name, required_fields)
        
        # Apply generator-specific defaults
        defaults = {
            'thread_num': 4,
            'temperature': 0.7,
            'max_tokens': 4096,
            'timeout': 600,
            'start_id': 0,
            'end_id': None
        }
        
        for key, default_value in defaults.items():
            config.setdefault(key, default_value)
            
        return config

    def get_config(self, config_name: str) -> Dict[str, Any]:
        """
        Get configuration by name with defaults applied.

        Args:
            config_name: Name of the configuration file (without .yaml extension)

        Returns:
            Configuration dictionary with defaults applied
        """
        if config_name == 'unified_task_gen_config':
            return self.get_generator_config('unified_task')
        else:
            return self.load_config(config_name)

    def reload_configs(self):
        """
        Clear the config cache and force reload on next access.
        """
        self._configs.clear()


# Global config loader instance
config_loader = ConfigLoader()


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Legacy function for backward compatibility.
    Load a YAML configuration file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Configuration dictionary
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) 