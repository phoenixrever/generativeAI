#!/usr/bin/env python3
"""
OllamaClient 嵌入模式演示脚本

演示 OllamaClient 的两种嵌入模式：
1. direct: 直接调用 Ollama API
2. langchain: 使用 LangChain OllamaEmbeddings
"""

import sys
import os

from realworld.src.rag_engine import OllamaClient

def demo_embedding_modes():
    """演示两种嵌入模式"""

    print("=== OllamaClient 嵌入模式演示 ===\n")

    # 测试文本
    test_text = "机器学习是人工智能的重要分支。"

    # 1. 直接模式
    print("1. 直接 API 调用模式:")
    try:
        client_direct = OllamaClient(embedding_mode="direct")
        print(f"   模式: {client_direct.embedding_mode}")
        print(f"   LangChain 可用: {client_direct.langchain_embedder is not None}")

        # 注意：这里不会实际调用 API，因为没有运行 Ollama 服务
        # 但可以检查初始化是否正确
        print("   ✓ 客户端初始化成功")

    except Exception as e:
        print(f"   ✗ 初始化失败: {e}")

    print()

    # 2. LangChain 模式
    print("2. LangChain 嵌入模式:")
    try:
        client_langchain = OllamaClient(embedding_mode="langchain")
        print(f"   模式: {client_langchain.embedding_mode}")
        print(f"   LangChain 可用: {client_langchain.langchain_embedder is not None}")

        if client_langchain.langchain_embedder is None:
            print("   ⚠ LangChain 不可用，已回退到直接模式")
        else:
            print("   ✓ LangChain 嵌入器初始化成功")

    except Exception as e:
        print(f"   ✗ 初始化失败: {e}")

    print()

    # 3. 默认模式（直接模式）
    print("3. 默认模式（不指定 embedding_mode）:")
    try:
        client_default = OllamaClient()
        print(f"   模式: {client_default.embedding_mode}")
        print("   ✓ 使用默认直接模式")

    except Exception as e:
        print(f"   ✗ 初始化失败: {e}")

    print("\n=== 演示完成 ===")
    print("\n注意：要实际测试嵌入生成，需要运行 Ollama 服务。")
    print("可以通过以下方式测试：")
    print("1. 启动 Ollama 服务: ollama serve")
    print("2. 拉取嵌入模型: ollama pull bge-m3")
    print("3. 运行实际的嵌入生成测试")

if __name__ == "__main__":
    demo_embedding_modes()