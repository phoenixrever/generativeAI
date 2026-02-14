"""
RAG 演示脚本 
"""

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
import embed_ollamaEmbeddings as embed  # 确保你的嵌入文件名正确

# --- 1. 配置生成模型 ---
GENERATION_MODEL = "qwen2.5:7b"  # 或者你安装的其他模型

# 初始化聊天模型 注意这不是agent 不能用system prompt
llm = ChatOllama(
    model=GENERATION_MODEL,
    temperature=0,      # RAG 通常设为 0，保证回答的稳定性
    streaming=True
)

def generate_answer(question: str, context_chunks: list[str]):
    """
    结合上下文和问题，使用 ChatOllama 实时流式生成回答。
    """
    # 1. 组装上下文字符串
    context_text = "\n\n".join([f"资料片段 {i+1}:\n{chunk}" for i, chunk in enumerate(context_chunks)])
    print(f"[DEBUG]📚 提供的上下文:\n{context_text}\n{'-'*30}")
    
    # 2. 定义系统指令
    system_instruction = (
        "你是一个专业的知识库助手。请根据提供的『上下文』内容来回答『问题』。\n"
        "规则：\n"
        "1. 如果上下文里没有答案，请直接说“根据现有资料无法回答”。\n"
        "2. 不要编造事实，保持客观简洁。\n"
        "3. 如果是日文资料，请用中文总结核心意图。\n"
    )

    # 3. 构建消息列表 (System + Human)
    messages = [
        SystemMessage(content=system_instruction),
        HumanMessage(content=f"--- 上下文 ---\n{context_text}\n\n--- 问题 ---\n{question}\n\n回答：")
    ]

    # 4. 流式调用
    try:
        print("✨ 回答结果: ", end="", flush=True)
        full_response = ""
        
        # 使用 .stream 方法
        for chunk in llm.stream(messages):
            content = chunk.content
            print(content, end="", flush=True) # 实时打印字符
            full_response += content
            
        print("\n" + "-" * 30)
        return full_response
    except Exception as e:
        raise Exception(f"ChatOllama 流式生成失败: {e}")

def main():
    question = "令狐冲领悟了什么魔法？"
    print(f"🤔 问题: {question}")

    # 检索阶段
    print("🔍 正在从数据库检索相关资料...")
    chunks = embed.query_db(question, n_results=3)

    if not chunks:
        print("⚠️ 未找到相关资料。")
        return

    # 生成阶段 (此时内部会自动流式打印)
    try:
        generate_answer(question, chunks)
    except Exception as e:
        print(f"❌ 运行出错: {e}")

if __name__ == '__main__':
    main()