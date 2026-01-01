# pip install langchain-google-genai langgraph 
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
import  tools 
# load_dotenv()  # 如果你有 .env 文件存放 API Key，可以启用这行

# 1. 初始化模型 (对应 Pydantic AI 的 GeminiModel)
# 注意：LangChain 使用的是 ChatGoogleGenerativeAI
model = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite")

# 2. 准备工具列表
# LangChain 会自动通过函数的类型提示和 docstring 来识别工具
langchain_tools = [tools.read_file, tools.list_files, tools.rename_file]

# 3. 创建 Agent (对应 Pydantic AI 的 Agent)
# create_react_agent 会自动处理：用户输入 -> 思考 -> 调用工具 -> 观察结果 -> 回答 的循环
system_prompt = "You are an experienced programmer"

"""
def create_react_agent(
    model: str | BaseChatModel,  # 第 1 个位置参数 也可以 model = model
    tools: Sequence[...] = None, # 第 2 个位置参数 (有默认值)
    *,                           # 分隔符：重点在这里！
    system_prompt: str = None,   # 强制关键字参数 (必须写参数名才能传值)
)
"""
agent_executor = create_agent(model, langchain_tools, system_prompt=system_prompt,debug=True)

def main():
    # 4. 初始化对话历史 (在 LangGraph 中通常存放在状态里，这里我们手动维护一个列表)
    messages = []
    
    while True:
        user_input = input("Input: ")
        if user_input.lower() in ['quit', 'exit']:
            break

        # 5. 运行 Agent
        # LangChain 的输入通常是一个包含消息对象的字典
        inputs = {"messages": messages + [HumanMessage(content=user_input)]}
        
        # 运行并获取结果
        response = agent_executor.invoke(inputs)
        
        # 6. 更新历史
        # response["messages"] 包含了从开始到最后的所有消息
        messages = response["messages"]
        
        # 7. 打印最后一条消息（即 AI 的回复）
        print(messages[-1].content)

if __name__ == "__main__":
    main()