from typing import Dict, Any

from .base_llm import BaseLLM
from .api_llm import ApiLLM
from .vllm_llm import VLLMLLM

def create_llm_from_config(config: Dict[str, Any]) -> BaseLLM:
    """
    根据配置创建LLM实例
    
    Args:
        config: 配置字典
        
    Returns:
        BaseLLM: LLM实例
    """
    mode = config.get('mode', 'api').lower()
    
    if mode == 'api':
        return ApiLLM(config.get('api', {}))
    elif mode == 'vllm':
        return VLLMLLM(config)
    else:
        raise ValueError(f"不支持的LLM模式: {mode}，可选值为: api, vllm") 