"""
测试模块 (Test Module)

这个模块包含 RAG 系统的单元测试和集成测试。
"""

import unittest
from unittest.mock import Mock, patch
import tempfile
from pathlib import Path
import json

from config import AppConfig, get_config
from document_processor import Document, TextDocumentProcessor, TextSplitter
from vector_store import VectorStore
from rag_engine import OllamaClient, RAGEngine

class TestConfig(unittest.TestCase):
    """配置模块测试"""

    def test_config_validation(self):
        """测试配置验证"""
        config = AppConfig()

        # 有效的配置
        errors = config.validate()
        self.assertEqual(len(errors), 0)

        # 无效的相似度阈值
        config.vector_store.similarity_threshold = 1.5
        errors = config.validate()
        self.assertIn("相似度阈值", errors[0])

class TestDocumentProcessor(unittest.TestCase):
    """文档处理器测试"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_file = Path(self.temp_dir) / "test.txt"

    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_text_processor(self):
        """测试文本文档处理器"""
        # 创建测试文件
        test_content = "这是测试内容。\n第二行。"
        self.temp_file.write_text(test_content, encoding='utf-8')

        processor = TextDocumentProcessor()
        document = processor.process(str(self.temp_file))

        self.assertEqual(document.content, test_content)
        self.assertEqual(document.source, str(self.temp_file))
        self.assertIn('line_count', document.metadata)

    def test_text_splitter(self):
        """测试文本分割器"""
        text = "第一段。\n\n第二段。\n\n第三段。"
        splitter = TextSplitter(chunk_size=10, chunk_overlap=5)

        chunks = splitter.split_text(text)
        self.assertGreater(len(chunks), 1)

        # 测试重叠
        for i in range(len(chunks) - 1):
            self.assertTrue(
                chunks[i][-5:] == chunks[i + 1][:5] or
                len(chunks[i]) <= 10
            )

class TestVectorStore(unittest.TestCase):
    """向量存储测试"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.store = VectorStore(str(self.temp_dir), "test_collection")

    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_add_and_search(self):
        """测试添加和搜索文档"""
        # 创建测试文档
        docs = [
            Document("机器学习是人工智能的重要分支。", {"source": "test1"}),
            Document("深度学习是机器学习的一种方法。", {"source": "test2"})
        ]

        # 添加文档（这里需要模拟嵌入向量）
        for doc in docs:
            doc.metadata['embedding'] = [0.1, 0.2, 0.3]  # 模拟嵌入向量

        added = self.store.add_documents(docs)
        self.assertEqual(added, 2)

        # 验证文档数量
        count = self.store.get_document_count()
        self.assertEqual(count, 2)

class TestOllamaClient(unittest.TestCase):
    """Ollama 客户端测试"""

    def setUp(self):
        """测试前准备"""
        self.client = OllamaClient("http://invalid-url:11434")  # 使用无效URL进行测试

    @patch('requests.post')
    def test_generate_embedding_error(self, mock_post):
        """测试嵌入生成错误处理"""
        mock_post.side_effect = Exception("Connection failed")

        with self.assertRaises(Exception):
            self.client.generate_embedding("test text", "test-model")

    @patch('requests.post')
    def test_generate_text_success(self, mock_post):
        """测试文本生成成功"""
        mock_response = Mock()
        mock_response.json.return_value = {"response": "生成的文本"}
        mock_post.return_value = mock_response

        result = self.client.generate_text("test prompt", "test-model")
        self.assertEqual(result, "生成的文本")

class TestRAGEngine(unittest.TestCase):
    """RAG 引擎测试"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()

        # 模拟组件
        self.mock_ollama = Mock()
        self.mock_vector_store = Mock()
        self.mock_cache = Mock()

        self.engine = RAGEngine(
            ollama_client=self.mock_ollama,
            vector_store=self.mock_vector_store,
            embedding_cache=self.mock_cache
        )

    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_query_workflow(self):
        """测试查询工作流程"""
        # 设置模拟返回值
        self.mock_ollama.generate_embedding.return_value = [0.1, 0.2, 0.3]
        self.mock_vector_store.search_similar.return_value = {
            'documents': [['相关文档内容']],
            'metadatas': [[{'source': 'test.txt'}]],
            'distances': [[0.1]]
        }
        self.mock_ollama.generate_text.return_value = "这是生成的回答"

        result = self.engine.query("测试问题")

        self.assertIn('question', result)
        self.assertIn('answer', result)
        self.assertIn('retrieved_documents', result)
        self.assertEqual(result['question'], "测试问题")
        self.assertEqual(result['answer'], "这是生成的回答")

if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)