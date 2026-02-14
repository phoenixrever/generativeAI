"""
2. 如何查看我的额度使用情况？
你可以通过以下两个官方入口查看实时数据：

Google AI Studio 仪表板:

访问 https://aistudio.google.com/app/plan_usage

这里能直观看到你今天用了多少次，还剩多少。

Google Cloud Console (更详细):

访问 https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas

在这里你可以看到具体的“每分钟请求数”曲线。
"""


import asyncio
from dotenv import load_dotenv

# LangChain 相关导入
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver  # 内存记忆存储器

# 导入你写的工具
import tools

load_dotenv()

# 1. 配置模型 (确保环境变量中有 GOOGLE_API_KEY)
model = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-lite", 
    streaming=True,
    temperature=0  # 设置为 0 让编程任务更严谨
)

# 2. 组装工具集
langchain_tools = [tools.read_file, tools.list_files, tools.rename_file]

# 3. 设置记忆存储 (Checkpointer)
# MemorySaver 会在程序运行期间记住对话，如果想重启程序也记住，可以换成 SqliteSaver
memory = MemorySaver()

# 4. 创建 Agent
system_prompt = "You are a professional Python programmer. Use the provided tools to manage files."
agent_executor = create_agent(
    model, 
    tools=langchain_tools, 
    checkpointer=memory,
    system_prompt=system_prompt
)

async def chat_loop():
    # thread_id 是记忆的“钥匙”，相同的 ID 对应同一个人的对话
    config = {"configurable": {"thread_id": "user_1"}}
    
    print("🚀 Agent 已就绪! (输入 'exit' 退出)")
    print(f"📁 当前工作目录: {tools.base_dir.absolute()}")

    while True:
        user_input = input("\nUser >>> ")
        if user_input.lower() in ["exit", "quit"]:
            break

        # 5. 使用 astream 进行流式处理
        # stream_mode="messages" 可以让我们捕获到所有消息块
        print("AI >>> ", end="", flush=True)
        
        # 我们只发送当前这一条消息，LangGraph 会自动从 memory 中提取历史记录
        inputs = {"messages": [HumanMessage(content=user_input)]}
        
        async for msg, metadata in agent_executor.astream(
            inputs, 
            config=config, 
            stream_mode="messages"
        ):
            # 处理 AI 的文本输出
            if msg.content and not isinstance(msg, HumanMessage):
                print(msg.content, end="", flush=True)
            
            # 处理工具调用反馈 (让用户知道 AI 在干嘛)
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    print(f"\n🛠️  [正在执行: {tc['name']} 参数: {tc['args']}]", flush=True)
        
        print() # 换行

if __name__ == "__main__":
    try:
        asyncio.run(chat_loop())
    except KeyboardInterrupt:
        print("\n程序已停止")