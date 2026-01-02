import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pydantic_ai import Agent
from pydantic_ai.tools import Tool

# 1. 配置你的 C# MCP 服务器路径
server_params = StdioServerParameters(
    command="D:/application/anaconda3/envs/py310/python.exe",  # 必填：可执行程序的路径。可以是 .exe, python, node 等
    args=["D:/code/generativeAI/small_demo/mcp/pydantic_ai/ai-mcp-demo.py"], # args 是传给 python.exe 的参数，第一个必须是脚本路径 选填：传递给程序的命令行参数（数组格式），比如 ["--debug", "run"]
    env={  # 如果你的 MCP 脚本依赖了同文件夹下的其他 .py 文件 可以确保 ai-mcp-demo.py 启动时能正确找到并 import 那些辅助代码
      "PYTHONPATH": "D:/code/generativeAI/small_demo/mcp/pydantic_ai/",   
      # 开启 PYTHONUNBUFFERED=1（无缓冲）：  强制无缓冲输出，确保 MCP 协议响应不延迟
      # 每当 Python 执行一行 print() 或 logging.info()，它会立刻把数据推送到 stdout（标准输出）。
      # 现象：你可以实时看到 AI 正在做什么，日志流是连续且实时的。
      "PYTHONUNBUFFERED": "1"
    },
    cwd=None, # 4. 工作目录：建议设置为脚本所在的目录，防止脚本读写相对路径文件时出错 在代码里写了相对路径的话，就必须设置这个参数
    encoding="utf-8"  # 选填：指定输入输出的编码格式，默认是 utf-8
  )
async def main():
    # 2. 建立 MCP 连接
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 初始化 MCP
            await session.initialize()
            
            # 3. 获取 MCP 服务器上的工具列表
            mcp_tools = await session.list_tools()
            
            # 4. 将 MCP 工具转换为 Pydantic AI 可识别的格式
            # 这里的逻辑是：将 MCP 的动态工具映射到 Agent 的 function 中
            pydantic_ai_tools = []
            for tool in mcp_tools.tools:
                # async def mcp_tool_wrapper(arguments: dict, tool_name=tool.name):
                async def mcp_tool_wrapper(tool_name=tool.name):
                    # 当 Agent 调用时，实际上是发回给 MCP 服务器执行
                    result = await session.call_tool(tool_name)
                    return result.content

                # 将其封装为 Pydantic AI 的 Tool 对象
                pydantic_ai_tools.append(
                    Tool(
                        mcp_tool_wrapper,
                        name=tool.name,
                        description=tool.description,
                    )
                )

            # 5. 定义 Agent 并注入工具
            # 这里你可以换成 gemini-1.5-flash 或 openai:gpt-4o
            agent = Agent(
                'gemini-2.0-flash-lite', 
                tools=pydantic_ai_tools,
                system_prompt="You are a professional system manager assistant. You can use the provided tools to get host information as needed.",
            )

            # 6. 测试对话
            user_query = "请帮我获取主机的基本信息。"
            result = await agent.run(user_query)
            
            print(f"Agent 回复: {result}")

if __name__ == "__main__":
    asyncio.run(main())