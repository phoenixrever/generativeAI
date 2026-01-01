# 安装: pip install mcp
# FastMCP 是 mcp 库中的一个高级封装类，旨在让你像写 FastAPI 或 Flask 一样快速创建 MCP 服务器。


# 层级,技术,负责内容
# 应用层,LangGraph,复杂的循环逻辑、多轮对话、状态管理。
# 协调层,LangChain,把模型、提示词和工具串联起来的框架。
# 接口层,MCP (FastMCP),定义工具的通信标准（如何传参、如何返回结果）。
# 数据层,Pydantic,确保数据格式从 Python 变成 JSON 过程中不出错。
# 语言层,Python,所有的底层逻辑实现。

# 总结
# LangChain 解决的是 “怎么用工具” 的问题。

# MCP 解决的是 “工具怎么找、怎么接” 的标准化问题。


# 使用 cline 为例子 点击左下角 mcp的 按钮添加mcp服务器


# 在 Cline 的设置中，"Auto-approve all tools" 是一个非常关键的开关。

# 简单来说，它的作用是：允许 AI 在不经过你手动点击“允许”的情况下，自动执行所有操作。


# {
#   "mcpServers": {
#     "host-info-mcp-server": {
#       "command": "D:/application/anaconda3/envs/py310/python.exe",
#       "args": [
#         "D:/code/generativeAI/small_demo/mcp/pydantic_ai/ai-mcp-demo.py"
#       ],
#       "env": {
#         "PYTHONPATH": "D:/code/generativeAI/small_demo/mcp/pydantic_ai/",
#         "PYTHONUNBUFFERED": "1"
#       }
#     }
#   }
# }



# {
#   "mcpServers": {
#     "host-info-mcp-server": {
#       "command": "uv",
#       "args": [
#         "run",
#         "--python", "3.10",
#         "D:/code/generativeAI/small_demo/mcp/pydantic_ai/ai-mcp-demo.py"
#       ]
#     }
#   }
# }


from mcp.server.fastmcp import FastMCP
import tools

mcp = FastMCP("host info mcp")
mcp.add_tool(tools.get_host_info)

@mcp.tool() # @mcp.tool(): 适合在当前文件直接定义新工具。即mco示例和工具函数写在同一个文件里面 
def foo():
    return ""

def main():
    # mcp.run("stdio") 是最常用的模式，它通过标准输入输出与客户端（如 Claude Desktop 或你的 LangGraph Agent）通信。
    # 这种方式的缺点就是 MCP server 和 客户端agent必须运行在同一台机器上，不能远程连接。
    # 另外一种是sse 基于 HTTP 的模式，适合远程连接，但需要额外配置 HTTP 服务器。
    mcp.run("stdio") #  


if __name__ == "__main__":
    main()

    
