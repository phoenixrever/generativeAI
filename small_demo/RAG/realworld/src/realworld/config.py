"""
配置管理模块 (Configuration Management Module)

这个模块负责管理应用程序的所有配置参数，包括 Ollama 设置、向量数据库配置、
文档处理参数等。支持从环境变量、配置文件和命令行参数加载配置。
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import json

# 获取当前文件所在的目录 要让 / 生效，BASE_DIR 必须先是一个 Path 对象：
BASE_DIR = Path(__file__).resolve().parent


@dataclass
class OllamaConfig:
    """Ollama 服务配置"""
    base_url: str = "http://localhost:11434"
    embedding_model: str = "bge-m3"  # 推荐的中文嵌入模型
    generation_model: str = "qwen2.5:7b"  # 推荐的中文生成模型
    request_timeout: int = 60  # 请求超时时间（秒）
    max_retries: int = 3  # 最大重试次数
    retry_delay: float = 1.0  # 重试延迟（秒）

@dataclass
class VectorStoreConfig:
    """向量数据库配置"""
    persist_directory: str = BASE_DIR / "db/chroma"
    collection_name: str = "documents"
    # A. 过滤“幻觉”的源头如果你不设阈值，向量数据库永远会返回最接近的 $K$ 个结果。如果没有阈值，LLM 就会一本正经地胡说八道。
    # B. 节省 Token 和性能 通过阈值过滤掉低质量的数据，可以减少传给大模型的上下文长度，既省钱又提高生成速度。
    similarity_threshold: float = 0.7  # 相似度阈值 

@dataclass
class DocumentConfig:
    """文档处理配置"""
    # default_factory 的意思是“默认工厂”。当你创建一个新的对象时，dataclass 就会调用一次这个函数，为你生成一个新的列表。
    # lambda: ['.txt', '.md', ...] 相当于定义了一个小函数，它的唯一任务就是“返回这个列表”。
    # lambda 的标准格式是： lambda 参数: 返回值
    supported_extensions: list[str] = field(default_factory=lambda: ['.txt', '.md', '.pdf', '.docx'])
    chunk_size: int = 1000  # 文本块大小
    chunk_overlap: int = 200  # 块重叠大小
    encoding: str = 'utf-8'  # 文件编码

@dataclass
class LoggingConfig:
    """日志配置"""
    enabled: bool = True
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = BASE_DIR / "logs/rag_app.log"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5

@dataclass
class CacheConfig:
    """缓存配置"""
    enabled: bool = True
    directory: str = BASE_DIR / "cache"
    ttl: int = 3600  # 缓存生存时间（秒）

@dataclass
class AppConfig:
    """应用程序总配置"""
    # 当你创建一个全新的 AppConfig 时，请顺便帮我把 OllamaConfig 也实例化（New）一个出来，塞进这个变量里。”
    # 这样你只需要执行 cfg = AppConfig()，它内部的所有子配置就都自动按照默认值准备好了。
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    vector_store: VectorStoreConfig = field(default_factory=VectorStoreConfig)
    document: DocumentConfig = field(default_factory=DocumentConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)




    # 当你写到 def from_env(cls) -> AppConfig 时，AppConfig 这个类还没完全定义完（编译器还没读到最后一行的 } 感觉）。
    # 如果你直接写类名，Python 解释器会报错，因为它不认识这个还没定义结束的类型。
    # 将类型名写在引号里 'AppConfig'。这叫 “延迟类型注解”（Postponed Evaluation of Annotations）。
    # 它告诉 Python：“这个方法返回的是一个 AppConfig 对象，但我现在还没定义完，你先把它当个字符串存着，等运行的时候再解析。
    @classmethod
    def from_env(cls) -> 'AppConfig':
        """从环境变量加载配置
            当你的 AppConfig.from_env() 运行时，os.getenv 寻找变量的逻辑是：
                最高优先级：你在终端执行程序前手动 export 的值，或者 Docker 注入的值。
                次高优先级：.env 文件里的内容（前提是你代码里写了 load_dotenv()）。
                兜底方案：你在 config.ollama.base_url 里写的那个默认值。
        """
        # 根据当前的类，创建一个全新的、干净的实例 如果你直接用 cls.ollama.base_url = ...，你修改的是类变量
        config = cls()

        # Ollama 配置
        config.ollama.base_url = os.getenv('OLLAMA_BASE_URL', config.ollama.base_url)
        config.ollama.embedding_model = os.getenv('OLLAMA_EMBEDDING_MODEL', config.ollama.embedding_model)
        config.ollama.generation_model = os.getenv('OLLAMA_GENERATION_MODEL', config.ollama.generation_model)

        # 向量存储配置
        config.vector_store.persist_directory = os.getenv('VECTOR_STORE_DIR', config.vector_store.persist_directory)

        # 日志配置
        config.logging.enabled = os.getenv('LOGGING_ENABLED', str(config.logging.enabled)).lower() in ('true', '1', 'yes')
        config.logging.level = os.getenv('LOG_LEVEL', config.logging.level)

        return config

    @classmethod
    def from_file(cls, config_path: str) -> 'AppConfig':
        """从 JSON 配置文件加载配置"""
        if not Path(config_path).exists():
            return cls()

        with open(config_path, 'r', encoding='utf-8') as f:
            # 这行代码的作用是将一个打开的文件对象转化为 Python 的字典（dict）或列表（list）。
            # 但 Python 的 json.load 是极其动态的。根据 JSON 文件的内容，它可能返回：
            #   一个 dict (如果 JSON 是 {...})
            #   一个 list (如果 JSON 是 [...])
            #   一个 str (如果 JSON 只有 "hello")
            #   一个 int / float / bool / None
            data = json.load(f)

        config = cls()

        # 递归更新配置
        def update_config(obj, data_dict):
            """
            递归地使用字典中的数据更新一个对象（通常是 dataclass 实例）的属性。
            
            :param obj: 要被更新的目标对象 (如 AppConfig 的实例)
            :param data_dict: 包含新配置数据的字典 (如从 JSON 加载的 dict)
            """
            # 遍历字典中的每一个键值对 (key 是变量名, value 是要设置的值)
            for key, value in data_dict.items():
                
                # 检查目标对象 obj 中是否存在名为 key 的属性，防止设置不存在的配置项
                if hasattr(obj, key):
                    # 获取对象中该属性当前的值 (可能是个基础类型，也可能是个子配置对象)
                    attr = getattr(obj, key)
                    
                    # 判断当前属性是否是一个“嵌套结构”：
                    # 1. isinstance(attr, dict): 属性本身是个字典
                    # 2. hasattr(attr, '__dataclass_fields__'): 属性是一个 dataclass 实例 ,__dataclass_fields__ 是区分“普通变量”和“子配置类”的指纹。
                    if isinstance(attr, dict) or hasattr(attr, '__dataclass_fields__'):
                        # 如果是嵌套结构，则递归调用自己，去更新子对象内部的属性
                        # 例如：obj 是 AppConfig，key 是 'ollama'，那么这一步就是去更新 ollama 对象里的值
                        update_config(attr, value)
                    else:
                        # 如果是普通的基础类型（str, int, float, list 等）
                        # 直接将字典里的 value 赋值给对象的属性
                        # 相当于执行了 obj.key = value
                        setattr(obj, key, value)

        update_config(config, data)
        return config

    def to_file(self, config_path: str) -> None:
        """
        将当前的配置对象（包括所有嵌套的子对象）转换并保存为 JSON 文件。
        """
        
        def to_dict(obj):
            """
            内部递归函数：将 dataclass 对象转换为普通的 Python 字典。
            """
            # 1. 检查 obj 是不是一个 dataclass 实例 传入的是 AppConfig 对象。
            # 就像之前的 update_config，利用 __dataclass_fields__ 这个“指纹”来判断
            if hasattr(obj, '__dataclass_fields__'):
                # 如果是 dataclass，就用“字典推导式”创建一个新字典
                # 遍历它所有的字段名 (k)，然后递归调用 to_dict 处理这个字段的值
                # 这样即使字段里面又嵌套了一个 dataclass，也能被转换 {k: {k1: v1}}
                return {k: to_dict(getattr(obj, k)) for k in obj.__dataclass_fields__}
            
            # 2. 检查 obj 是不是一个列表
            # 比如你的 supported_extensions: list[str] = field(default_factory=lambda: ['.txt', '.md', '.pdf', '.docx'])
            elif isinstance(obj, list):
                # 如果是列表，就遍历列表里的每个元素，递归调用 to_dict 转化为列表 ['.txt', '.md', '.pdf', '.docx']。
                # 确保列表里的每个对象（如果是 dataclass 的话）也被转换 
                return [to_dict(item) for item in obj]
            
            # 3. 如果是基础类型 (str, int, float, bool, None) 
            # 这些类型 json 库直接认识，不需要处理，直接返回即可
            else:
                return obj

        # --- 开始执行保存逻辑 ---
        
        # 首先调用上面的内部函数，把整个 AppConfig 对象变成一个巨大的嵌套字典
        config_dict = to_dict(self)
        
        # 确保配置文件所在的目录存在，如果不存在就创建它
        Path(config_path).parent.mkdir(parents=True, exist_ok=True)
        
        # 像打开普通文件一样，将字典写入 JSON 文件
        with open(config_path, 'w', encoding='utf-8') as f:
            # indent=2 是为了让生成的 JSON 文件有缩进，方便人类阅读
            # ensure_ascii=False 是为了让中文（如果有的话）正常显示，而不是显示成 \uabcd
            json.dump(config_dict, f, indent=2, ensure_ascii=False)

    def validate(self) -> list[str]:
        """验证配置的有效性，返回错误列表"""
        errors = []

        # 检查 Ollama URL 格式
        if not self.ollama.base_url.startswith(('http://', 'https://')):
            errors.append("Ollama base_url 必须以 http:// 或 https:// 开头")

        # 检查路径 不存在会创建的 目录就不检查了 
        # if not Path(self.vector_store.persist_directory).parent.exists():
        #     errors.append(f"向量存储目录的父目录不存在: {self.vector_store.persist_directory}")

        # 检查相似度阈值
        if not 0 <= self.vector_store.similarity_threshold <= 1:
            errors.append("相似度阈值必须在 0-1 之间")

        # 检查日志级别
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.logging.level.upper() not in valid_levels:
            errors.append(f"日志级别必须是以下之一: {', '.join(valid_levels)}")

        return errors

# 全局配置实例 “懒汉式单例” 的实现。
# 初始为 None，表示配置还没加载
# 1 _：私有的，通过 get_config() 来访问。外部直接调用IDE（如 VS Code）可能会给你警告
# 2 Optional[AppConfig]：类型注解，表示这个变量要么是 AppConfig 类型，要么是 None 等价于 _config : AppConfig | None

# _config: Optional[AppConfig] = None
_config : AppConfig | None = None # Union Types (联合类型) 的简写（使用 | 符号） Python 环境版本 >= 3.10

def get_config() -> AppConfig:
    """获取全局配置实例"""
    global _config  # 声明我们要修改外部定义的全局变量 _config
    
    # 如果是第一次调用，_config 是 None，就需要去加载它
    if _config is None:
        # 第一步：先创建一个基础配置（内部会去读环境变量）
        # 优先级: 环境变量 > 默认值
        _config = AppConfig.from_env()

        # 第二步：看看有没有本地的 config.json 文件
        config_file = os.getenv('RAG_CONFIG_FILE', 'config.json')
        if Path(config_file).exists():
            # 如果文件存在，用文件里的内容覆盖掉当前的 _config
            # 优先级变为：配置文件 > 环境变量 > 默认值
            _config = AppConfig.from_file(config_file)

    # 以后再调用 get_config，直接返回已经加载好的 _config，不再重复读取文件
    return _config



def set_config(config: AppConfig) -> None:
    """手动强制替换全局配置。通常用于测试代码（比如你想临时换一个测试数据库）。"""
    global _config
    _config = config


def init_config(config_path: Optional[str] = None, **overrides) -> AppConfig:
    """初始化配置，并支持通过参数临时修改某些配置项"""
    
    # 1. 拿到当前的配置（可能是默认的，也可能是读了文件的）
    config = get_config()

    # 2. 应用“覆盖参数” (overrides 是个字典，比如 {"ollama.temperature": 0.5})
    for key, value in overrides.items():
        # 情况 A：key 是一级属性，比如 init_config(debug=True)
        if hasattr(config, key):
            setattr(config, key, value)
        else:
            # 情况 B：处理点号分隔的嵌套属性，比如 init_config(ollama.base_url="...")
            parts = key.split('.')
            if len(parts) == 2:
                section, attr = parts # section="ollama", attr="base_url"
                
                # 检查 config 里面是否有 ollama 这个子对象
                if hasattr(config, section):
                    section_obj = getattr(config, section)
                    # 检查 ollama 对象里是否有 base_url 属性
                    if hasattr(section_obj, attr):
                        # 修改子对象的属性值
                        setattr(section_obj, attr, value)

    # 3. 验证配置是否合法（比如检查 URL 格式是否正确，文件路径是否存在）
    errors = config.validate()
    if errors:
        # 如果 validate 函数返回了错误信息列表，直接抛出异常，阻止程序启动
        raise ValueError(f"配置验证失败: {'; '.join(errors)}")

    # 4. 把修改好的新配置存回全局变量
    set_config(config)
    return config