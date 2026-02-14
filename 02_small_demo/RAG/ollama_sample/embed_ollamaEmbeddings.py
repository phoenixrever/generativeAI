"""
嵌入和向量数据库模块 (Embedding and Vector Database Module)

功能：使用 Ollama 生成日文/中文语义向量，并持久化存储到 ChromaDB。
模型：默认使用 bge-m3 (支持多语言，上下文窗口 8192)。


ChromaDB 的设计是支持“一次存一堆”的，所以即便你只存一个，也要包一层：
    ids: ["id1"]
    documents: ["内容1"]
    embeddings: [[0.1, 0.2, ...]] （注意这是列表套列表）
"""

import chromadb
import my_chunk as chunk_module  # 确保文件名已改为 my_chunk.py
from langchain_ollama import OllamaEmbeddings
from pathlib import Path

# --- 1. 环境与路径配置 ---

# 获取当前脚本所在目录，并在其下创建 db 文件夹
current_dir: Path = Path(__file__).resolve().parent
db_path: Path = current_dir / "db"
db_path.mkdir(exist_ok=True) # 自动创建 db 文件夹，如果已存在则跳过

# 初始化 LangChain 提供的 Ollama 嵌入类 (它会自动调用本地 11434 端口)
# 这样做就不需要自己写 requests.post 了，更优雅
embedder = OllamaEmbeddings(model="bge-m3")

# --- 2. ChromaDB 初始化 ---

# 这里的路径指向 db 文件夹下的 chroma.db 子目录
chromadb_client: chromadb.ClientAPI = chromadb.PersistentClient(path=str(db_path / "chroma.db"))

def get_embedding(text: str) -> list[float]:
    """
    通过 LangChain 封装调用 Ollama 生成单个文本的向量。
    """
    try:
        return embedder.embed_query(text)
    except Exception as e:
        raise Exception(f"生成向量失败，请检查 Ollama 是否启动: {e}")
    

#循环单个文件 感觉不太好的样子
def add_document_to_db() -> None:
    """
    读取文本块，生成向量并存入数据库。
    """
    print("🚀 正在启动向量数据库创建程序...")
    collection : chromadb.Collection =delete_create_collection()
    
    # 这里的 chunks 应该是一个字符串数组，例如 ["第一段文字", "第二段文字", ...]
    chunks: list[str] = chunk_module.get_chunks()
    
    if not chunks:
        print("❌ 未获取到任何文本块，请检查 my_chunk.py")
        return

    for idx, c in enumerate(chunks):
        print(f"📦 处理进度 {idx+1}/{len(chunks)}: {c[:30]}...")
        
        # 获取当前块的向量 (bge-m3 返回的是 1024 维列表)
        vector: list[float] = get_embedding(c)
        
        
        # upsert 是 Update（更新） + Insert（插入） 的缩写。 它的逻辑如下：
        #     如果 ID 已存在：它会用新的 document 和 embedding 替换（覆盖） 掉旧的内容。
        #     如果 ID 不存在：它会新增一条记录。      
          
        # 存入 ChromaDB
        # 注意：即便 c 是字符串，也要写成 [c] 以符合 API 的批量输入要求
        collection.upsert(
            ids=[f"chunk_{idx}"],      # ID 必须是字符串列表
            documents=[c],             # 文档必须是字符串列表
            embeddings=[vector]        # 向量必须是嵌套列表 [[...]]
        )
        
    print("✅ 向量数据库已成功更新并持久化存储。")



def add_documents_to_db() -> None:
    """
    【高性能版】一次性读取所有块并批量存入数据库。
    """
    print("🚀 正在批量处理向量数据库...")
    collection : chromadb.Collection =delete_create_collection()   

    # 1. 获取所有块 (假设这是一个列表: ["内容1", "内容2", ...])
    chunks: list[str] = chunk_module.get_chunks()
    
    if not chunks:
        return

    # 2. 【关键】调用批量生成向量接口 (一次性把整个数组传进去)
    # 这比在循环里一个一个 get_embedding 快得多！
    all_embeddings: list[list[float]] = embedder.embed_documents(chunks)
    
    # 3. 【关键】生成 ID 列表 (例如: ["chunk_0", "chunk_1", ...])
    all_ids: list[str] = [f"chunk_{i}" for i in range(len(chunks))]
    
    # 4. 一次性写入数据库
    # 这里不需要加方括号了，因为 chunks, all_embeddings, all_ids 本身就是列表
    collection.upsert(
        ids=all_ids,
        documents=chunks,
        embeddings=all_embeddings
    )
    
    print(f"✅ 成功一次性存入 {len(chunks)} 条文档片段！")



def query_db(question: str, n_results: int = 5) -> list[str]:
    """
    搜索最相关的文本块。
    """
    print(f"🔍 正在查询: {question}")
    collection : chromadb.Collection = chromadb_client.get_or_create_collection("japanese_docs_ollama")
    
    # 1. 先把问题转换成向量
    question_vector: list[float] = get_embedding(question)
    
    # 2. 在数据库中检索
    result = collection.query(
        query_embeddings=[question_vector], # 注意嵌套
        n_results=n_results
    )
    
    # result['documents'] 的结构是 [[doc1, doc2, ...]]
    if result["documents"] and len(result["documents"]) > 0:
        return result["documents"][0]
    return []



def delete_create_collection()  -> chromadb.Collection:
    """
    获取或创建 ChromaDB 集合 (Collection)。
    """
    # 获取所有现有的 ID 并删除，或者直接删除整个 Collection
    try:
        # 简单的做法：如果存在，先删掉这个集合再重建
        chromadb_client.delete_collection("japanese_docs_ollama")
    except:
        pass
    # 创建或获取集合。注意：如果从 nomic 换到 bge-m3，建议改个名字或删除旧 db 文件夹
    return  chromadb_client.get_or_create_collection("japanese_docs_ollama")

# --- 3. 测试运行 ---

if __name__ == '__main__':
    # 1. 验证模型和向量长度
    print("--- 正在测试 BGE-M3 模型 ---")
    test_vec: list[float] = get_embedding("こんにちは")
    print(f"向量维度: {len(test_vec)}") # 应该输出 1024

    # 2. 创建/更新数据库
    # add_document_to_db()

    # 3. 执行一次检索测试
    question = "令狐冲领悟了什么魔法？"
    results: list[str] = query_db(question)
    
    print("\n--- 检索到的相关片段 ---")
    for i, res in enumerate(results):
        print(f"[{i+1}] {res[:150]}...\n")