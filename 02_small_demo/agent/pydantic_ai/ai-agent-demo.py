##https://ai.pydantic.dev/agents/
##https://ai.pydantic.dev/models/google/#api-key-generative-language-api
"""
装饰器 (@agent.tool)：就像是给 Agent 手动安装插件。

构造函数 (tools=[...])：就像是买电脑时自带的预装软件。
"""
from pydantic_ai import Agent

from dotenv import load_dotenv
import tools

load_dotenv()

agent = Agent("gemini-2.5-flash-lite",
              system_prompt="You are an experienced programmer",
              tools=[tools.read_file, tools.list_files, tools.rename_file])

def main():
    # 1. 初始化对话历史列表，用于存储每一轮的对话记录（用户说的 + AI 回复的）
    history = []
    
    # 2. 开启一个无限循环，让你可以持续和 AI 聊天，直到手动停止
    while True:
        # 获取用户在命令行输入的指令
        user_input = input("Input: ")
        
        # 3. 运行 Agent，处理用户输入
        # message_history=history: 把之前的对话记录发给 AI，这样它才能“记得”你刚才说过的话
        resp = agent.run_sync(
            user_input,
            message_history=history
        )
        
        # 4. 【关键步骤】更新对话历史
        # resp.all_messages() 会返回本次对话产生的所有消息（包括 AI 的思考过程和结果）
        # 将其转化为 list 并覆盖旧的 history，供下一轮对话使用
        history = list(resp.all_messages())
        
        # 5. 打印 AI 的最终回复内容
        print(resp.output)

# 提示：运行 main() 之前确保你已经定义好了 agent


if __name__ == "__main__":
    main()


