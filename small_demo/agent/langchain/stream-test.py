# https://docs.langchain.com/oss/python/langchain/streaming#llm-tokens
from langchain.agents import create_agent
from langchain_ollama import ChatOllama

model = ChatOllama(
    # model="qwen2.5:7b",
    model="qwen3:1.7b",
    temperature=0,
    streaming=True
)
    
def get_weather(city: str) -> str:
    """Get weather for a given city."""

    return f"It's always sunny in {city}!"

agent = create_agent(
    model,
    tools=[get_weather],
)
# for chunk in agent.stream(  
#     {"messages": [{"role": "user", "content": "What is the weather in SF?"}]},
#     stream_mode="messages",
# ):
#     for step, data in chunk.items():
#         print(f"step: {step}")
#         print(f"content: {data['messages'][-1].content_blocks}")
        
        
# for token, metadata in agent.stream(  
#     {"messages": [{"role": "user", "content": "你是谁"}]},
#     stream_mode="messages",
# ):
#     # print(f"node: {metadata['langgraph_node']}")
#     print(f"content: {token.content_blocks[0].text}", end="", flush=True)
#     # print("\n")
    
    
for token, metadata in agent.stream(
    {"messages": [{"role": "user", "content": "你是谁"}]},
    stream_mode="messages",
):
    # 1. 检查是否有 content_blocks
    if hasattr(token, "content_blocks") and token.content_blocks:
        block = token.content_blocks[0]
        
        # 2. 用字典的方式访问 ['type'] 和 ['text']
        # 增加判断，防止有些 block 没有 text 键
        if isinstance(block, dict) and block.get("type") == "text":
            print(block.get("text", ""), end="", flush=True)
            
    # 3. (可选) 如果你想处理工具调用，它们通常不在 content_blocks 里
    # if hasattr(token, "tool_call_chunks") and token.tool_call_chunks:
    #     print("\n🛠️ [正在构造工具调用...]", end="", flush=True)