# pip install langchain langchain-openai langchain-google-genai
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain.agents import create_agent
from langchain_core.tools import Tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI # 示例使用 Gemini
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver

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
                    """获取当前主机的详细系统信息。不需要任何输入参数。""" # AI 会读这段话！
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
            system_prompt = "You are a professional system manager assistant. You can use the provided tools to get host information as needed"
            agent_executor = create_agent(
                model=llm, 
                tools=langchain_tools, 
                checkpointer=memory,
                system_prompt=system_prompt
            )
        
            config = {"configurable": {"thread_id": "local_user"}} 
            # 6. 执行任务
            print("\n--- 开始执行 LangChain 任务 ---")
            # 参数顺序第一个参数是 输入字典（对应你的 Prompt 变量），第二个参数才是 配置字典。
            response = await agent_executor.ainvoke(
                {"input": "请帮我获取当前主机的系统信息。"},
                config={"configurable": {"thread_id": "local_user"}}
            )
            # {'messages': [AIMessage(content='', additional_kwargs={
            final_content = response["messages"][-1].content
            print(f"\nFinal Response: {final_content}")

if __name__ == "__main__":
    asyncio.run(main())