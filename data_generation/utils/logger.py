"""
Logging utilities with color support for better readability.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
import threading
import time


class ColoredFormatter(logging.Formatter):
    """Colored log formatter for better readability."""
    
    # ANSI color codes
    COLORS = {
        'RESET': '\033[0m',
        'BOLD': '\033[1m',
        
        # Basic colors
        'BLACK': '\033[30m',
        'RED': '\033[31m',
        'GREEN': '\033[32m',
        'YELLOW': '\033[33m',
        'BLUE': '\033[34m',
        'MAGENTA': '\033[35m',
        'CYAN': '\033[36m',
        'WHITE': '\033[37m',
        
        # Bright colors
        'BRIGHT_RED': '\033[91m',
        'BRIGHT_GREEN': '\033[92m',
        'BRIGHT_YELLOW': '\033[93m',
        'BRIGHT_BLUE': '\033[94m',
        'BRIGHT_MAGENTA': '\033[95m',
        'BRIGHT_CYAN': '\033[96m',
    }
    
    # Level-specific formatting
    LEVEL_COLORS = {
        'DEBUG': COLORS['CYAN'],
        'INFO': COLORS['GREEN'],
        'WARNING': COLORS['YELLOW'],
        'ERROR': COLORS['RED'],
        'CRITICAL': COLORS['BRIGHT_RED'] + COLORS['BOLD'],
    }
    
    # Special keywords coloring
    KEYWORD_COLORS = {
        'SUCCESS': COLORS['BRIGHT_GREEN'] + COLORS['BOLD'],
        'FAILED': COLORS['BRIGHT_RED'] + COLORS['BOLD'],
        'RETRY': COLORS['BRIGHT_YELLOW'] + COLORS['BOLD'],
        'COMPLETED': COLORS['BRIGHT_GREEN'],
        'PROCESSING': COLORS['BRIGHT_BLUE'],
        'STARTING': COLORS['BRIGHT_CYAN'],
        'FINISHED': COLORS['BRIGHT_GREEN'],
    }
    
    def __init__(self, fmt=None, use_color=True):
        super().__init__()
        self.use_color = use_color and sys.stdout.isatty()
        self.fmt = fmt or '%(asctime)s - %(name)s - [%(levelname)s] - [%(threadName)s] - %(message)s'
        
    def format(self, record):
        if not self.use_color:
            return logging.Formatter(self.fmt).format(record)
            
        # Get level color
        level_color = self.LEVEL_COLORS.get(record.levelname, '')
        reset = self.COLORS['RESET']
        
        # Color the level name
        original_levelname = record.levelname
        record.levelname = f"{level_color}{record.levelname}{reset}"
        
        # Color special keywords in message
        message = record.getMessage()
        colored_message = self._color_keywords(message)
        record.msg = colored_message
        record.args = ()
        
        # Format with colors
        formatted = logging.Formatter(self.fmt).format(record)
        
        # Restore original values
        record.levelname = original_levelname
        record.msg = message
        
        return formatted
    
    def _color_keywords(self, message: str) -> str:
        """Apply colors to special keywords in the message."""
        colored_message = message
        
        for keyword, color in self.KEYWORD_COLORS.items():
            if keyword.lower() in message.lower():
                # Use word boundaries to avoid partial matches
                import re
                pattern = re.compile(f'\\b{re.escape(keyword)}\\b', re.IGNORECASE)
                colored_message = pattern.sub(
                    f"{color}{keyword}{self.COLORS['RESET']}", 
                    colored_message
                )
        
        return colored_message


class ProgressFormatter(ColoredFormatter):
    """Special formatter for progress messages with visual indicators."""
    
    PROGRESS_SYMBOLS = {
        'start': '🚀',
        'success': '✅',
        'error': '❌',
        'warning': '⚠️',
        'info': '💡',
        'processing': '⚙️',
        'completed': '🎉',
        'retry': '🔄',
    }
    
    def format(self, record):
        message = record.getMessage()
        
        # Add symbols based on message content
        for keyword, symbol in self.PROGRESS_SYMBOLS.items():
            if keyword.lower() in message.lower():
                record.msg = f"{symbol} {message}"
                record.args = ()
                break
                
        return super().format(record)


def setup_logging(console_level: str = "INFO", 
                 file_level: str = "DEBUG",
                 log_dir: str = "./logs",
                 use_color: bool = True,
                 use_progress_symbols: bool = True) -> None:
    """
    Setup logging with color support and multiple outputs.
    
    Args:
        console_level: Console logging level
        file_level: File logging level  
        log_dir: Directory for log files
        use_color: Enable colored console output
        use_progress_symbols: Enable progress symbols
    """
    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Clear any existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    # Set root level to most verbose
    root_logger.setLevel(logging.DEBUG)
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, console_level.upper()))
    
    if use_progress_symbols:
        console_formatter = ProgressFormatter(use_color=use_color)
    else:
        console_formatter = ColoredFormatter(use_color=use_color)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (detailed, no colors)
    file_handler = logging.FileHandler(log_path / "pipeline.log", encoding='utf-8')
    file_handler.setLevel(getattr(logging, file_level.upper()))
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - [%(levelname)s] - [%(threadName)s] - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(name)


def log_raw_response(generator_type: str, item_id: str, thread_id: int, response: str) -> None:
    """Log raw LLM responses to separate files."""
    log_dir = Path("./logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create raw response log file
    raw_log_path = log_dir / f"{generator_type}_raw.log"
    
    # Thread-safe logging
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"""
{'='*80}
TIMESTAMP: {timestamp}
GENERATOR: {generator_type}
ITEM_ID: {item_id}
THREAD_ID: {thread_id}
{'='*80}
{response}
{'='*80}

"""
    
    # Use thread-local lock for file writing
    if not hasattr(log_raw_response, '_locks'):
        log_raw_response._locks = {}
    
    if raw_log_path not in log_raw_response._locks:
        log_raw_response._locks[raw_log_path] = threading.Lock()
    
    with log_raw_response._locks[raw_log_path]:
        with open(raw_log_path, 'a', encoding='utf-8') as f:
            f.write(log_entry)


# Convenience functions for colored logging
def log_success(logger: logging.Logger, message: str):
    """Log success message with special formatting."""
    logger.info(f"SUCCESS: {message}")

def log_error(logger: logging.Logger, message: str):
    """Log error message with special formatting."""
    logger.error(f"FAILED: {message}")

def log_processing(logger: logging.Logger, message: str):
    """Log processing message with special formatting."""
    logger.info(f"PROCESSING: {message}")

def log_completed(logger: logging.Logger, message: str):
    """Log completion message with special formatting."""
    logger.info(f"COMPLETED: {message}")

def log_retry(logger: logging.Logger, message: str):
    """Log retry message with special formatting."""
    logger.warning(f"RETRY: {message}")

def log_starting(logger: logging.Logger, message: str):
    """Log starting message with special formatting."""
    logger.info(f"STARTING: {message}")

def log_finished(logger: logging.Logger, message: str):
    """Log finished message with special formatting."""
    logger.info(f"FINISHED: {message}")


# ANSI color codes
class Colors:
    """ANSI color codes for terminal output."""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    # Regular colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    GRAY = '\033[90m'
    
    # Background colors
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'


class ColoredLogger:
    """
    Logger with colored output for better readability.
    """
    
    def __init__(self, name: str):
        """Initialize colored logger."""
        self.name = name
        self.colors_enabled = sys.stdout.isatty()  # Only use colors in terminal
        
    def _format_message(self, message: str, color: str = None, bold: bool = False) -> str:
        """Format message with color if enabled."""
        if not self.colors_enabled or color is None:
            return f"[{self.name}] {message}"
            
        color_code = getattr(Colors, color.upper(), Colors.RESET)
        bold_code = Colors.BOLD if bold else ''
        
        return f"{bold_code}{color_code}[{self.name}] {message}{Colors.RESET}"
        
    def debug(self, message: str, color: str = 'gray'):
        """Log debug message."""
        print(self._format_message(message, color))
        
    def info(self, message: str, color: str = None):
        """Log info message."""
        print(self._format_message(message, color))
        
    def warning(self, message: str, color: str = 'yellow'):
        """Log warning message."""
        print(self._format_message(f"⚠️  {message}", color, bold=True))
        
    def error(self, message: str, color: str = 'red'):
        """Log error message."""
        print(self._format_message(f"❌ {message}", color, bold=True))
        
    def success(self, message: str, color: str = 'green'):
        """Log success message."""
        print(self._format_message(f"✅ {message}", color))
        
    def progress(self, message: str, color: str = 'blue'):
        """Log progress message."""
        print(self._format_message(f"⏳ {message}", color))


# Export all functions
__all__ = [
    'setup_logging', 'get_logger', 'log_raw_response',
    'log_success', 'log_error', 'log_processing', 
    'log_completed', 'log_retry', 'log_starting', 'log_finished',
    'ColoredFormatter', 'ProgressFormatter', 'ColoredLogger'
]
