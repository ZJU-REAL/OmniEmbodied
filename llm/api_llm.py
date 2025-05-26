import os
import logging
import json
from typing import Dict, List, Optional, Any
import openai

from .base_llm import BaseLLM

logger = logging.getLogger(__name__)

class ApiLLM(BaseLLM):
    """
    通过API调用的LLM实现，支持OpenAI官方API和自定义端点
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化API LLM
        
        Args:
            config: 配置字典，包含API密钥等
        """
        super().__init__(config)
        self.provider = config.get('provider', 'openai').lower()
        provider_config = config.get(self.provider, {})
        
        # 设置模型名称
        self.model = provider_config.get('model', self.model)
        self.temperature = provider_config.get('temperature', self.temperature)
        self.max_tokens = provider_config.get('max_tokens', self.max_tokens)
        
        # 设置API密钥
        if self.provider == 'openai':
            self.api_key = provider_config.get('api_key') or os.environ.get('OPENAI_API_KEY', '')
            self.endpoint = "https://api.openai.com/v1"
        else:  # 自定义端点
            self.api_key = provider_config.get('api_key') or os.environ.get('CUSTOM_LLM_API_KEY', '')
            self.endpoint = provider_config.get('endpoint', '')
            
        if not self.api_key:
            logger.warning(f"{self.provider.capitalize()} API密钥未设置")
            
        # 配置OpenAI客户端
        if self.api_key:
            openai.api_key = self.api_key
            
        if self.endpoint and self.provider != 'openai':
            openai.base_url = self.endpoint
            
        # 设置组织ID（如果有）
        if provider_config.get('organization'):
            openai.organization = provider_config.get('organization')

        # 存储其他参数
        self.top_p = provider_config.get('top_p', 1.0)
        self.frequency_penalty = provider_config.get('frequency_penalty', 0.0)
        self.presence_penalty = provider_config.get('presence_penalty', 0.0)
        
        # 是否发送历史消息
        parameters = config.get('parameters', {})
        self.send_history = parameters.get('send_history', False)
        if logger.level <= logging.DEBUG:
            logger.debug("是否发送历史消息: %s", self.send_history)
        
    def generate(self, 
                 prompt: str, 
                 system_message: Optional[str] = None,
                 **kwargs) -> str:
        """
        生成文本响应
        
        Args:
            prompt: 用户输入提示
            system_message: 系统消息，可选
            **kwargs: 额外参数
            
        Returns:
            str: 生成的文本响应
        """
        # 构建消息列表
        messages = []
        
        if system_message:
            messages.append({"role": "system", "content": system_message})
            
        messages.append({"role": "user", "content": prompt})
        
        if logger.level <= logging.DEBUG:
            logger.debug("=== generate方法参数 ===")
            logger.debug(f"prompt: {prompt[:100]}...")
            if system_message:
                logger.debug(f"system_message: {system_message[:100]}...")
            logger.debug(f"其他参数: {kwargs}")
        
        return self.generate_chat(messages, **kwargs)
    
    def generate_chat(self, 
                      messages: List[Dict[str, str]],
                      **kwargs) -> str:
        """
        生成多轮对话响应
        
        Args:
            messages: 消息列表，每个消息是包含'role'和'content'的字典
            **kwargs: 额外参数
            
        Returns:
            str: 生成的文本响应
        """
        if not self.api_key:
            raise ValueError(f"{self.provider.capitalize()} API密钥未设置")
        
        # 处理system_message参数
        if "system_message" in kwargs and kwargs["system_message"]:
            system_msg = {"role": "system", "content": kwargs["system_message"]}
            # 检查是否已有system消息
            has_system = any(msg.get("role") == "system" for msg in messages)
            if not has_system:
                messages = [system_msg] + messages
        
        # 根据配置决定是否发送历史消息
        send_history = kwargs.get("send_history", self.send_history)
        if not send_history and len(messages) > 1:
            # 如果不发送历史，只保留system消息（如果有）和最后一条用户消息
            system_msg = None
            last_user_msg = None
            
            # 查找system消息和最后一条用户消息
            for msg in messages:
                if msg.get("role") == "system":
                    system_msg = msg
                elif msg.get("role") == "user":
                    last_user_msg = msg
            
            # 重建消息列表
            filtered_messages = []
            if system_msg:
                filtered_messages.append(system_msg)
            if last_user_msg:
                filtered_messages.append(last_user_msg)
            
            messages = filtered_messages
            
            if logger.level <= logging.DEBUG:
                logger.debug("已禁用历史消息发送，只发送system消息和最后一条用户消息")
        
        # 在DEBUG级别下记录完整请求详情
        if logger.level <= logging.DEBUG:
            logger.debug("=== LLM API 请求详情 ===")
            logger.debug(f"模型: {kwargs.get('model', self.model)}")
            logger.debug(f"温度: {kwargs.get('temperature', self.temperature)}")
            logger.debug(f"最大token: {kwargs.get('max_tokens', self.max_tokens)}")
            logger.debug(f"发送历史: {send_history}")
            
            # 记录完整的消息内容
            logger.debug("消息内容:")
            for i, msg in enumerate(messages):
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                logger.debug(f"[{i}] {role}: {content[:150]}..." if len(content) > 150 else f"[{i}] {role}: {content}")
        
        try:
            # 创建参数字典，只包含OpenAI API支持的参数
            params = {
                "model": kwargs.get("model", self.model),
                "messages": messages,
                "temperature": kwargs.get("temperature", self.temperature),
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                "top_p": kwargs.get("top_p", self.top_p),
                "frequency_penalty": kwargs.get("frequency_penalty", self.frequency_penalty),
                "presence_penalty": kwargs.get("presence_penalty", self.presence_penalty),
            }
            
            # 其他可选参数
            optional_params = ["n", "stream", "stop", "logit_bias", "user"]
            for param in optional_params:
                if param in kwargs and kwargs[param] is not None:
                    params[param] = kwargs[param]
            
            # 调用API
            if logger.level <= logging.DEBUG:
                logger.debug(f"发送API请求，参数: {json.dumps({k: v for k, v in params.items() if k != 'messages'}, ensure_ascii=False)}")
                
            response = openai.chat.completions.create(**params)
            
            # 记录API响应细节
            if logger.level <= logging.DEBUG:
                try:
                    response_dict = {}
                    if hasattr(response, 'model'):
                        response_dict['model'] = response.model
                    if hasattr(response, 'usage'):
                        response_dict['usage'] = {
                            'prompt_tokens': response.usage.prompt_tokens,
                            'completion_tokens': response.usage.completion_tokens,
                            'total_tokens': response.usage.total_tokens
                        }
                    if hasattr(response, 'choices') and len(response.choices) > 0:
                        response_dict['content'] = response.choices[0].message.content
                        if hasattr(response.choices[0], 'finish_reason'):
                            response_dict['finish_reason'] = response.choices[0].finish_reason
                    
                    logger.debug(f"API响应详情: {json.dumps(response_dict, ensure_ascii=False, indent=2)}")
                except Exception as e:
                    logger.debug(f"记录API响应详情时出错: {e}")
            
            # 返回生成的内容
            if hasattr(response, 'choices') and len(response.choices) > 0:
                result = response.choices[0].message.content
                
                # 记录响应内容
                if logger.level <= logging.DEBUG:
                    logger.debug(f"=== LLM响应内容 ===\n{result}\n===================")
                
                return result
            else:
                logger.warning(f"API响应中未找到有效内容")
                return ""
                
        except Exception as e:
            logger.exception(f"调用API时发生错误: {str(e)}")
            return f"错误: {str(e)}" 