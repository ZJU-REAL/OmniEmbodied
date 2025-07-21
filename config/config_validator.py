import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class ConfigValidator:
    """配置验证器"""
    
    # 基础配置模式
    BASE_SCHEMA = {
        "type": "object",
        "properties": {
            "system": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "version": {"type": "string"}
                }
            },
            "data_dir": {"type": "string"},
            "execution": {
                "type": "object",
                "properties": {
                    "max_total_steps": {"type": "integer", "minimum": 1},
                    "max_steps_per_task": {"type": "integer", "minimum": 1},
                    "timeout_seconds": {"type": "integer", "minimum": 1}
                }
            }
        },
        "required": ["data_dir"]
    }
    
    # LLM配置模式
    LLM_SCHEMA = {
        "type": "object",
        "properties": {
            "mode": {"type": "string", "enum": ["api", "vllm"]},
            "api": {
                "type": "object",
                "properties": {
                    "provider": {"type": "string"}
                },
                "required": ["provider"]
            }
        },
        "required": ["mode"]
    }
    
    # 智能体配置模式
    AGENT_SCHEMA = {
        "type": "object",
        "properties": {
            "agent_config": {
                "type": "object",
                "properties": {
                    "agent_class": {"type": "string"},
                    "max_failures": {"type": "integer", "minimum": 1},
                    "max_history": {"type": "integer", "minimum": -1}
                },
                "required": ["agent_class"]
            }
        },
        "required": ["agent_config"]
    }
    
    @classmethod
    def validate_config(cls, config: Dict[str, Any], config_type: str = "base") -> List[str]:
        """
        验证配置
        
        Args:
            config: 配置字典
            config_type: 配置类型 ("base", "llm", "agent")
            
        Returns:
            List[str]: 验证错误列表，空列表表示验证通过
        """
        schema_map = {
            "base": cls.BASE_SCHEMA,
            "llm": cls.LLM_SCHEMA,
            "agent": cls.AGENT_SCHEMA
        }
        
        schema = schema_map.get(config_type, cls.BASE_SCHEMA)
        errors = []
        
        try:
            # 简单的验证逻辑，可以后续扩展为使用jsonschema
            if config_type == "base":
                if "data_dir" not in config:
                    errors.append("缺少必需的 'data_dir' 配置")
            elif config_type == "llm":
                if "mode" not in config:
                    errors.append("缺少必需的 'mode' 配置")
                elif config["mode"] not in ["api", "vllm"]:
                    errors.append("'mode' 必须是 'api' 或 'vllm'")
            elif config_type == "agent":
                if "agent_config" not in config:
                    errors.append("缺少必需的 'agent_config' 配置")
                elif "agent_class" not in config["agent_config"]:
                    errors.append("缺少必需的 'agent_config.agent_class' 配置")
                    
        except Exception as e:
            errors.append(f"配置验证异常: {str(e)}")
        
        return errors
    
    @classmethod
    def validate_config_file(cls, config_manager, config_name: str) -> bool:
        """
        验证配置文件
        
        Args:
            config_manager: 配置管理器实例
            config_name: 配置名称
            
        Returns:
            bool: 是否验证通过
        """
        try:
            config = config_manager.get_config(config_name)
            
            # 根据配置名称确定验证类型
            if 'llm' in config_name:
                config_type = "llm"
            elif 'agent' in config_name:
                config_type = "agent"
            else:
                config_type = "base"
            
            errors = cls.validate_config(config, config_type)
            
            if errors:
                for error in errors:
                    logger.error(f"配置 {config_name} 验证失败: {error}")
                return False
            
            logger.info(f"配置 {config_name} 验证通过")
            return True
            
        except Exception as e:
            logger.error(f"验证配置 {config_name} 时发生异常: {e}")
            return False
