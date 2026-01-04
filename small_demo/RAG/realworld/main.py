"""
RAG 系统主入口 (RAG System Main Entry)

这个模块是应用程序的主入口点，提供简化的接口来使用 RAG 系统。

# 下载推荐模型
ollama pull bge-m3          # 嵌入模型
ollama pull qwen2.5:7b      # 生成模型

# realworld 工程
cd realworld
python cli.py add ./documents    # 添加文档
python cli.py query "您的问题"   # 查询
"""

import sys
from pathlib import Path

# 添加当前目录到 Python 路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from config import init_config
from rag_engine import create_rag_engine
import logger

def main():
    """主函数 - 演示 RAG 系统的基本用法"""
    print("🚀 启动 RAG 系统...")

    # 初始化配置
    init_config()

    # 创建 RAG 引擎
    engine = create_rag_engine()

    # 显示系统状态
    print("📊 检查系统状态...")
    stats = engine.get_stats()
    print(f"   文档数量: {stats['document_count']}")
    print(f"   Ollama 状态: {'✅ 正常' if stats['ollama_health'] else '❌ 异常'}")
    print(f"   可用模型: {', '.join(stats['available_models'])}")

    if not stats['ollama_health']:
        print("❌ Ollama 服务不可用，请确保 Ollama 已启动")
        return

    # 示例：添加文档
    print("\n📁 添加示例文档...")
    # 这里可以添加实际的文档路径
    # engine.add_documents(["./documents"])

    # 示例：执行查询
    print("\n🤔 执行示例查询...")
    question = "什么是机器学习？"
    result = engine.query(question)

    print(f"问题: {result['question']}")
    print(f"回答: {result['answer']}")
    print(".2f"
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 用户中断，程序退出")
    except Exception as e:
        print(f"❌ 程序运行出错: {e}")
        sys.exit(1)