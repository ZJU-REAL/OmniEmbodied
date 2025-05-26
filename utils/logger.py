import os
import logging
import sys
from typing import Optional
import time

class ColorizedFormatter(logging.Formatter):
    """
    为不同级别的日志提供不同颜色的格式化器
    """
    # 定义ANSI颜色代码
    COLORS = {
        'DEBUG': '\033[36m',     # 青色
        'INFO': '\033[32m',      # 绿色
        'WARNING': '\033[33m',   # 黄色
        'ERROR': '\033[31m',     # 红色
        'CRITICAL': '\033[35m',  # 紫色
        'RESET': '\033[0m',      # 重置
    }
    
    def __init__(self, fmt=None, datefmt=None, style='%', use_colors=True, is_debug_format=False):
        super().__init__(fmt, datefmt, style)
        self.use_colors = use_colors
        self.is_debug_format = is_debug_format
    
    def format(self, record):
        # 保存原始的levelname
        levelname = record.levelname
        
        # 添加颜色，如果使用颜色且不是文件处理器
        if self.use_colors and hasattr(record, 'use_color') and record.use_color:
            color_start = self.COLORS.get(levelname, self.COLORS['RESET'])
            color_end = self.COLORS['RESET']
            record.levelname = f"{color_start}{levelname}{color_end}"
        
        # 对调试日志增加更多上下文信息
        if self.is_debug_format and record.levelno == logging.DEBUG:
            # 添加文件名、行号等详细信息
            record.message = record.getMessage()
            record.pathname = record.pathname.replace('\\', '/')
            filename = record.pathname.split('/')[-1]
            record.location = f"{filename}:{record.lineno}"
        else:
            # 对于非调试级别或非调试格式的日志，添加一个空的location字段
            if not hasattr(record, 'location'):
                record.location = ""
        
        result = super().format(record)
        
        # 恢复原始的levelname，避免影响其他处理器
        record.levelname = levelname
        
        return result

class ColorizedConsoleHandler(logging.StreamHandler):
    """
    支持颜色输出的控制台处理器
    """
    def __init__(self, stream=None):
        super().__init__(stream)
        
    def emit(self, record):
        # 确保严格按照级别过滤日志
        if not self.filter(record):
            return
            
        # 标记此记录需要使用颜色
        record.use_color = True
        super().emit(record)

def setup_logger(
    log_name: str = "embodied_agent",
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
    log_to_console: bool = True,
    file_log_level: Optional[int] = None,
    console_log_level: Optional[int] = None,
    propagate_to_root: bool = True
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
        propagate_to_root: 是否将日志级别传播到根logger，默认为True
        
    Returns:
        logging.Logger: 设置好的日志记录器
    """
    logger = logging.getLogger(log_name)
    
    # 设置根日志级别，确保所有处理器都能正确过滤
    if log_level < logging.DEBUG:
        logger.setLevel(logging.DEBUG)  # 确保不会低于DEBUG
    else:
        logger.setLevel(log_level)
    
    # 设置根logger的级别，以便传播到所有子logger
    if propagate_to_root:
        root_logger = logging.getLogger()
        if log_level < logging.DEBUG:
            root_logger.setLevel(logging.DEBUG)
        else:
            root_logger.setLevel(log_level)
    
    # 清除现有的处理器
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 基本格式
    base_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    # 调试格式 - 包含文件名和行号
    debug_fmt = '%(asctime)s - %(name)s - %(levelname)s - [%(location)s] - %(message)s'
    
    # 添加文件处理器
    if log_file:
        # 确保目录存在
        log_dir = os.path.dirname(os.path.abspath(log_file))
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
            
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        # 确保设置正确的文件日志级别
        actual_file_level = file_log_level if file_log_level is not None else log_level
        file_handler.setLevel(actual_file_level)
        
        # 针对不同级别使用不同格式
        if actual_file_level <= logging.DEBUG:
            file_formatter = ColorizedFormatter(debug_fmt, datefmt='%Y-%m-%d %H:%M:%S', use_colors=False, is_debug_format=True)
        else:
            file_formatter = logging.Formatter(base_fmt, datefmt='%Y-%m-%d %H:%M:%S')
            
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # 添加控制台处理器
    if log_to_console:
        console_handler = ColorizedConsoleHandler(sys.stdout)
        # 确保设置正确的控制台日志级别
        actual_console_level = console_log_level if console_log_level is not None else log_level
        console_handler.setLevel(actual_console_level)
        
        # 针对不同级别使用不同格式
        if actual_console_level <= logging.DEBUG:
            console_formatter = ColorizedFormatter(debug_fmt, datefmt='%Y-%m-%d %H:%M:%S', is_debug_format=True)
        else:
            console_formatter = ColorizedFormatter(base_fmt, datefmt='%Y-%m-%d %H:%M:%S')
            
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    return logger 