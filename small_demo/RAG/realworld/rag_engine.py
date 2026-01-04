"""
RAG 引擎模块 (RAG Engine Module)

这个模块是 RAG 系统的核心，整合了文档处理、嵌入生成、向量搜索和文本生成。
提供完整的检索增强生成流程。
"""

import time
from typing import List, Dict, Any, Optional, Tuple
import logging
import requests
from retry import retry

from config import get_config
from document_processor import Document, DocumentLoader, TextSplitter, create_document_loader, create_text_splitter
from vector_store import VectorStore, EmbeddingCache, create_vector_store, create_embedding_cache
import logger

class OllamaClient:
    """Ollama API 客户端"""

    def __init__(self, base_url: str = "http://localhost:11434", timeout: int = 60):
        """
        初始化 Ollama 客户端

        参数:
            base_url: Ollama 服务地址
            timeout: 请求超时时间
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)

    @retry(exceptions=(requests.RequestException, ConnectionError), tries=3, delay=1, backoff=2)
    def generate_embedding(self, text: str, model: str) -> List[float]:
        """
        生成文本嵌入向量

        参数:
            text: 输入文本
            model: 嵌入模型名称

        返回:
            嵌入向量
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": model,
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

    @retry(exceptions=(requests.RequestException, ConnectionError), tries=3, delay=1, backoff=2)
    def generate_text(self, prompt: str, model: str, stream: bool = False, **kwargs) -> str:
        """
        生成文本

        参数:
            prompt: 输入提示
            model: 生成模型名称
            stream: 是否流式输出
            **kwargs: 其他生成参数

        返回:
            生成的文本
        """
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": stream,
                **kwargs
            }

            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()
            generated_text = data.get("response", "")

            self.logger.debug(f"文本生成成功，长度: {len(generated_text)}")
            return generated_text

        except requests.RequestException as e:
            self.logger.error(f"Ollama API 请求失败: {e}")
            raise
        except Exception as e:
            self.logger.error(f"文本生成失败: {e}")
            raise

    def list_models(self) -> List[str]:
        """列出可用的模型"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=self.timeout)
            response.raise_for_status()

            data = response.json()
            models = [model["name"] for model in data.get("models", [])]
            return models

        except Exception as e:
            self.logger.error(f"获取模型列表失败: {e}")
            return []

    def check_health(self) -> bool:
        """检查 Ollama 服务健康状态"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

class RAGEngine:
    """RAG 引擎主类"""

    def __init__(
        self,
        ollama_client: Optional[OllamaClient] = None,
        vector_store: Optional[VectorStore] = None,
        embedding_cache: Optional[EmbeddingCache] = None
    ):
        """
        初始化 RAG 引擎

        参数:
            ollama_client: Ollama 客户端实例
            vector_store: 向量存储实例
            embedding_cache: 嵌入缓存实例
        """
        self.config = get_config()
        self.logger = logging.getLogger(__name__)

        # 初始化组件
        self.ollama = ollama_client or OllamaClient(
            base_url=self.config.ollama.base_url,
            timeout=self.config.ollama.request_timeout
        )

        self.vector_store = vector_store or create_vector_store()
        self.embedding_cache = embedding_cache or create_embedding_cache()

        # 初始化文档处理组件
        self.document_loader = create_document_loader()
        self.text_splitter = create_text_splitter()

        self.logger.info("RAG 引擎初始化完成")

    def add_documents(self, file_paths: List[str], recursive: bool = True) -> int:
        """
        添加文档到知识库

        参数:
            file_paths: 文件或目录路径列表
            recursive: 是否递归处理目录

        返回:
            添加的文档块数量
        """
        start_time = time.time()
        self.logger.info(f"开始添加文档: {len(file_paths)} 个路径")

        all_documents = []

        for path in file_paths:
            path_obj = Path(path)

            if path_obj.is_file():
                # 处理单个文件
                try:
                    doc = self.document_loader.load_document(path)
                    chunks = self.text_splitter.split_document(doc)
                    all_documents.extend(chunks)
                    self.logger.info(f"处理文件: {path} -> {len(chunks)} 个块")
                except Exception as e:
                    self.logger.error(f"处理文件失败 {path}: {e}")

            elif path_obj.is_dir():
                # 处理目录
                try:
                    docs = self.document_loader.load_documents(path, recursive=recursive)
                    for doc in docs:
                        chunks = self.text_splitter.split_document(doc)
                        all_documents.extend(chunks)
                    self.logger.info(f"处理目录: {path} -> {len(docs)} 个文档")
                except Exception as e:
                    self.logger.error(f"处理目录失败 {path}: {e}")

        # 为文档生成嵌入向量
        self.logger.info("开始生成嵌入向量...")
        embedded_documents = []

        for doc in all_documents:
            # 检查缓存
            if self.config.cache.enabled:
                cached_embedding = self.embedding_cache.get(doc.content)
                if cached_embedding:
                    doc.metadata['embedding'] = cached_embedding
                    embedded_documents.append(doc)
                    continue

            # 生成新的嵌入向量
            try:
                embedding = self.ollama.generate_embedding(
                    doc.content,
                    self.config.ollama.embedding_model
                )

                # 缓存嵌入向量
                if self.config.cache.enabled:
                    self.embedding_cache.set(doc.content, embedding)

                doc.metadata['embedding'] = embedding
                embedded_documents.append(doc)

            except Exception as e:
                self.logger.error(f"生成嵌入向量失败: {e}")
                continue

        # 添加到向量存储
        added_count = self.vector_store.add_documents(embedded_documents)

        elapsed_time = time.time() - start_time
        self.logger.info(".2f"
        return added_count

    def search_documents(self, query: str, n_results: int = 5, **filters) -> List[Tuple[Document, float]]:
        """
        搜索相关文档

        参数:
            query: 查询字符串
            n_results: 返回结果数量
            **filters: 过滤条件

        返回:
            (文档, 相似度分数) 元组列表
        """
        start_time = time.time()
        self.logger.info(f"开始搜索: {query}")

        # 生成查询嵌入向量
        query_embedding = self.ollama.generate_embedding(
            query,
            self.config.ollama.embedding_model
        )

        # 搜索相似文档
        results = self.vector_store.search_similar(
            query_embedding=query_embedding,
            n_results=n_results,
            **filters
        )

        # 解析结果
        documents = []
        if results.get('documents') and results['documents'][0]:
            for i, (doc_content, metadata, distance) in enumerate(zip(
                results['documents'][0],
                results.get('metadatas', [[]])[0] or [{}] * len(results['documents'][0]),
                results.get('distances', [[]])[0] or [0.0] * len(results['documents'][0])
            )):
                # 将距离转换为相似度分数 (假设距离越小相似度越高)
                similarity_score = 1.0 / (1.0 + distance) if distance else 1.0

                doc = Document(
                    content=doc_content,
                    metadata=metadata,
                    source=metadata.get('source')
                )
                documents.append((doc, similarity_score))

        elapsed_time = time.time() - start_time
        self.logger.info(".2f"
        return documents

    def generate_answer(
        self,
        query: str,
        context_documents: List[Document],
        system_prompt: Optional[str] = None,
        **generation_kwargs
    ) -> str:
        """
        基于上下文生成回答

        参数:
            query: 用户查询
            context_documents: 相关文档列表
            system_prompt: 系统提示（可选）
            **generation_kwargs: 生成参数

        返回:
            生成的回答
        """
        start_time = time.time()
        self.logger.info("开始生成回答")

        # 构建上下文
        context_parts = []
        for i, doc in enumerate(context_documents):
            source = doc.metadata.get('source', '未知来源')
            context_parts.append(f"文档 {i+1} (来源: {source}):\n{doc.content}")

        context_text = "\n\n".join(context_parts)

        # 默认系统提示
        if system_prompt is None:
            system_prompt = """你是一个专业的知识库助手。请根据提供的上下文内容回答用户的问题。

规则：
1. 基于上下文内容回答，不要编造信息
2. 如果上下文没有相关信息，请明确说明
3. 回答要准确、简洁、有条理
4. 引用来源时标注文档编号"""

        # 构建完整提示
        full_prompt = f"""{system_prompt}

上下文信息：
{context_text}

用户问题：{query}

请基于以上上下文回答："""

        # 生成回答
        try:
            answer = self.ollama.generate_text(
                prompt=full_prompt,
                model=self.config.ollama.generation_model,
                **generation_kwargs
            )

            elapsed_time = time.time() - start_time
            self.logger.info(".2f"
            return answer

        except Exception as e:
            self.logger.error(f"生成回答失败: {e}")
            raise

    def query(
        self,
        question: str,
        n_results: int = 5,
        min_similarity: float = 0.0,
        **generation_kwargs
    ) -> Dict[str, Any]:
        """
        执行完整的 RAG 查询流程

        参数:
            question: 用户问题
            n_results: 检索文档数量
            min_similarity: 最小相似度阈值
            **generation_kwargs: 生成参数

        返回:
            包含回答和检索信息的字典
        """
        self.logger.info(f"执行 RAG 查询: {question}")

        # 1. 检索相关文档
        search_results = self.search_documents(question, n_results=n_results)

        # 2. 过滤低相似度结果
        filtered_results = [
            (doc, score) for doc, score in search_results
            if score >= min_similarity
        ]

        if not filtered_results:
            return {
                "question": question,
                "answer": "抱歉，知识库中没有找到相关信息。",
                "retrieved_documents": [],
                "processing_time": 0.0
            }

        # 3. 生成回答
        start_time = time.time()
        context_docs = [doc for doc, _ in filtered_results]

        try:
            answer = self.generate_answer(
                query=question,
                context_documents=context_docs,
                **generation_kwargs
            )
        except Exception as e:
            self.logger.error(f"生成回答失败: {e}")
            answer = f"生成回答时发生错误: {e}"

        processing_time = time.time() - start_time

        # 4. 返回结果
        result = {
            "question": question,
            "answer": answer,
            "retrieved_documents": [
                {
                    "content": doc.content,
                    "source": doc.source,
                    "similarity_score": score,
                    "metadata": doc.metadata
                }
                for doc, score in filtered_results
            ],
            "processing_time": processing_time
        }

        self.logger.info(f"RAG 查询完成，处理时间: {processing_time:.2f}秒")
        return result

    def get_stats(self) -> Dict[str, Any]:
        """获取引擎统计信息"""
        return {
            "document_count": self.vector_store.get_document_count(),
            "ollama_health": self.ollama.check_health(),
            "available_models": self.ollama.list_models(),
            "vector_store_info": self.vector_store.get_collection_info()
        }

def create_rag_engine() -> RAGEngine:
    """创建配置的 RAG 引擎实例"""
    return RAGEngine()