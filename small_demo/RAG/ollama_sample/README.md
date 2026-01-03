使用 Ollama 进行文本嵌入（Embedding）是构建本地 RAG（检索增强生成）系统的核心环节。以下是全方位的总结：

### 1. 核心流程

1. **拉取模型** ：在终端执行 `ollama pull <模型名>`（如 `bge-m3`）。
2. **发送请求** ：通过 HTTP POST 请求访问 `/api/embeddings` 接口。
3. **获取向量** ：接口返回一个高维浮点数列表（Vector），代表文本的语义坐标。
4. **存入数据库** ：将这些向量存入 ChromaDB 或 FAISS 等向量数据库。

---

### 2. 主流模型对比（针对你的日文/中文需求）

| **模型名称**            | **擅长语言**    | **上下文窗口 (Token)** | **推荐理由**                                            |
| ----------------------- | --------------- | ---------------------- | ------------------------------------------------------- |
| **`bge-m3`**            | **中/日/韩/英** | **8192**               | **全能王** ，对日文语义理解极佳，目前 Ollama 上的首选。 |
| **`nomic-embed-text`**  | 英/通用         | 8192                   | 速度极快，但在处理日文/中文细微差别时不如 BGE。         |
| **`mxbai-embed-large`** | 英语为主        | 512                    | 英文表现顶级，但上下文窗口较小。                        |

---

### 3. 技术限制与注意事项

- **维度固定** ：每个模型的维度是固定的（例如 `bge-m3` 是 **1024** 维，`nomic` 是 **768** 维）。在 ChromaDB 中初始化时，维度必须匹配。
- **截断机制** ：如果输入的文本超过了模型的 **Token 限制** （如 8192），Ollama 会自动截断。为了效果更好，建议在代码层手动将长文切分成小块（Chunking）。
- **不可混用** ：数据库中存的向量和查询时用的向量 **必须来自同一个模型** 。换模型 = 必须删库重建。
- **显存占用** ：嵌入模型通常比聊天模型小很多，`bge-m3` 约占用 **2-3GB** 显存，可以和 `qwen2.5` 等聊天模型共存。

---

### 4. 代码实现方案

```
ollama pull bge-m3
pip install chromadb requests langchain-ollama
```

你可以访问 `http://localhost:11434`，如果显示 "Ollama is running"，说明环境正常。

```
# 启动服务
ollama serve
```

#### 方案 A：原生请求（无需额外库）

**Python**

```
import requests

def embed_text(text, model="bge-m3"):
    res = requests.post(
        "http://localhost:11434/api/embeddings",
        json={"model": model, "prompt": text}
    )
    return res.json()["embedding"]
```

#### 方案 B：LangChain 集成（推荐用于复杂项目）

**Python**

```
from langchain_ollama import OllamaEmbeddings

embedder = OllamaEmbeddings(model="bge-m3")
# 直接嵌入文档
vector = embedder.embed_query("こんにちわ、元気ですか？")
```

---

### 5. 常见坑点排查

- **404 错误** ：确保 Ollama 服务已启动，且 `ollama list` 里能看到该模型。
- **速度慢** ：如果是 CPU 运行，嵌入大批量文档会很慢。建议分批次（Batch）处理，或确保 GPU 驱动已正确安装。
- **SQLite 版本** ：如果你用 ChromaDB 配合 Ollama，Linux 用户常遇到 `pysqlite3` 版本过低问题，记得安装 `pysqlite3-binary`。

---

**既然你已经安装了 ChromaDB 并准备处理日文，需要我帮你写一个自动将日文长文本切分并存入 ChromaDB 的完整脚本吗？**
