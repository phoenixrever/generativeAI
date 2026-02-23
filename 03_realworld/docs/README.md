# RealWorld RAG 项目详细学习指南

本文档整合了项目的所有文档资源，旨在为您提供从入门到精通的完整指南。

---

## 📚 目录

1.  [项目概述](#1-项目概述)
2.  [快速开始](#2-快速开始)
3.  [工程结构详解](#3-工程结构详解)
4.  [配置详解 (Config)](#4-配置详解-config)
5.  [依赖管理 (pyproject.toml)](#5-依赖管理-pyprojecttoml)
6.  [日志系统详解](#6-日志系统详解)
7.  [API 与使用指南](#7-api-与使用指南)

---

## 1. 项目概述

**RealWorld RAG** 是一个完整的企业级检索增强生成 (RAG) 系统，使用本地 Ollama 服务构建。它支持多种文档格式、向量搜索、缓存机制和命令行操作。

### 核心特性
-   **多格式文档支持**: TXT, MD, PDF, DOCX
-   **本地 LLM 集成**: 使用 Ollama 支持多种开源模型
-   **高效向量搜索**: ChromaDB 提供快速相似度检索
-   **智能文本分割**: 支持重叠分块和元数据保留
-   **缓存机制**: 嵌入向量缓存提升性能
-   **命令行工具**: 完整的 CLI 接口

---

## 2. 快速开始

### 环境准备
-   **Python 3.8+**
-   **Ollama**: 必须安装并启动 (`ollama serve`)

### 安装步骤
在项目根目录下运行：

```bash
# 以“可编辑模式”安装（推荐开发使用）
pip install -e .
```

### 验证安装
```bash
realworld-cli --help
```

---

## 3. 工程结构详解

本项目遵循现代 Python 打包标准 (src-layout)。

### 目录树

```text
realworld/
├── pyproject.toml        # 项目配置和依赖管理 (核心)
├── src/                  # 源代码目录
│   └── realworld/        # 主包
│       ├── rag_engine.py # RAG 引擎核心 (指挥官)
│       ├── embedders.py  # 嵌入器 (翻译官)
│       ├── vector_store.py # 向量存储 (记忆库)
│       ├── document_processor.py # 文档处理 (厨师)
│       ├── config.py     # 配置管理 (控制台)
│       ├── logger.py     # 日志配置
│       └── cli/          # 命令行工具
├── data/                 # 数据文件 (文档、数据库)
├── logs/                 # 日志目录
└── docs/                 # 文档目录
```

### 核心模块说明

-   **`rag_engine.py`**: 核心调度器，连接文档处理、向量存储和 LLM 生成。
-   **`embedders.py`**: 定义了如何将文本转换为向量。支持 Ollama 直接调用或 LangChain 集成。
-   **`vector_store.py`**: 封装了 ChromaDB 的操作，负责增删改查向量数据。
-   **`document_processor.py`**: 负责读取不同格式的文件，并将其切割成适合模型处理的小块 (Chunks)。

---

## 4. 配置详解 (Config)

我们使用 `src/realworld/config.py` 进行集中式配置管理，支持 **Python Dataclass** 定义、**JSON 文件** 加载和 **环境变量** 覆盖。

### 4.1 核心配置对象

#### Ollama 配置 (`OllamaConfig`)
-   `base_url`: Ollama 服务地址，默认 `http://localhost:11434`
-   `embedding_model`: 嵌入模型，推荐 `bge-m3`
-   `generation_model`: 生成模型，推荐 `qwen2.5:7b`

#### 向量存储配置 (`VectorStoreConfig`)
-   `persist_directory`: ChromaDB 存储路径
-   `collection_name`: 集合名称
-   `similarity_threshold`: **相似度阈值** (重要)，低于此分数的检索结果将被丢弃，防止“幻觉”。

### 4.2 配置加载优先级

1.  **命令行参数** (最高优先级)
2.  **环境变量** (如 `export OLLAMA_BASE_URL=...`)
3.  **配置文件** (`config.json`)
4.  **代码默认值** (最低优先级)

### 4.3 为什么使用 `@dataclass`?
-   **类型安全**: 明确知道每个配置项的类型。
-   **自动补全**: IDE 可以智能提示配置结构。
-   **清晰分层**: 使用嵌套结构 (`config.ollama.url`) 而不是很长的扁平键名。

---

## 5. 依赖管理 (pyproject.toml)

本项目使用 `pyproject.toml` 作为唯一的项目配置文件（替代了传统的 `setup.py`）。

### 关键部分解读

-   **`[build-system]`**: 指定使用 `setuptools` 进行构建。
-   **`[project]`**: 定义项目元数据（名称、版本、作者）。
-   **`dependencies`**: 核心依赖列表 (chromadb, requests, pypdf2 等)。
-   **`[project.optional-dependencies]`**:
    -   `realworld[dev]`: 安装开发工具 (pytest, black, mypy)。
    -   `realworld[langchain]`: 安装 LangChain 支持。
-   **`[project.scripts]`**: 定义命令行入口。`realworld-cli = "realworld.cli.cli:main"` 让你可以直接在终端运行 `realworld-cli`。
-   **`[tool.setuptools.package-dir]`**: `"" = "src"` 告诉工具源码在 `src` 目录下，这是 Python 社区推荐的结构，能避免导入混淆。

---

## 6. 日志系统详解

日志系统通过 `src/realworld/logger.py` 实现，经过优化后支持更灵活的控制。

### 命令行控制
-   `--verbose` / `-v`: 开启调试模式 (DEBUG 级别)，看到所有细节。
-   `--quiet` / `-q`: 安静模式，只输出结果，不打印日志。
-   `--no-file`: 仅输出到屏幕，不写入文件。

### 日志文件
-   默认位置: `logs/rag_app.log`
-   自动轮转: 单个文件超过 10MB 会自动切割，保留最近 5 个备份。

### 代码中使用
```python
from realworld.logger import get_logger
logger = get_logger(__name__)
logger.info("这是一个普通信息")
logger.error("出错了！")
```

---

## 7. API 与使用指南

### 命令行接口 (CLI)

```bash
# 1. 添加文档
realworld-cli add ./data/documents --recursive

# 2. 搜索并问答
realworld-cli query "RAG 系统的核心组件有哪些？"

# 3. 查看系统状态（文档数量等）
realworld-cli stats

# 4. 清空知识库
realworld-cli clear
```

### Python API

```python
from realworld.rag_engine import RAGEngine

# 初始化
engine = RAGEngine()

# 添加文档
engine.add_documents(["./README.md"])

# 查询
result = engine.query("这个项目是用什么写的？")
print(result["answer"])
print(result["source_documents"]) # 查看引用来源
```

---

希望这份详细指南能帮助你全面掌握 **RealWorld RAG** 项目！
