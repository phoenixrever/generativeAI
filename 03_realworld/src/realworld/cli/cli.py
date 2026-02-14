"""
命令行接口模块 (Command Line Interface Module)

这个模块提供命令行界面，用于与 RAG 系统交互。
支持文档添加、查询、管理等操作。
"""

import argparse
import sys
import json
import os
from pathlib import Path
from typing import List, Optional
import logging

from ..config import get_config, init_config
from ..logger import initialize_logging
from ..rag_engine import create_rag_engine, RAGEngine

def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="RAG 系统命令行工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 添加文档
  python cli.py add /path/to/documents --recursive

  # 查询问题
  python cli.py query "什么是机器学习？"

  # 查看统计信息
  python cli.py stats

  # 清空数据库
  python cli.py clear --yes
        """,
        add_help=False  # 禁用默认的 -h/--help 选项
    )

    # 全局选项
    parser.add_argument(
        '--config',
        type=str,
        help='配置文件路径'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='详细输出（DEBUG 级别）'
    )

    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='安静模式（禁用日志输出）'
    )

    parser.add_argument(
        '--no-log',
        action='store_true',
        help='禁用日志输出（同 --quiet）'
    )

    parser.add_argument(
        '--no-file',
        action='store_true',
        help='仅输出到控制台，不保存日志文件'
    )

    parser.add_argument(
        '--help',
        action='store_true',
        help='显示帮助信息'
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # 添加文档命令
    add_parser = subparsers.add_parser('add', help='添加文档到知识库')
    add_parser.add_argument(
        'paths',
        nargs='+',
        help='文件或目录路径'
    )
    add_parser.add_argument(
        '--no-recursive',
        action='store_true',
        help='不递归处理子目录'
    )

    # 查询命令
    query_parser = subparsers.add_parser('query', help='查询知识库')
    query_parser.add_argument(
        'question',
        help='查询问题'
    )
    query_parser.add_argument(
        '--n-results',
        type=int,
        default=5,
        help='返回结果数量 (默认: 5)'
    )
    query_parser.add_argument(
        '--format',
        choices=['text', 'json'],
        default='text',
        help='输出格式 (默认: text)'
    )

    # 统计信息命令
    subparsers.add_parser('stats', help='显示系统统计信息')

    # 清空数据库命令
    clear_parser = subparsers.add_parser('clear', help='清空知识库')
    clear_parser.add_argument(
        '--yes',
        action='store_true',
        help='跳过确认提示'
    )

    return parser

class RAGCLI:
    """RAG 命令行接口"""

    def __init__(self):
        self.engine: Optional[RAGEngine] = None
        self.logger = logging.getLogger(__name__)  # 使用标准logging

    def initialize_engine(self) -> None:
        """初始化 RAG 引擎"""
        try:
            self.engine = create_rag_engine()
            self.logger.info("RAG 引擎初始化成功")
        except Exception as e:
            self.logger.error(f"RAG 引擎初始化失败: {e}")
            sys.exit(1)
            self.logger.info("RAG 引擎初始化成功")
        except Exception as e:
            self.logger.error(f"RAG 引擎初始化失败: {e}")
            sys.exit(1)

    def add_documents(self, paths: List[str], recursive: bool = True) -> None:
        """
        添加文档命令

        参数:
            paths: 文件或目录路径列表
            recursive: 是否递归处理目录
        """
        if not self.engine:
            self.initialize_engine()

        self.logger.info(f"添加文档: {paths}")

        try:
            added_count = self.engine.add_documents(paths, recursive=recursive)
            print(f"✅ 成功添加了 {added_count} 个文档块")

        except Exception as e:
            self.logger.error(f"添加文档失败: {e}")
            print(f"❌ 添加文档失败: {e}")
            sys.exit(1)

    def query(self, question: str, n_results: int = 5, output_format: str = "text") -> None:
        """
        查询命令

        参数:
            question: 查询问题
            n_results: 返回结果数量
            output_format: 输出格式 (text/json)
        """
        if not self.engine:
            self.initialize_engine()

        self.logger.info(f"执行查询: {question}")

        try:
            result = self.engine.query(question, n_results=n_results)

            if output_format == "json":
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                # 文本格式输出
                print(f"\n🤔 问题: {result['question']}")
                print(f"\n💡 回答: {result['answer']}")

                if result['retrieved_documents']:
                    print(f"\n📚 参考文档 ({len(result['retrieved_documents'])} 个):")
                    for i, doc in enumerate(result['retrieved_documents'], 1):
                        print(f"\n{i}. 来源: {doc['source'] or '未知'}")
                        print(f"   相似度: {doc['score']:.3f}")
                        print(f"   内容: {doc['content'][:200]}...")

                print(f"\n⏱️  查询耗时: {result['query_time']:.2f} 秒")
        except Exception as e:
            self.logger.error(f"查询失败: {e}")
            print(f"❌ 查询失败: {e}")
            sys.exit(1)

    def stats(self) -> None:
        """显示统计信息"""
        if not self.engine:
            self.initialize_engine()

        try:
            stats = self.engine.get_stats()

            print("📊 RAG 系统统计信息:")
            print(f"   文档数量: {stats['document_count']}")
            print(f"   Ollama 健康状态: {'✅ 正常' if stats['ollama_health'] else '❌ 异常'}")
            print(f"   可用模型: {', '.join(stats['available_models'])}")
            print(f"   向量存储: {stats['vector_store_info']['name']}")
            print(f"   存储路径: {stats['vector_store_info']['persist_directory']}")

        except Exception as e:
            self.logger.error(f"获取统计信息失败: {e}")
            print(f"❌ 获取统计信息失败: {e}")
            sys.exit(1)

    def clear_database(self, confirm: bool = False) -> None:
        """
        清空数据库命令

        参数:
            confirm: 是否跳过确认提示
        """
        if not confirm:
            response = input("⚠️  这将删除所有文档和向量数据，确定要继续吗？(y/N): ")
            if response.lower() not in ['y', 'yes']:
                print("操作已取消")
                return

        if not self.engine:
            self.initialize_engine()

        try:
            success = self.engine.vector_store.clear_collection()
            if success:
                print("✅ 数据库已清空")
            else:
                print("❌ 清空数据库失败")
                sys.exit(1)

        except Exception as e:
            self.logger.error(f"清空数据库失败: {e}")
            print(f"❌ 清空数据库失败: {e}")
            sys.exit(1)

def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()

    # 如果是 help 请求，显示帮助
    if getattr(args, 'help', False):
        try:
            init_config(getattr(args, 'config', None))
            initialize_logging(args, get_config())
        except:
            pass
        parser.print_help()
        return

    # 初始化配置
    try:
        init_config(getattr(args, 'config', None))
    except Exception as e:
        logging.basicConfig(level=logging.INFO)
        logging.getLogger(__name__).warning(f"配置初始化失败: {e}")

    # 初始化日志（一行搞定）
    initialize_logging(args, get_config())

    # 初始化 CLI
    cli = RAGCLI()

    # 执行命令
    try:
        if args.command == 'add':
            recursive = not getattr(args, 'no_recursive', False)
            cli.add_documents(args.paths, recursive=recursive)

        elif args.command == 'query':
            cli.query(
                question=args.question,
                n_results=args.n_results,
                output_format=args.format
            )

        elif args.command == 'stats':
            cli.stats()

        elif args.command == 'clear':
            cli.clear_database(confirm=args.yes)

    except KeyboardInterrupt:
        print("\n⚠️  操作被用户中断")
        sys.exit(1)
    except Exception as e:
        logging.getLogger(__name__).error(f"未预期的错误: {e}")
        print(f"❌ 发生未预期的错误: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
