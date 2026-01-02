# pip install langchain langchain-openai langchain-google-genai
# conda activate py310 ; pip install --upgrade langchain langgraph
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import Tool
from langchain_google_genai import ChatGoogleGenerativeAI # 示例使用 Gemini
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage,AIMessage,AIMessageChunk


# 1. 配置 MCP 服务器参数 (与之前一致)
server_params = StdioServerParameters(
    command="D:/application/anaconda3/envs/py310/python.exe",
    args=["D:/code/generativeAI/small_demo/mcp/langchain/ai-mcp-demo.py"],
    env={
        "PYTHONPATH": "D:/code/generativeAI/small_demo/mcp/langchain/",
        "PYTHONUNBUFFERED": "1"
    },
    cwd="D:/code/generativeAI/small_demo/mcp/langchain/",
    encoding="utf-8"
)

async def main():
    # 使用 stdio_client 连接 MCP 服务端
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 握手初始化
            await session.initialize()
            
            # 获取工具列表
            mcp_tools = await session.list_tools()
            
            # --- LangChain 工具转换开始 ---
            langchain_tools = []

            for tool in mcp_tools.tools:
                # 【闭包处理】使用默认参数锁定 tool_name
                # LangChain 的工具函数通常接收一个字符串或字典作为输入
                async def wrapper(tool_input=None, tool_name=tool.name):
                    """
                    LangChain 工具包装器
                    tool_input: LangChain 传入的参数（如果工具声明不需要参数，则为 None）
                    """
                    # 如果工具不需要参数，arguments 传空字典 {}
                    arguments = tool_input if isinstance(tool_input, dict) else {}
                    
                    print(f"DEBUG: LangChain 正在调用 MCP [{tool_name}] 工具，参数: {arguments}")
                    
                    # 转发请求给 MCP 服务端 (C# 或其他 Python 脚本)
                    result = await session.call_tool(tool_name, arguments)
                    
                    # 提取文本结果返回给 LangChain
                    if result.content:
                        return result.content[0].text
                    return "No output from tool."

                # 将其转换为 LangChain 的 Tool 对象 
                # 如果你用的是 ainvoke（异步调用），它就去找 coroutine 里的 wrapper 去干活。
                # 如果你用的是 invoke（同步调用），它就去找 func。
                lc_tool = Tool.from_function(
                    func=None,              # 同步函数置空 同步执行的回退方案 它会明确告诉你“我不支持同步”，而不是报一个莫名其妙的系统错误。
                    coroutine=wrapper,      # 传入异步包装器 当你（AI）决定调用我时，请使用 await 来运行 wrapper 这个函数
                    name=tool.name,         # 工具名称
                    description=tool.description # 工具描述，Agent 靠这个判断何时调用
                )
                langchain_tools.append(lc_tool)
            # --- LangChain 工具转换结束 ---

            # 2. 初始化模型 (这里以 Gemini 为例)
            # llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
            llm = ChatOllama(
                model="qwen2.5:7b",
                temperature=0, # 设为 0 以获得更确定性的回答
                streaming=True # 开启流式输出
            )

            # 设置记忆
            memory = MemorySaver()
            
            # 4. 构造 Agent
            # placeholder 会告诉 LangChain：“这里不是存一个简单的字符串，而是存一个消息列表。” 当 Agent 运行时，它会将所有的历史消息自动展开并填入这个位置。
            # ("placeholder", "{messages}")：接收对象列表。它保留了消息的原始类型（比如某条消息是工具调用的指令，某条是普通对话），这对模型判断后续动作至关重要。
            # 在构建 Agent 时，placeholder 是标准配置。如果去掉它，你的 Agent 每次只能处理孤立的一条指令。
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a professional system manager assistant. You can use the provided tools to get host information as needed."),
                ("placeholder", "{messages}"),
            ])
            
            # create_agent 返回 AgentExecutor，astream 返回完整 AIMessage。
            # create_react_agent 返回 LangGraph 的 CompiledGraph，astream_events 返回 AIMessageChunk（碎片）。
            # ★记住create_agent不支持astream，返回的不是流
            agent_executor = create_react_agent(
                llm, 
                langchain_tools, 
                prompt=prompt,
                checkpointer=memory,
            )
            
            # G. 配置运行参数：thread_id 用于区分不同的用户或会话
            config = {"configurable": {"thread_id": "mcp_demo_session_001"}}
    
            print("\nDEBUG: Starting astream_events...")
            # 6. 执行任务 async  astream_events 支持异步流式输出，获取更细粒度的流式事件
            # 使用 async for 配合 agent_executor.astream_events
            async for event in agent_executor.astream_events(
                {"messages": [HumanMessage(content="请帮我获取当前主机的系统信息")]},
                config=config,
                version="v2",# v2 是对底层异步流逻辑的重写，比 v1 更快，资源占用更低。 不用了解
            ):
                # 过滤事件类型，只处理 LLM 流式输出 基本不用
                if event["event"] == "on_llm_stream":
                    # 获取 AIMessageChunk
                    chunk = event["data"]["chunk"]
                    if hasattr(chunk, "content") and chunk.content:
                        print(chunk.content, end="", flush=True)
                
                # 处理聊天模型流式 ：现代 Agent 几乎都用这个，因为它能处理复杂的对话逻辑。
                elif event["event"] == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if hasattr(chunk, "content") and chunk.content:
                        print(chunk.content, end="", flush=True)
                
                # 检测工具调用
                elif event["event"] == "on_tool_start":
                    print(f"\n[🛠️  正在异步调用 MCP 工具: {event['name']}...]", flush=True)
                    # 如果你想看 AI 传给工具的参数：
                    # print(f"输入参数: {event['data'].get('input')}")

                # 监控工具结束 (看返回的 JSON)
                elif event["event"]  == "on_tool_end":
                    print(f"\n[✅ 工具执行完毕: {event['name']}]")
                    
                    # 提取工具返回的结果
                    output = event["data"].get("output")
                    
                    # 这里的 output 通常是 ToolMessage
                    if hasattr(output, "content"):
                        print(f"返回结果 (JSON): \n{output.content}")
                    else:
                        print(f"返回结果: {output}")

if __name__ == "__main__":
    # asyncio它背后做了三件事：
    #     创建一个事件循环（Event Loop，可以理解为异步任务调度器）。
    #     运行你的 main() 函数。
    #     运行结束后，自动关闭并清理调度器。
    asyncio.run(main()) 
    
    
"""
 原先写法
  async for token, metadata in agent_executor.astream(
                {"messages": [HumanMessage(content="请帮我获取当前主机的系统信息。")]},
                config=config,
                stream_mode="messages", 
            ):
                if hasattr(token, "content_blocks") and token.content_blocks:
                    block = token.content_blocks[0]
                    if isinstance(block, dict) and block.get("type") == "text":
                        print(block.get("text", ""), end="", flush=True)
                        
                elif hasattr(token, "content") and token.content:
                    print(token.content, end="", flush=True)

                node_name = metadata.get('langgraph_node')
                if node_name == 'tools': 
                    print(f"\n[🛠️  正在异步调用 MCP 工具...]", flush=True)
            print("\n--- 任务完成 ---")
            

第一次输出（JSON 部分）：这是 tools 节点运行完后，返回给 AI 的 ToolMessage（工具执行结果）。
DEBUG: LangChain 正在调用 MCP [get_host_info] 工具，参数: {}
{
    "system": "Windows",
    "release": "10",
    "machine": "AMD64",
    "processor": "AMD64",
    "memory_gb": "15.35",
    "cpu_count": "16",
    "cpu_model": "Unknown"
}



第二次输出（文字部分）：这是 AI 接收到工具结果后，生成的 AIMessage（最终回复）
[🛠️  正在异步调用 MCP 工具...]
当前主机的系统信息如下：

- 系统: Windows 10
- 内存: 15.35 GB
- CPU 核心数: 16
- CPU 模型: 未知

如果有其他需要查询的信息，请告知我。
--- 任务完成 ---

关键区别：

同步 stream：返回 AIMessageChunk，支持 token 级流式，但要求工具必须是同步的（不支持异步工具）。
异步 astream：返回完整 AIMessage，不支持 token 级流式，但支持异步工具。
为什么你的情况失败：
你的工具是异步的（coroutine=wrapper），同步 stream 尝试同步调用工具，导致 NotImplementedError: Tool does not support sync invocation.。

解决方案：

如果要用同步 stream 获取 AIMessageChunk，需要将工具改为同步（func=wrapper, coroutine=None），但 MCP 客户端是异步的，所以无法直接同步调用。
推荐继续用异步 astream_events（LangGraph），它能正确返回 AIMessageChunk 并支持异步工具。
如果你坚持用 create_agent + 同步流式，只能用同步工具，但 MCP 不支持同步调用。建议用 LangGraph 的 create_react_agent + astream_events。
"""