"""
日志配置模块 (Logging Configuration Module)

提供统一的日志配置，支持以下功能：
- 控制台彩色输出
- 文件输出与轮转
- 灵活的日志级别控制
- 简洁的命令行参数集成

快速使用:
    from realworld.logger import get_logger
    
    logger = get_logger(__name__)
    logger.info("开始处理...")
    
    # CLI 端无需手动初始化，直接使用参数
    # python cli.py query "..." -v  # 详细模式
    # python cli.py query "..." -q  # 安静模式
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
from .config import get_config

def setup_logging(
    level: Optional[str] = None,
    enable_file: bool = True,
    enable_colors: bool = True
) -> logging.Logger:
    """
    设置应用程序的日志系统（使用配置文件中的参数）

    参数:
        level: 日志级别，默认使用配置文件中的设置
        enable_file: 是否启用文件输出
        enable_colors: 是否启用控制台彩色输出

    返回:
        配置好的根日志器
    """
    config = get_config()
    
    # 使用参数或配置中的值
    log_level = level or config.logging.level
    format_string = config.logging.format
    file_path = config.logging.file_path if enable_file else None
    max_file_size = config.logging.max_file_size
    backup_count = config.logging.backup_count

    # 创建根日志器
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))

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

def init_app_logging(level: Optional[str] = None, enable_file: bool = True) -> None:
    """
    初始化应用程序日志系统

    参数:
        level: 日志级别（可选，使用配置文件中的默认值）
        enable_file: 是否启用文件输出
    """
    config = get_config()

    # 如果配置中禁用了日志，则使用静默模式
    if not config.logging.enabled:
        logger = logging.getLogger()
        logger.setLevel(logging.CRITICAL)
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        return

    # 检查是否在终端环境中运行
    enable_colors = sys.stdout.isatty() and sys.stderr.isatty()

    # 设置日志
    setup_logging(level=level, enable_file=enable_file, enable_colors=enable_colors)

    logger = get_logger(__name__)
    logger.debug("日志系统初始化完成")

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

def configure_logging(quiet: bool = False, verbose: bool = False, no_file: bool = False) -> None:
    """
    快捷日志配置函数

    参数:
        quiet: 安静模式（禁用日志输出）
        verbose: 详细模式（DEBUG 级别）
        no_file: 禁用文件输出
    """
    config = get_config()

    # 处理安静模式
    if quiet:
        config.logging.enabled = False
        init_app_logging(enable_file=False)
        return

    # 处理详细模式
    level = "DEBUG" if verbose else None

    # 初始化日志
    init_app_logging(level=level, enable_file=not no_file)

def disable_logging() -> None:
    """禁用所有日志输出"""
    config = get_config()
    config.logging.enabled = False
    init_app_logging(enable_file=False)

def initialize_logging(args, config) -> None:
    """
    从命令行参数初始化日志系统

    参数:
        args: 命令行参数
        config: 配置对象
    """
    # 处理特殊标志
    verbose = getattr(args, 'verbose', False)
    quiet = getattr(args, 'quiet', False) or getattr(args, 'no_log', False)
    no_file = getattr(args, 'no_file', False)

    try:
        configure_logging(quiet=quiet, verbose=verbose, no_file=no_file)
    except Exception as e:
        # 如果日志初始化失败，至少要有基本的日志
        logging.basicConfig(level=logging.INFO)
        logging.getLogger(__name__).warning(f"日志系统初始化失败: {e}")

__all__ = [
    'get_logger',
    'setup_logging',
    'init_app_logging',
    'configure_logging',
    'initialize_logging',
    'disable_logging',
    'ColorFormatter',
]