# conda activate py310 ollama run qwen3:1.7b pip3 install langchain_ollama
"""
# 检查当前可用的模型列表
ollama list

# 如果你想尝试 Qwen 的最新实验版（假设叫 qwen3-preview）
ollama run qwen2.5:7b  # 目前最推荐
# 或者尝试阿里最近发布的更小、更快的 Coder 专用版本
ollama run qwen2.5-coder:7b
"""

# 核心变化：导入 Ollama 驱动
import inspect
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.tools import BaseTool

# 导入当前文件夹下的 tools 模块
import tools

def chat_loop():
    # 1. 初始化 Ollama 模型
    # model="qwen2.5:7b" 是目前本地运行工具调用最稳的模型之一
    # 如果电脑配置一般，可以换成 "qwen3:1.7b" 
    model = ChatOllama(
        model="qwen2.5:7b",
        # model="qwen3:1.7b",
        temperature=0, # 设为 0 以获得更确定性的回答
        streaming=True # 开启流式输出
    )

    # 2. 组装工具
    # langchain_tools = [tools.read_file, tools.list_files, tools.rename_file,tools.write_file]
    
    # 这一行会自动抓取 tools.py 里所有带 @tool 的函数
    langchain_tools = [
        # 结果层 (Output)：obj 数据源层 (Source)：for name, obj in inspect.getmembers(tools)  过滤器层 (Filter)：if isinstance(obj, BaseTool)
        obj for name, obj in inspect.getmembers(tools) if isinstance(obj, BaseTool)
    ]

    # 3. 设置记忆
    memory = MemorySaver()

    # 4. 创建 Agent
    system_prompt = "You are a professional Python programmer. Use the provided tools to manage files."
    agent_executor = create_agent(
        model=model, 
        tools=langchain_tools, 
        checkpointer=memory,
        system_prompt=system_prompt
    )

    # 5. 运行循环 
    config = {"configurable": {"thread_id": "local_user"}} 
    print("🚀 Ollama Agent 已启动!")

    while True:
        user_input = input("\nUser >>> ")
        if user_input.lower() in ["exit", "quit"]:
            break

        print("AI >>> ", end="", flush=True)
        
        # 这里的 token 实际上是一个 AIMessageChunk
        for token, metadata in agent_executor.stream(
            {"messages": [HumanMessage(content=user_input)]},
            config=config,
            stream_mode="messages", # 其他模式见文档
        ):
            # 根据模型不同，内容可能在 content 或 content_blocks 里
            # 检查是否有 content_blocks 模型发给你的每一个 token 碎片并不一定都带着content
            # token.content_blocks 检测content_blocks是否为空。 在 Python 中，空列表 [] 在布尔判断中被视为 False
            if hasattr(token, "content_blocks") and token.content_blocks:
                block = token.content_blocks[0]
                
                # 2. 用字典的方式访问 ['type'] 和 ['text']
                # 增加判断，防止有些 block 没有 text 键 
                if isinstance(block, dict) and block.get("type") == "text":
                    print(block.get("text", ""), end="", flush=True)
            
            # 2. 如果你想看当前是哪个节点在运行（调试用）
            node_name = metadata.get('langgraph_node')
            if node_name == 'tools': # 如果正在运行工具节点
                print(f"\n[🛠️  执行工具中...]", flush=True)

        print() # AI 回复结束后换行

if __name__ == "__main__":
    chat_loop()