#!/usr/bin/env python3
"""
嵌入器演示脚本

演示如何使用不同的嵌入器：
1. OllamaDirectEmbedder - 直接调用 Ollama API
2. OllamaLangchainEmbedder - 使用 LangChain OllamaEmbeddings
3. OnlineModelEmbedder - 线上大模型 (待实现)
"""

import sys
import os

from realworld.src.embedders import create_embedder, OllamaDirectEmbedder
from realworld.src.rag_engine import RAGEngine

def demo_embedders():
    """演示不同的嵌入器"""

    print("=== 嵌入器演示 ===\n")

    # 测试文本
    test_text = "机器学习是人工智能的重要分支。"

    # 1. OllamaDirectEmbedder
    print("1. OllamaDirectEmbedder (直接 API 调用):")
    try:
        embedder_direct = create_embedder("ollama_direct")
        print(f"   嵌入器类型: {type(embedder_direct).__name__}")
        print(f"   健康状态: {embedder_direct.check_health()}")

        # 注意：实际嵌入生成需要运行 Ollama 服务
        print("   ✓ 嵌入器创建成功")

    except Exception as e:
        print(f"   ✗ 创建失败: {e}")

    print()

    # 2. OllamaLangchainEmbedder
    print("2. OllamaLangchainEmbedder (LangChain):")
    try:
        embedder_langchain = create_embedder("ollama_langchain")
        print(f"   嵌入器类型: {type(embedder_langchain).__name__}")
        print(f"   健康状态: {embedder_langchain.check_health()}")
        print("   ✓ LangChain 嵌入器创建成功")

    except Exception as e:
        print(f"   ✗ 创建失败: {e}")
        print("     原因: langchain-ollama 未安装或 Ollama 服务不可用")

    print()

    # 3. OnlineModelEmbedder (Gemini)
    print("3. OnlineModelEmbedder (Gemini):")
    try:
        # 注意：需要有效的 Gemini API key
        gemini_embedder = create_embedder("online", api_key="fake_key_for_demo")
        print(f"   嵌入器类型: {type(gemini_embedder).__name__}")
        print("   ⚠ 需要有效的 Gemini API key 才能使用")

    except ImportError as e:
        print(f"   ✗ 依赖未安装: {e}")
        print("     请运行: pip install google-generativeai")
    except Exception as e:
        print(f"   ✗ 创建失败: {e}")

    print()

    # 4. 在 RAG 引擎中使用不同的嵌入器
    print("4. 在 RAG 引擎中使用不同的嵌入器:")

    # 使用直接嵌入器
    print("   创建 RAG 引擎 (直接嵌入器)...")
    try:
        engine_direct = RAGEngine(embedder_type="ollama_direct")
        print("   ✓ 直接嵌入器 RAG 引擎创建成功")
    except Exception as e:
        print(f"   ✗ 创建失败: {e}")

    # 使用 LangChain 嵌入器
    print("   创建 RAG 引擎 (LangChain 嵌入器)...")
    try:
        engine_langchain = RAGEngine(embedder_type="ollama_langchain")
        print("   ✓ LangChain 嵌入器 RAG 引擎创建成功")
    except Exception as e:
        print(f"   ✗ 创建失败: {e}")

    # 使用 Gemini 嵌入器
    print("   创建 RAG 引擎 (Gemini 嵌入器)...")
    try:
        engine_gemini = RAGEngine(
            embedder_type="online",
            embedder_kwargs={"api_key": "fake_key_for_demo"}
        )
        print("   ⚠ Gemini 嵌入器 RAG 引擎创建成功 (需要有效 API key)")
    except ImportError as e:
        print(f"   ✗ 依赖未安装: {e}")
    except Exception as e:
        print(f"   ✗ 创建失败: {e}")

    print("\n=== 演示完成 ===")
    print("\n使用说明：")
    print("1. 安装 langchain-ollama: pip install langchain-ollama")
    print("2. 启动 Ollama 服务: ollama serve")
    print("3. 拉取嵌入模型: ollama pull bge-m3")
    print("4. 安装 Gemini 支持: pip install google-generativeai")
    print("5. 获取 Gemini API key: https://makersuite.google.com/app/apikey")
    print("6. 运行实际的嵌入生成测试")

if __name__ == "__main__":
    demo_embedders()