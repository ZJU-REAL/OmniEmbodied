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


def setup_logging(
    name: str,
    level: str = "INFO",
    log_file: Optional[str] = None,
    console_output: bool = True,
    format_style: str = "simple",
    enable_colors: bool = True
) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 记录器名称
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件路径，如果为None则不写入文件
        console_output: 是否输出到控制台
        format_style: 格式样式 ("simple", "detailed", "debug")
        enable_colors: 是否启用颜色（仅影响控制台输出）
    
    Returns:
        配置好的Logger对象
    """
    # 获取日志级别
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # 创建logger
    logger = logging.getLogger(name)
    logger.setLevel(numeric_level)
    
    # 清除已有的处理器
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 定义格式
    formats = {
        "simple": "%(asctime)s [%(levelname)s] %(message)s",
        "detailed": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        "debug": "%(asctime)s [%(levelname)s] %(name)s (%(location)s): %(message)s"
    }
    
    log_format = formats.get(format_style, formats["simple"])
    date_format = "%H:%M:%S"
    
    # 控制台处理器
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        
        # 为控制台处理器创建格式化器
        console_formatter = ColorizedFormatter(
            log_format, date_format, 
            use_colors=enable_colors,
            is_debug_format=(format_style == "debug")
        )
        console_handler.setFormatter(console_formatter)
        
        # 添加一个过滤器来标记是否应该使用颜色
        def add_color_flag(record):
            record.use_color = True
            return True
        console_handler.addFilter(add_color_flag)
        
        logger.addHandler(console_handler)
    
    # 文件处理器
    if log_file:
        # 确保日志目录存在
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(numeric_level)
        
        # 文件处理器不使用颜色
        file_formatter = ColorizedFormatter(
            log_format, date_format,
            use_colors=False,
            is_debug_format=(format_style == "debug")
        )
        file_handler.setFormatter(file_formatter)
        
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Name of the logger
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# 创建默认logger
default_logger = setup_logging("default") 