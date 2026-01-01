# TODO 异步目前还是不起作用
import asyncio
# 需要安装: pip install aioconsole
import aioconsole 
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver

# 假设你的 tools 已经定义好了
import tools

async def chat_loop():
    # 1. 初始化模型
    model = ChatOllama(
        model="qwen3:1.7b",
        temperature=0,
        streaming=True
    )

    # 2. 组装工具
    langchain_tools = [tools.read_file, tools.list_files, tools.rename_file]

    # 3. 设置记忆
    memory = MemorySaver()

    # 4. 创建 Agent (使用最新的 create_react_agent 避免旧版同步阻塞)
    system_prompt = "You are a professional Python programmer. Use the provided tools to manage files."
    agent_executor = create_agent(
        model, 
        tools=langchain_tools, 
        checkpointer=memory,
        system_prompt=system_prompt # 新版参数名
    )

    config = {"configurable": {"thread_id": "async_local_user"}}
    print("🚀 异步 Ollama Agent 已启动!")

    while True:
        # 使用 aioconsole.ainput 防止阻塞异步事件循环
        user_input = await aioconsole.ainput("\nUser >>> ")
        
        if user_input.lower() in ["exit", "quit"]:
            break

        print("AI >>> ", end="", flush=True)
        
        # 重点：使用 astream 配合 stream_mode="messages"
        async for token, metadata in agent_executor.astream(
            {"messages": [HumanMessage(content=user_input)]},
            config=config,
            stream_mode="messages",
        ):
            # 处理 Token 片段
            if hasattr(token, "content_blocks") and token.content_blocks:
                block = token.content_blocks[0]
                if isinstance(block, dict) and block.get("type") == "text":
                    print(block.get("text", ""), end="", flush=True)
                # 处理某些版本可能返回对象的情况
                elif hasattr(block, "text"):
                    print(block.text, end="", flush=True)
            
            # 处理工具节点显示
            node_name = metadata.get('langgraph_node')
            if node_name == 'tools':
                # 注意：在 astream 中，工具节点可能会多次触发事件，这里简单去重打印
                pass 

        print() 

if __name__ == "__main__":
    # 使用 asyncio.run 启动
    try:
        asyncio.run(chat_loop())
    except KeyboardInterrupt:
        pass