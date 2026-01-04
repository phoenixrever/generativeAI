"""
向量存储模块 (Vector Store Module)

这个模块负责管理向量数据库的创建、更新、查询和维护操作。
使用 ChromaDB 作为底层向量存储，支持高效的相似度搜索。
"""

import time
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import hashlib
import pickle
import logging

import chromadb
from chromadb.config import Settings

from .config import get_config
from .document_processor import Document
from . import logger

class VectorStore:
    """向量存储管理器"""

    def __init__(self, persist_directory: str, collection_name: str = "documents"):
        """
        初始化向量存储

        参数:
            persist_directory: 持久化存储目录
            collection_name: 集合名称
        """
        self.persist_directory = Path(persist_directory)
        self.collection_name = collection_name
        self.logger = logging.getLogger(__name__)

        # 确保目录存在
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        # 初始化 ChromaDB 客户端
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(anonymized_telemetry=False)
        )

        # 获取或创建集合
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "RAG 文档向量集合"}
        )

        self.logger.info(f"向量存储初始化完成: {persist_directory}/{collection_name}")

    def _generate_id(self, content: str, metadata: Dict[str, Any]) -> str:
        """生成文档的唯一ID"""
        # 使用内容和源文件的哈希作为ID
        source = metadata.get('source', '')
        content_hash = hashlib.md5((source + content).encode('utf-8')).hexdigest()
        return f"{source}_{content_hash}"

    def add_documents(self, documents: List[Document], batch_size: int = 100) -> int:
        """
        批量添加文档到向量存储

        参数:
            documents: 要添加的文档列表
            batch_size: 批处理大小

        返回:
            添加的文档数量
        """
        if not documents:
            return 0

        total_added = 0

        # 分批处理
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]

            ids = []
            texts = []
            metadatas = []
            embeddings = []  # 如果文档已经包含嵌入向量

            for doc in batch:
                doc_id = self._generate_id(doc.content, doc.metadata)

                # 检查文档是否已存在
                existing = self.collection.get(ids=[doc_id])
                if existing['ids']:
                    self.logger.debug(f"文档已存在，跳过: {doc_id}")
                    continue

                ids.append(doc_id)
                texts.append(doc.content)
                metadatas.append(doc.metadata)

                # 注意：这里假设嵌入向量由外部提供
                # 在实际使用中，需要先调用嵌入模型生成向量

            if ids:
                try:
                    self.collection.add(
                        ids=ids,
                        documents=texts,
                        metadatas=metadatas
                    )
                    total_added += len(ids)
                    self.logger.info(f"添加批次 {i//batch_size + 1}: {len(ids)} 个文档")
                except Exception as e:
                    self.logger.error(f"添加批次失败: {e}")
                    raise

        self.logger.info(f"总共添加了 {total_added} 个文档")
        return total_added

    def search_similar(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        搜索相似文档

        参数:
            query_embedding: 查询的嵌入向量
            n_results: 返回结果数量
            where: 元数据过滤条件
            where_document: 文档内容过滤条件

        返回:
            搜索结果字典
        """
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where,
                where_document=where_document
            )

            self.logger.debug(f"相似搜索完成，返回 {len(results.get('documents', [[]])[0])} 个结果")
            return results

        except Exception as e:
            self.logger.error(f"相似搜索失败: {e}")
            raise

    def delete_documents(self, ids: List[str]) -> bool:
        """
        删除指定ID的文档

        参数:
            ids: 要删除的文档ID列表

        返回:
            删除是否成功
        """
        try:
            self.collection.delete(ids=ids)
            self.logger.info(f"删除了 {len(ids)} 个文档")
            return True
        except Exception as e:
            self.logger.error(f"删除文档失败: {e}")
            return False

    def update_document(self, doc_id: str, document: Document) -> bool:
        """
        更新指定ID的文档

        参数:
            doc_id: 文档ID
            document: 新的文档对象

        返回:
            更新是否成功
        """
        try:
            self.collection.update(
                ids=[doc_id],
                documents=[document.content],
                metadatas=[document.metadata]
            )
            self.logger.info(f"更新文档: {doc_id}")
            return True
        except Exception as e:
            self.logger.error(f"更新文档失败: {e}")
            return False

    def get_document_count(self) -> int:
        """获取集合中的文档数量"""
        try:
            count = self.collection.count()
            return count
        except Exception as e:
            self.logger.error(f"获取文档数量失败: {e}")
            return 0

    def list_collections(self) -> List[str]:
        """列出所有集合"""
        try:
            collections = self.client.list_collections()
            return [col.name for col in collections]
        except Exception as e:
            self.logger.error(f"列出集合失败: {e}")
            return []

    def clear_collection(self) -> bool:
        """清空当前集合"""
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "RAG 文档向量集合"}
            )
            self.logger.info(f"清空集合: {self.collection_name}")
            return True
        except Exception as e:
            self.logger.error(f"清空集合失败: {e}")
            return False

    def get_collection_info(self) -> Dict[str, Any]:
        """获取集合信息"""
        return {
            "name": self.collection_name,
            "document_count": self.get_document_count(),
            "persist_directory": str(self.persist_directory)
        }

class EmbeddingCache:
    """嵌入向量缓存"""

    def __init__(self, cache_dir: str = "./cache/embeddings"):
        """
        初始化缓存

        参数:
            cache_dir: 缓存目录
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)

    def _get_cache_key(self, text: str) -> str:
        """生成缓存键"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def get(self, text: str) -> Optional[List[float]]:
        """获取缓存的嵌入向量"""
        cache_key = self._get_cache_key(text)
        cache_file = self.cache_dir / f"{cache_key}.pkl"

        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    embedding = pickle.load(f)
                self.logger.debug(f"缓存命中: {cache_key}")
                return embedding
            except Exception as e:
                self.logger.warning(f"读取缓存失败: {e}")
                cache_file.unlink(missing_ok=True)  # 删除损坏的缓存文件

        return None

    def set(self, text: str, embedding: List[float], ttl: int = 3600) -> None:
        """设置缓存"""
        cache_key = self._get_cache_key(text)
        cache_file = self.cache_dir / f"{cache_key}.pkl"

        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(embedding, f)
            self.logger.debug(f"缓存设置: {cache_key}")
        except Exception as e:
            self.logger.warning(f"设置缓存失败: {e}")

    def clear(self) -> None:
        """清空缓存"""
        for cache_file in self.cache_dir.glob("*.pkl"):
            cache_file.unlink()
        self.logger.info("缓存已清空")

def create_vector_store() -> VectorStore:
    """创建配置的向量存储实例"""
    config = get_config()
    return VectorStore(
        persist_directory=config.vector_store.persist_directory,
        collection_name=config.vector_store.collection_name
    )

def create_embedding_cache() -> EmbeddingCache:
    """创建嵌入缓存实例"""
    config = get_config()
    return EmbeddingCache(cache_dir=config.cache.directory)