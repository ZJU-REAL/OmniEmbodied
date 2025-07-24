import os
import logging
import json
from typing import Dict, List, Optional, Any
import openai

from llm.base_llm import BaseLLM

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

        # 动态获取供应商配置 - 支持新旧两种结构
        providers_config = config.get('providers', {})
        if self.provider in providers_config:
            # 新结构：使用 providers 配置
            provider_config = providers_config[self.provider]
            logger.debug(f"使用新配置结构加载供应商: {self.provider}")
        else:
            # 旧结构：向后兼容
            provider_config = config.get(self.provider, {})
            logger.debug(f"使用旧配置结构加载供应商: {self.provider}")

        if not provider_config:
            logger.warning(f"未找到供应商配置: {self.provider}")
            provider_config = {}

        # 基础参数设置
        self.model = provider_config.get('model', self.model)
        self.temperature = provider_config.get('temperature', self.temperature)
        self.max_tokens = provider_config.get('max_tokens', self.max_tokens)

        # 动态API密钥处理
        api_key_config = provider_config.get('api_key', '')
        if isinstance(api_key_config, str) and api_key_config.startswith('${') and api_key_config.endswith('}'):
            # 从环境变量名中提取
            env_var_name = api_key_config[2:-1]  # 去掉 ${ 和 }
            self.api_key = os.environ.get(env_var_name, '')
            if not self.api_key:
                logger.warning(f"环境变量 {env_var_name} 未设置")
        else:
            # 直接使用配置中的值
            self.api_key = api_key_config.strip() if api_key_config else ''

        # 端点配置
        self.endpoint = provider_config.get('endpoint', '')

        # 扩展配置（支持约束生成）
        self.extends = provider_config.get('extends', {})
        if self.extends.get('guided_regex'):
            logger.info(f"配置约束生成参数: {self.extends.get('guided_regex')}")

        # 存储所有其他参数（用于传递给API调用）
        self.extra_params = {}
        basic_params = {'model', 'temperature', 'max_tokens', 'api_key', 'endpoint', 'extends'}
        for key, value in provider_config.items():
            if key not in basic_params:
                self.extra_params[key] = value
                logger.debug(f"存储额外参数: {key} = {value}")

        if not self.api_key:
            logger.warning(f"{self.provider.capitalize()} API密钥未设置")

        # 配置OpenAI客户端
        client_kwargs = {}
        if self.api_key:
            client_kwargs['api_key'] = self.api_key

        if self.endpoint:
            client_kwargs['base_url'] = self.endpoint

        # 设置组织ID（如果有）
        if 'organization' in self.extra_params:
            client_kwargs['organization'] = self.extra_params['organization']

        # 设置timeout（如果有）
        if 'timeout' in self.extra_params:
            client_kwargs['timeout'] = self.extra_params['timeout']
            logger.debug(f"设置API超时时间: {self.extra_params['timeout']}秒")

        # 创建OpenAI客户端实例
        self.client = openai.OpenAI(**client_kwargs)

        # 向后兼容：存储常用参数
        self.top_p = self.extra_params.get('top_p', 1.0)
        self.frequency_penalty = self.extra_params.get('frequency_penalty', 0.0)
        self.presence_penalty = self.extra_params.get('presence_penalty', 0.0)
        self.enable_thinking = self.extra_params.get('enable_thinking')

        # 是否发送历史消息
        parameters = config.get('parameters', {})
        self.send_history = parameters.get('send_history', False)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("是否发送历史消息: %s", self.send_history)
            if self.enable_thinking is not None:
                logger.debug("enable_thinking 配置: %s", self.enable_thinking)
            logger.debug(f"额外参数: {self.extra_params}")

        # 用于记录最后一次调用的统计信息
        self.last_token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        self.last_response_time_ms = 0.0
        
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
        
        if logger.isEnabledFor(logging.DEBUG):
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
            
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("已禁用历史消息发送，只发送system消息和最后一条用户消息")
        
        # 记录完整请求详情（在DEBUG级别或配置启用时）
        show_details = logger.isEnabledFor(logging.DEBUG)
        if show_details:
            logger.info("=== LLM API 请求详情 ===")
            logger.info(f"模型: {kwargs.get('model', self.model)}")
            logger.info(f"温度: {kwargs.get('temperature', self.temperature)}")
            logger.info(f"最大token: {kwargs.get('max_tokens', self.max_tokens)}")
            logger.info(f"发送历史: {send_history}")

            # 记录完整的消息内容
            logger.info("消息内容:")
            for i, msg in enumerate(messages):
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                logger.info(f"[{i}] {role}: {content[:300]}..." if len(content) > 300 else f"[{i}] {role}: {content}")
        
        try:
            # 记录开始时间
            import time
            start_time = time.time()

            # 创建基础参数字典
            params = {
                "model": kwargs.get("model", self.model),
                "messages": messages,
                "temperature": kwargs.get("temperature", self.temperature),
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            }

            # 添加配置中的额外参数
            for key, value in self.extra_params.items():
                if key not in params and key not in ['system_message', 'send_history']:
                    params[key] = value

            # 添加运行时传入的额外参数（优先级更高）
            excluded_params = {'system_message', 'send_history', 'model', 'messages', 'temperature', 'max_tokens'}
            for key, value in kwargs.items():
                if key not in excluded_params and value is not None:
                    params[key] = value

            # 处理 extra_body 参数的合并
            config_extra_body = self.extra_params.get('extra_body', {})
            runtime_extra_body = kwargs.get('extra_body', {})

            # 如果有extends配置，添加约束生成参数
            if self.extends.get('guided_regex'):
                extends_extra_body = {
                    'guided_regex': self.extends.get('guided_regex'),
                    'stop': self.extends.get('stop_tokens', [])
                }
                config_extra_body.update(extends_extra_body)
                if show_details:
                    logger.info(f"添加约束生成参数: {extends_extra_body}")

            if config_extra_body or runtime_extra_body:
                # 合并配置中的 extra_body 和运行时的 extra_body
                merged_extra_body = {}
                merged_extra_body.update(config_extra_body)
                merged_extra_body.update(runtime_extra_body)
                params['extra_body'] = merged_extra_body

            # 调用API
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"发送API请求，参数: {json.dumps({k: v for k, v in params.items() if k != 'messages'}, ensure_ascii=False)}")

            response = self.client.chat.completions.create(**params)

            # 记录响应时间
            end_time = time.time()
            self.last_response_time_ms = (end_time - start_time) * 1000
            
            # 记录API响应细节
            if logger.isEnabledFor(logging.DEBUG):
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
            
            # 记录token使用情况
            if hasattr(response, 'usage') and response.usage:
                self.last_token_usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            else:
                self.last_token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

            # 返回生成的内容
            if hasattr(response, 'choices') and len(response.choices) > 0:
                result = response.choices[0].message.content

                # 记录响应内容
                if show_details:
                    logger.info(f"=== LLM响应内容 ===\n{result}\n===================")
                    logger.info(f"Token使用: {self.last_token_usage}")
                    logger.info(f"响应时间: {self.last_response_time_ms:.2f}ms")

                return result
            else:
                logger.warning(f"API响应中未找到有效内容")
                return ""
                
        except Exception as e:
            logger.exception(f"调用API时发生错误: {str(e)}")
            return f"错误: {str(e)}" 