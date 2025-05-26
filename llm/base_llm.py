from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union, Any

class BaseLLM(ABC):
    """
    大语言模型基类，定义与LLM交互的通用接口
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化LLM
        
        Args:
            config: 配置字典，包含模型参数
        """
        self.config = config
        self.model = config.get('model', '')
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 1024)
        
        # 从parameters获取其他参数
        parameters = config.get('parameters', {})
        # 是否发送历史消息，默认为False
        self.send_history = parameters.get('send_history', False)
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    def get_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return self.config.copy() 