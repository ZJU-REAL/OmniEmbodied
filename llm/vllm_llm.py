import logging
from typing import Dict, List, Optional, Any
from llm.base_llm import BaseLLM

logger = logging.getLogger(__name__)

# [TODO] 待实现，使用transformers库，构造chat_template, 使用vllm进行推理   
class VLLMLLM(BaseLLM):
    """
    使用VLLM进行本地推理的LLM实现
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化VLLM LLM
        
        Args:
            config: 配置字典
        """
        super().__init__(config)
        
        try:
            from vllm import LLM, SamplingParams
        except ImportError:
            raise ImportError("使用VLLM模式需要安装vllm库。请运行 'pip install vllm'")
        
        self._SamplingParams = SamplingParams
        
        vllm_config = config.get('vllm', {})
        self.model_path = vllm_config.get('model_path', '')
        
        if not self.model_path:
            raise ValueError("VLLM模型路径未设置")
        
        self.temperature = vllm_config.get('temperature', self.temperature)
        self.max_tokens = vllm_config.get('max_tokens', self.max_tokens)
        
        # VLLM特有参数
        self.tensor_parallel_size = vllm_config.get('tensor_parallel_size', 1)
        self.gpu_memory_utilization = vllm_config.get('gpu_memory_utilization', 0.9)

        # 用于记录最后一次调用的统计信息
        self.last_token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        self.last_response_time_ms = 0.0

        # 初始化VLLM模型
        try:
            logger.info(f"正在加载VLLM模型: {self.model_path}")
            self.engine = LLM(
                model=self.model_path,
                tensor_parallel_size=self.tensor_parallel_size,
                gpu_memory_utilization=self.gpu_memory_utilization
            )
            logger.info("VLLM模型加载成功")
        except Exception as e:
            logger.exception(f"加载VLLM模型时发生错误: {str(e)}")
            raise
    
    def generate(self, 
                 prompt: str, 
                 system_message: Optional[str] = None,
                 temperature: Optional[float] = None, 
                 max_tokens: Optional[int] = None,
                 **kwargs) -> str:
        """
        生成文本响应
        
        Args:
            prompt: 用户输入提示
            system_message: 系统消息，可选
            temperature: 温度参数，控制随机性，可选
            max_tokens: 最大生成token数，可选
            **kwargs: 额外参数
            
        Returns:
            str: 生成的文本响应
        """
        # 构造完整的提示词
        full_prompt = ""
        
        if system_message:
            full_prompt = f"<|im_start|>system\n{system_message}<|im_end|>\n"
            
        full_prompt += f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
        
        # 设置采样参数
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens
        
        sampling_params = self._SamplingParams(
            temperature=temp,
            max_tokens=tokens,
            stop_token_ids=[],
            stop=["<|im_end|>"],
            **kwargs
        )
        
        try:
            # 记录开始时间
            import time
            start_time = time.time()

            # 生成响应
            outputs = self.engine.generate(
                prompts=[full_prompt],
                sampling_params=sampling_params
            )

            # 记录响应时间
            end_time = time.time()
            self.last_response_time_ms = (end_time - start_time) * 1000

            if outputs and len(outputs) > 0:
                output = outputs[0]
                generated_text = output.outputs[0].text

                # 估算token使用情况（VLLM没有直接提供token统计）
                prompt_tokens = len(full_prompt.split()) * 1.3  # 粗略估算
                completion_tokens = len(generated_text.split()) * 1.3  # 粗略估算

                self.last_token_usage = {
                    "prompt_tokens": int(prompt_tokens),
                    "completion_tokens": int(completion_tokens),
                    "total_tokens": int(prompt_tokens + completion_tokens)
                }

                return generated_text.strip()
            else:
                self.last_token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
                return ""
        except Exception as e:
            logger.exception(f"VLLM推理时发生错误: {str(e)}")
            self.last_token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            return f"错误: {str(e)}"
    
    def generate_chat(self, 
                     messages: List[Dict[str, str]],
                     temperature: Optional[float] = None,
                     max_tokens: Optional[int] = None,
                     **kwargs) -> str:
        """
        生成多轮对话响应
        
        Args:
            messages: 消息列表，每个消息是包含'role'和'content'的字典
            temperature: 温度参数，控制随机性，可选
            max_tokens: 最大生成token数，可选
            **kwargs: 额外参数
            
        Returns:
            str: 生成的文本响应
        """
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
        
        # 构造聊天格式的提示词
        full_prompt = ""
        
        for message in messages:
            role = message.get("role", "")
            content = message.get("content", "")
            
            full_prompt += f"<|im_start|>{role}\n{content}<|im_end|>\n"
            
        full_prompt += "<|im_start|>assistant\n"
        
        # 设置采样参数
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens
        
        sampling_params = self._SamplingParams(
            temperature=temp,
            max_tokens=tokens,
            stop_token_ids=[],
            stop=["<|im_end|>"],
            **kwargs
        )
        
        try:
            # 记录开始时间
            import time
            start_time = time.time()

            # 生成响应
            outputs = self.engine.generate(
                prompts=[full_prompt],
                sampling_params=sampling_params
            )

            # 记录响应时间
            end_time = time.time()
            self.last_response_time_ms = (end_time - start_time) * 1000

            if outputs and len(outputs) > 0:
                output = outputs[0]
                generated_text = output.outputs[0].text

                # 估算token使用情况（VLLM没有直接提供token统计）
                prompt_tokens = len(full_prompt.split()) * 1.3  # 粗略估算
                completion_tokens = len(generated_text.split()) * 1.3  # 粗略估算

                self.last_token_usage = {
                    "prompt_tokens": int(prompt_tokens),
                    "completion_tokens": int(completion_tokens),
                    "total_tokens": int(prompt_tokens + completion_tokens)
                }

                return generated_text.strip()
            else:
                self.last_token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
                return ""
        except Exception as e:
            logger.exception(f"VLLM推理时发生错误: {str(e)}")
            self.last_token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            return f"错误: {str(e)}"