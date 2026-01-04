#!/usr/bin/env python3
"""
Gemini 嵌入器使用示例

展示如何使用 Gemini 嵌入器进行文本嵌入生成
"""

import os
import sys

from realworld.src.embedders import OnlineModelEmbedder

def gemini_embedding_example():
    """Gemini 嵌入器使用示例"""

    print("=== Gemini 嵌入器使用示例 ===\n")

    # 注意：需要有效的 Gemini API key
    # 获取 API key: https://makersuite.google.com/app/apikey

    api_key = os.getenv("GEMINI_API_KEY")  # 从环境变量获取

    if not api_key:
        print("❌ 请设置 GEMINI_API_KEY 环境变量")
        print("获取 API key: https://makersuite.google.com/app/apikey")
        print("\n# 设置环境变量示例:")
        print("export GEMINI_API_KEY='your_api_key_here'")
        return

    try:
        # 创建 Gemini 嵌入器
        print("1. 创建 Gemini 嵌入器...")
        embedder = OnlineModelEmbedder(api_key=api_key)
        print("✅ Gemini 嵌入器创建成功")

        # 测试单个文本嵌入
        print("\n2. 生成单个文本嵌入...")
        text = "机器学习是人工智能的重要分支。"
        embedding = embedder.generate_embedding(text)
        print(f"✅ 嵌入生成成功，维度: {len(embedding)}")

        # 测试批量文本嵌入
        print("\n3. 批量生成文本嵌入...")
        texts = [
            "深度学习是机器学习的一种方法。",
            "自然语言处理是AI的重要领域。",
            "向量数据库用于存储嵌入向量。"
        ]
        embeddings = embedder.generate_embeddings(texts)
        print(f"✅ 批量嵌入生成成功，数量: {len(embeddings)}")

        # 测试健康检查
        print("\n4. 健康检查...")
        is_healthy = embedder.check_health()
        print(f"✅ 服务健康状态: {'正常' if is_healthy else '异常'}")

        print("\n=== 示例完成 ===")

    except Exception as e:
        print(f"❌ 错误: {e}")
        print("\n可能的原因:")
        print("- API key 无效")
        print("- 网络连接问题")
        print("- API 配额不足")

if __name__ == "__main__":
    gemini_embedding_example()