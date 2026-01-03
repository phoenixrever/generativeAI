"""
未运行测试 
嵌入和向量数据库模块 (Embedding and Vector Database Module)

这个模块使用本地的 Ollama 服务来生成文本嵌入，并使用 ChromaDB 存储和检索向量。
需要确保 Ollama 服务正在运行，并且已安装 nomic-embed-text 模型用于嵌入。

# 安装模型
ollama pull bge-m3  # 嵌入模型

ollama list  # 查看已安装模型
# 启动服务
ollama serve

"""

import requests  # 用于调用 Ollama API
import chromadb
import my_chunk as chunk_module  # 导入文本分割模块
from pathlib import Path

# Ollama 服务配置
OLLAMA_BASE_URL = "http://localhost:11434"  # Ollama 默认地址
EMBEDDING_MODEL = "bge-m3"  # 用于嵌入的模型，需要先在 Ollama 中安装

# ChromaDB 配置
# 1. 获取当前代码文件 (.py) 的绝对路径
current_file = Path(__file__).resolve()
# 2. 获取这个文件所在的文件夹目录
parent_dir = current_file.parent
# tool 的工作目录
base_dir = parent_dir / "db"
chromadb_client = chromadb.PersistentClient("base_dir/chroma.db")
chromadb_collection = chromadb_client.get_or_create_collection("linghuchong_ollama")

def get_embedding(text: str) -> list[float]:
    """
    使用 Ollama 生成文本的嵌入向量。

    参数:
        text (str): 要嵌入的文本。

    返回:
        list[float]: 嵌入向量。

    异常:
        如果 Ollama 服务不可用或模型未安装，会抛出异常。
    """
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/embeddings",
            json={
                "model": EMBEDDING_MODEL,
                "prompt": text
            }
        )
        response.raise_for_status()  # 检查 HTTP 错误
        data = response.json()
        return data["embedding"]
    except requests.exceptions.RequestException as e:
        raise Exception(f"无法连接到 Ollama 服务: {e}")

def create_db() -> None:
    """
    创建向量数据库。

    这个函数读取所有文本块，生成嵌入，并存储到 ChromaDB 中。
    如果数据库已存在，会覆盖。
    """
    print("正在创建向量数据库...")
    chunks = chunk_module.get_chunks()
    for idx, c in enumerate(chunks):
        print(f"处理块 {idx+1}/{len(chunks)}: {c[:50]}...")  # 显示前50字符
        embedding = get_embedding(c)
        chromadb_collection.upsert(
            ids=[str(idx)],  # 注意这里加了方括号
            documents=[c],   # 同样，documents 通常也建议传列表
            embeddings=embedding
        )
    print("向量数据库创建完成！")

def query_db(question: str, n_results: int = 5) -> list[str]:
    """
    查询向量数据库，找到最相关的文本块。

    参数:
        question (str): 查询问题。
        n_results (int): 返回的结果数量，默认5。

    返回:
        list[str]: 最相关的文本块列表。
    """
    question_embedding = get_embedding(question)
    result = chromadb_collection.query(
        query_embeddings=question_embedding,
        n_results=n_results
    )
    if result["documents"]:
        return result["documents"][0]
    else:
        return []

if __name__ == '__main__':
    """
    主函数：用于测试嵌入功能。
    运行此脚本时，会创建数据库并进行一次查询测试。
    """
    print("测试嵌入功能...")
    # 测试嵌入
    test_text = "令狐冲领悟了什么魔法？"
    embedding = get_embedding(test_text)
    print(f"嵌入向量长度: {len(embedding)}")

    # 创建数据库
    create_db()

    # 测试查询
    results = query_db(test_text)
    print(f"查询结果数量: {len(results)}")
    for i, res in enumerate(results):
        print(f"结果 {i+1}: {res[:100]}...")