"""
日志配置模块 (Logging Configuration Module)

这个模块提供统一的日志配置，包括控制台输出、文件输出、日志轮转等功能。
支持不同日志级别的彩色输出和结构化日志记录。
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
from config import get_config

def setup_logging(
    level: str = "INFO",
    format_string: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    file_path: Optional[str] = None,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    enable_colors: bool = True
) -> logging.Logger:
    """
    设置应用程序的日志系统

    参数:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: 日志格式字符串
        file_path: 日志文件路径，如果为 None 则只输出到控制台
        max_file_size: 单个日志文件的最大大小（字节）
        backup_count: 保留的日志文件备份数量
        enable_colors: 是否启用控制台彩色输出

    返回:
        配置好的根日志器
    """
    # 创建根日志器
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper()))

    # 清除现有的处理器
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # 创建格式器
    formatter = ColorFormatter(format_string, enable_colors=enable_colors)

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件处理器（如果指定了文件路径）
    if file_path:
        # 确保日志目录存在
        log_file = Path(file_path)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # 创建轮转文件处理器
        file_handler = logging.handlers.RotatingFileHandler(
            filename=str(log_file),
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(logging.Formatter(format_string))
        logger.addHandler(file_handler)

    return logger

class ColorFormatter(logging.Formatter):
    """支持彩色输出的日志格式器"""

    # ANSI 颜色代码
    COLORS = {
        'DEBUG': '\033[36m',     # 青色
        'INFO': '\033[32m',      # 绿色
        'WARNING': '\033[33m',   # 黄色
        'ERROR': '\033[31m',     # 红色
        'CRITICAL': '\033[35m',  # 紫色
        'RESET': '\033[0m'       # 重置
    }

    def __init__(self, fmt: str, enable_colors: bool = True):
        super().__init__(fmt)
        self.enable_colors = enable_colors

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录，支持彩色输出"""
        # 获取原始格式化消息
        message = super().format(record)

        if self.enable_colors and sys.stdout.isatty():
            # 添加颜色
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            message = f"{color}{message}{self.COLORS['RESET']}"

        return message

def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的日志器

    参数:
        name: 日志器名称，通常使用 __name__

    返回:
        配置好的日志器实例
    """
    return logging.getLogger(name)

def init_app_logging() -> None:
    """初始化应用程序日志系统，使用配置中的设置"""
    config = get_config()

    # 检查是否在终端环境中运行（决定是否启用颜色）
    enable_colors = sys.stdout.isatty() and sys.stderr.isatty()

    setup_logging(
        level=config.logging.level,
        format_string=config.logging.format,
        file_path=config.logging.file_path,
        max_file_size=config.logging.max_file_size,
        backup_count=config.logging.backup_count,
        enable_colors=enable_colors
    )

    logger = get_logger(__name__)
    logger.info("日志系统初始化完成")
    logger.info(f"日志级别: {config.logging.level}")
    if config.logging.file_path:
        logger.info(f"日志文件: {config.logging.file_path}")

# 便捷函数
def log_function_call(func_name: str, args: Optional[dict] = None) -> None:
    """记录函数调用日志"""
    logger = get_logger(__name__)
    if args:
        logger.debug(f"调用函数: {func_name}, 参数: {args}")
    else:
        logger.debug(f"调用函数: {func_name}")

def log_performance(func_name: str, duration: float, unit: str = "秒") -> None:
    """记录性能日志"""
    logger = get_logger(__name__)
    logger.info(f"函数 {func_name} 执行时间: {duration:.3f} {unit}")

def log_error_with_context(error: Exception, context: Optional[dict] = None) -> None:
    """记录错误及其上下文信息"""
    logger = get_logger(__name__)
    logger.error(f"发生错误: {error}")
    if context:
        logger.error(f"错误上下文: {context}")
    logger.error(f"错误类型: {type(error).__name__}")

# 初始化日志系统
init_app_logging()