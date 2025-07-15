import logging
import os
import time
from typing import Dict, Any, Optional

class SimulationLogger:
    """模拟器日志工具 - 负责记录模拟器操作日志"""
    
    def __init__(self, log_level: str = "INFO", 
                log_file: Optional[str] = None,
                log_to_console: bool = True):
        """
        初始化日志工具
        
        Args:
            log_level: 日志级别，可选值为DEBUG, INFO, WARNING, ERROR, CRITICAL
            log_file: 日志文件路径，如果为None则不保存到文件
            log_to_console: 是否输出到控制台
        """
        # 创建logger
        self.logger = logging.getLogger("embodied_simulator")
        
        # 设置日志级别
        level = getattr(logging, log_level.upper(), logging.INFO)
        self.logger.setLevel(level)
        
        # 清除已有的handler
        self.logger.handlers = []
        
        # 创建格式化器
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # 如果需要输出到控制台
        if log_to_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # 如果需要输出到文件
        if log_file:
            # 确保日志目录存在
            log_dir = os.path.dirname(os.path.abspath(log_file))
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
                
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def debug(self, message: str) -> None:
        """记录DEBUG级别日志"""
        self.logger.debug(message)
    
    def info(self, message: str) -> None:
        """记录INFO级别日志"""
        self.logger.info(message)
    
    def warning(self, message: str) -> None:
        """记录WARNING级别日志"""
        self.logger.warning(message)
    
    def error(self, message: str) -> None:
        """记录ERROR级别日志"""
        self.logger.error(message)
    
    def critical(self, message: str) -> None:
        """记录CRITICAL级别日志"""
        self.logger.critical(message)
    
    def log_action(self, agent_id: str, action: str, status: str, message: str) -> None:
        """
        记录动作日志
        
        Args:
            agent_id: 智能体ID
            action: 动作命令
            status: 执行状态
            message: 反馈消息
        """
        self.info(f"Agent: {agent_id} | Action: {action} | Status: {status} | Message: {message}")
    
    def log_state_change(self, entity_id: str, property_name: str, old_value: Any, new_value: Any) -> None:
        """
        记录状态变化日志
        
        Args:
            entity_id: 实体ID (物体或智能体)
            property_name: 变化的属性名
            old_value: 旧值
            new_value: 新值
        """
        self.debug(f"State Change: {entity_id}.{property_name} changed from {old_value} to {new_value}")
    
    def log_error(self, error_type: str, message: str) -> None:
        """
        记录错误日志
        
        Args:
            error_type: 错误类型
            message: 错误消息
        """
        self.error(f"{error_type}: {message}")
        
    def start_session(self, config: Dict[str, Any]) -> None:
        """
        记录会话开始
        
        Args:
            config: 配置信息
        """
        self.info(f"=== Simulation Session Started at {time.strftime('%Y-%m-%d %H:%M:%S')} ===")
        self.info(f"Configuration: {config}")
    
    def end_session(self) -> None:
        """记录会话结束"""
        self.info(f"=== Simulation Session Ended at {time.strftime('%Y-%m-%d %H:%M:%S')} ===")
        self.info("="*50) 