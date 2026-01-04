# 企业级 RAG 系统 (Enterprise RAG System)

一个完整的企业级检索增强生成 (RAG) 系统，使用本地 Ollama 服务构建。支持多种文档格式、向量搜索、缓存机制和命令行操作。

## 🚀 核心特性

- **多格式文档支持**: TXT, MD, PDF, DOCX
- **本地 LLM 集成**: 使用 Ollama 支持多种开源模型
- **高效向量搜索**: ChromaDB 提供快速相似度检索
- **智能文本分割**: 支持重叠分块和元数据保留
- **缓存机制**: 嵌入向量缓存提升性能
- **命令行工具**: 完整的 CLI 接口
- **配置管理**: 灵活的配置系统
- **日志记录**: 结构化日志和错误处理
- **单元测试**: 完整的测试覆盖

## 📋 系统要求

- Python 3.8+
- Ollama (已安装并运行)
- 磁盘空间: 至少 2GB (用于模型和向量存储)

## 🛠️ 安装步骤

### 1. 安装 Ollama

```bash
# 下载并安装 Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 启动 Ollama 服务
ollama serve
```

### 2. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 3. 下载模型

```bash
# 嵌入模型 (推荐)
ollama pull bge-m3

# 生成模型 (根据需要选择)
ollama pull qwen2.5:7b      # 通义千问 (推荐)
ollama pull qwen2.5:14b     # 通义千问更大模型
ollama pull qwen2.5:32b     # 通义千问最大模型
```

## ⚙️ 配置

系统支持多种配置方式：

### 环境变量配置

```bash
export OLLAMA_BASE_URL="http://localhost:11434"
export OLLAMA_EMBEDDING_MODEL="bge-m3"
export OLLAMA_GENERATION_MODEL="qwen2.5:7b"
export LOG_LEVEL="INFO"
```

### 配置文件

创建 `config.json`:

```json
{
  "ollama": {
    "base_url": "http://localhost:11434",
    "embedding_model": "bge-m3",
    "generation_model": "qwen2.5:7b"
  },
  "vector_store": {
    "persist_directory": "./db/chroma",
    "collection_name": "documents"
  },
  "logging": {
    "level": "INFO",
    "file_path": "logs/rag_app.log"
  }
}
```

## 📖 使用指南

### 命令行工具

```bash
# 查看帮助
python cli.py --help

# 添加文档
python cli.py add /path/to/documents --recursive

# 查询问题
python cli.py query "什么是机器学习？" --n-results 3

# 查看统计信息
python cli.py stats

# 清空知识库
python cli.py clear --yes
```

### Python API

```python
from rag_engine import create_rag_engine

# 创建引擎
engine = create_rag_engine()

# 添加文档
engine.add_documents(["./documents"])

# 执行查询
result = engine.query("你的问题")
print(result["answer"])
```

## 📁 项目结构

```
realworld/
├── config.py              # 配置管理
├── logger.py              # 日志系统
├── document_processor.py  # 文档处理
├── vector_store.py        # 向量存储
├── rag_engine.py          # RAG 引擎核心
├── cli.py                 # 命令行接口
├── main.py                # 主入口
├── requirements.txt       # 依赖列表
├── README.md             # 文档
└── tests/
    └── test_rag.py       # 单元测试
```

## 🔧 高级配置

### 文档处理配置

```python
# 在 config.json 中自定义
{
  "document": {
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "supported_extensions": [".txt", ".md", ".pdf", ".docx"]
  }
}
```

### 向量搜索配置

```python
{
  "vector_store": {
    "similarity_threshold": 0.7,
    "max_results": 5
  }
}
```

### 缓存配置

```python
{
  "cache": {
    "enabled": true,
    "directory": "./cache",
    "ttl": 3600
  }
}
```

## 🧪 测试

运行单元测试：

```bash
python -m pytest tests/ -v
```

或直接运行：

```bash
python tests/test_rag.py
```

## 📊 性能优化

1. **模型选择**: 使用更小的模型以提高响应速度
2. **缓存**: 启用嵌入缓存以避免重复计算
3. **批处理**: 大量文档时使用批处理添加
4. **索引优化**: 定期清理无用文档

## 🔍 故障排除

### Ollama 连接问题

```bash
# 检查 Ollama 状态
curl http://localhost:11434/api/tags

# 重启 Ollama
ollama serve
```

### 内存不足

- 使用更小的模型
- 减少 `chunk_size`
- 启用缓存清理

### 文档处理失败

- 检查文件编码 (推荐 UTF-8)
- 验证文件格式支持
- 查看日志文件获取详细错误

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 📞 支持

如有问题，请查看日志文件或提交 Issue。
