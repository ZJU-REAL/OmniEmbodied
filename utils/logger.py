import os
import logging
import sys
from typing import Optional

def setup_logger(
    log_name: str = "embodied_agent",
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
    log_to_console: bool = True,
    file_log_level: Optional[int] = None,
    console_log_level: Optional[int] = None
) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        log_name: 日志记录器名称
        log_level: 默认日志级别
        log_file: 日志文件路径，可选
        log_to_console: 是否输出到控制台
        file_log_level: 文件日志级别，默认与log_level相同
        console_log_level: 控制台日志级别，默认与log_level相同
        
    Returns:
        logging.Logger: 设置好的日志记录器
    """
    logger = logging.getLogger(log_name)
    logger.setLevel(log_level)
    
    # 清除现有的处理器
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 设置格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 添加文件处理器
    if log_file:
        # 确保目录存在
        os.makedirs(os.path.dirname(os.path.abspath(log_file)), exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(file_log_level or log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # 添加控制台处理器
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(console_log_level or log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger 