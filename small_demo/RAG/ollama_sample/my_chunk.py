"""
文本分割模块 (Text Chunking Module)

这个模块负责将长文本分割成小的块 (chunks)，以便于后续的嵌入和检索。
我们使用简单的段落分割方法，将文本按双换行符分割，并保留标题信息。
"""
from pathlib import Path


# 1. 获取当前代码文件 (.py) 的绝对路径
current_file = Path(__file__).resolve()
# 2. 获取这个文件所在的文件夹目录
parent_dir = current_file.parent
# tool 的工作目录
base_dir = parent_dir / "data"


def read_data() -> str:
    """
    读取数据文件的内容。

    返回:
        str: 文件的完整文本内容。
    """
    with open(base_dir/"data.txt", "r", encoding="utf-8") as f:
        return f.read()

def get_chunks() -> list[str]:
    """
    将文本分割成块。

    这个函数读取数据文件，按段落分割文本。
    如果遇到以 '#' 开头的行（标题），将其与后续内容合并。

    返回:
        list[str]: 分割后的文本块列表，每个块包含标题和相应内容。
    """
    content = read_data()
    # 按双换行符分割，得到段落
    chunks = content.split('\n\n')

    result = []
    header = ""
    for c in chunks:
        c = c.strip()  # 移除前后空白
        if not c:  # 跳过空段落
            continue
        if c.startswith("#"):
            # 如果是标题，累积到 header
            header += f"{c}\n"
        else:
            # 如果是内容，与之前的标题合并成一个块
            if header:
                result.append(f"{header}{c}")
                header = ""  # 重置标题
            else:
                result.append(c)

    # 处理最后一个标题（如果没有后续内容）
    if header:
        result.append(header.strip())

    return result

if __name__ == '__main__':
    """
    主函数：用于测试文本分割功能。
    运行此脚本时，会打印所有分割后的块。
    """
    chunks = get_chunks()
    for i, c in enumerate(chunks):
        print(f"Chunk {i+1}:")
        print(c)
        print("--------------")