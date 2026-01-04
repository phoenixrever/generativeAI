"""
嵌入器接口和实现 (Embedder Interface and Implementations)

这个模块定义了统一的嵌入器接口，以及不同嵌入方式的具体实现：
- OllamaDirectEmbedder: 直接调用 Ollama API
- OllamaLangchainEmbedder: 使用 LangChain OllamaEmbeddings
- OnlineModelEmbedder: 线上大模型 (使用 Google Gemini)

注意：本模块使用 Python 标准 logging 模块记录日志。
日志配置通过项目根目录的 logger.py 模块进行全局设置，
所有 logger 实例都会继承根 logger 的配置（包括输出格式、级别、文件输出等）。
"""

from abc import ABC, abstractmethod
from typing import List, Optional
import logging  # 导入标准 logging 模块，用于记录日志
import requests
from retry import retry

try:
    from langchain_ollama import OllamaEmbeddings
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

# pip install -e ".[gemini]"
try:
    from google import genai  # Google 在 2024 年底/2025 年初刚推出的全新统一 SDK（被称为 Multimodal Live API 时代的产品）。老的是 google-generativeai
    GOOGLE_GENAI_AVAILABLE = True
except ImportError:
    GOOGLE_GENAI_AVAILABLE = False

# ABC 是 Abstract Base Class（抽象基类）的缩写。它是 Python abc 模块提供的一个工具，用来定义“规范”或“模板”。
# 抽象基类不能直接实例化，必须由子类实现所有抽象方法。
class Embedder(ABC):
    """嵌入器抽象基类

    定义了嵌入器的统一接口，所有嵌入器实现都必须继承此类并实现其抽象方法。
    这样可以保证不同嵌入器实现的一致性和可替换性。
    """

    @abstractmethod
    def generate_embedding(self, text: str) -> List[float]:
        """
        生成文本嵌入向量

        参数:
            text: 输入文本

        返回:
            嵌入向量
        """
        pass

    @abstractmethod
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        批量生成文本嵌入向量

        参数:
            texts: 输入文本列表

        返回:
            嵌入向量列表
        """
        pass

    @abstractmethod
    def check_health(self) -> bool:
        """检查服务健康状态"""
        pass


class OllamaDirectEmbedder(Embedder):
    """直接调用 Ollama API 的嵌入器"""

    def __init__(self, base_url: str = "http://localhost:11434", timeout: int = 60, model: str = "bge-m3"):
        """
        初始化 Ollama 直接嵌入器

        参数:
            base_url: Ollama 服务地址
            timeout: 请求超时时间
            model: 嵌入模型名称
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.model = model
        self.logger = logging.getLogger(__name__)  # 创建模块级别的logger，用于记录该类的操作日志

    @retry(exceptions=(requests.RequestException, ConnectionError), tries=3, delay=1, backoff=2)
    def generate_embedding(self, text: str) -> List[float]:
        """生成单个文本的嵌入向量"""
        try:
            self.logger.debug(f"使用直接 API 调用生成嵌入向量")
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.model,
                    "prompt": text
                },
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()
            embedding = data.get("embedding")

            if not embedding:
                raise ValueError("响应中没有嵌入向量")

            self.logger.debug(f"生成嵌入向量成功，维度: {len(embedding)}")
            return embedding

        except requests.RequestException as e:
            self.logger.error(f"Ollama API 请求失败: {e}")
            raise
        except Exception as e:
            self.logger.error(f"生成嵌入向量失败: {e}")
            raise

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """批量生成嵌入向量（逐个调用）"""
        embeddings = []
        for text in texts:
            embedding = self.generate_embedding(text)
            embeddings.append(embedding)
        return embeddings

    def check_health(self) -> bool:
        """检查 Ollama 服务健康状态"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False


class OllamaLangchainEmbedder(Embedder):
    """使用 LangChain OllamaEmbeddings 的嵌入器"""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "bge-m3"):
        """
        初始化 LangChain Ollama 嵌入器

        参数:
            base_url: Ollama 服务地址
            model: 嵌入模型名称
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.logger = logging.getLogger(__name__)  # 创建模块级别的logger，用于记录该类的操作日志

        # 初始化 LangChain 嵌入器
        self.langchain_embedder = None
        if LANGCHAIN_AVAILABLE:
            try:
                self.langchain_embedder = OllamaEmbeddings(
                    model=self.model,
                    base_url=self.base_url
                )
                self.logger.info("LangChain OllamaEmbeddings 初始化成功")
            except Exception as e:
                self.logger.error(f"LangChain OllamaEmbeddings 初始化失败: {e}")
                raise
        else:
            raise ImportError("langchain-ollama 未安装，无法使用 LangChain 嵌入器")

    def generate_embedding(self, text: str) -> List[float]:
        """生成单个文本的嵌入向量"""
        if not self.langchain_embedder:
            raise RuntimeError("LangChain 嵌入器未初始化")

        try:
            self.logger.debug(f"使用 LangChain OllamaEmbeddings 生成嵌入向量")
            embedding = self.langchain_embedder.embed_query(text)
            self.logger.debug(f"生成嵌入向量成功，维度: {len(embedding)}")
            return embedding
        except Exception as e:
            self.logger.error(f"LangChain 嵌入生成失败: {e}")
            raise

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """批量生成嵌入向量"""
        if not self.langchain_embedder:
            raise RuntimeError("LangChain 嵌入器未初始化")

        try:
            self.logger.debug(f"使用 LangChain OllamaEmbeddings 批量生成嵌入向量")
            embeddings = self.langchain_embedder.embed_documents(texts)
            self.logger.debug(f"批量生成嵌入向量成功，数量: {len(embeddings)}")
            return embeddings
        except Exception as e:
            self.logger.error(f"LangChain 批量嵌入生成失败: {e}")
            raise

    def check_health(self) -> bool:
        """检查 Ollama 服务健康状态"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False


class OnlineModelEmbedder(Embedder):
    """线上大模型嵌入器 (使用 Google Gemini)"""

    def __init__(self, api_key: str, model: str = "models/text-embedding-004", base_url: Optional[str] = None):
        """
        初始化线上模型嵌入器

        参数:
            api_key: Google AI API 密钥
            model: 模型名称 (默认使用 Gemini embedding model)
            base_url: 自定义 API 地址（可选，暂不支持）
        """
        if not GOOGLE_GENAI_AVAILABLE:
            raise ImportError("google-generativeai 未安装，请运行: pip install google-generativeai")

        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)  # 创建模块级别的logger，用于记录该类的操作日志

        # 初始化 Gemini API
        try:
            genai.Client(api_key=self.api_key)
            self.logger.info(f"Gemini 嵌入器初始化成功，使用模型: {self.model}")
        except Exception as e:
            self.logger.error(f"Gemini API 初始化失败: {e}")
            raise

    def generate_embedding(self, text: str) -> List[float]:
        """生成单个文本的嵌入向量"""
        try:
            self.logger.debug(f"使用 Gemini 生成嵌入向量")
            result = genai.models.embed(
                model=self.model,
                content=text,
                task_type="retrieval_document"
            )

            embedding = result['embedding']
            self.logger.debug(f"生成嵌入向量成功，维度: {len(embedding)}")
            return embedding

        except Exception as e:
            self.logger.error(f"Gemini 嵌入生成失败: {e}")
            raise

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """批量生成嵌入向量"""
        try:
            self.logger.debug(f"使用 Gemini 批量生成嵌入向量，数量: {len(texts)}")

            # Gemini API 支持批量嵌入
            result = genai.models.embed(
                model=self.model,
                content=texts,
                task_type="retrieval_document"
            )

            embeddings = result['embedding']
            self.logger.debug(f"批量生成嵌入向量成功，数量: {len(embeddings)}")
            return embeddings

        except Exception as e:
            self.logger.error(f"Gemini 批量嵌入生成失败: {e}")
            raise

    def check_health(self) -> bool:
        """检查 Gemini API 健康状态"""
        try:
            # 尝试生成一个简单的嵌入来测试连接
            test_result = genai.models.embed(
                model=self.model,
                content="test",
                task_type="retrieval_document"
            )
            return 'embedding' in test_result and len(test_result['embedding']) > 0
        except Exception as e:
            self.logger.error(f"Gemini 健康检查失败: {e}")
            return False


def create_embedder(embedder_type: str, **kwargs) -> Embedder:
    """
    创建嵌入器工厂函数

    参数:
        embedder_type: 嵌入器类型 ('ollama_direct', 'ollama_langchain', 'online')
        **kwargs: 嵌入器初始化参数

    返回:
        嵌入器实例
    """
    if embedder_type == "ollama_direct":
        return OllamaDirectEmbedder(**kwargs)
    elif embedder_type == "ollama_langchain":
        return OllamaLangchainEmbedder(**kwargs)
    elif embedder_type == "online":
        # 为 Gemini 设置默认参数
        kwargs.setdefault("model", "models/text-embedding-004")
        return OnlineModelEmbedder(**kwargs)
    else:
        raise ValueError(f"不支持的嵌入器类型: {embedder_type}")