#### tools.py
from pathlib import Path
import os

# 1. 获取当前代码文件 (.py) 的绝对路径
current_file = Path(__file__).resolve()

# 2. 获取这个文件所在的文件夹目录
parent_dir = current_file.parent

# tool 的工作目录
base_dir = parent_dir / "test"



# Function must have a docstring if description not provided. langchain必须有docstring才能识别工具

def read_file(name: str) -> str:
    """Return file content. If not exist, return error message.
    """
    print(f"(read_file {name})")
    try:
        with open(base_dir / name, "r") as f:
            content = f.read()
        return content
    except Exception as e:
        return f"An error occurred: {e}"

def list_files() -> list[str]:
    """Return all file names under base_dir (recursively).
    """
    print("执行工具 list_file...")
    file_list = []
    # .glob("*")只看第一层 .rglob("*") 全盘扫描
    for item in base_dir.rglob("*"):
        if item.is_file():
            # 相对路径 (Relative Path): test/main.py
            # relative_to 返回的是一个 Path 对象。 str() 把它转换成普通的字符串。
            file_list.append(str(item.relative_to(base_dir))) 
    return file_list

def rename_file(name: str, new_name: str) -> str:
    """Rename a file from name to new_name under base_dir."""
    print(f"(rename_file {name} -> {new_name})")
    try:
        new_path = base_dir / new_name
        if not str(new_path).startswith(str(base_dir)):
            return "Error: new_name is outside base_dir."

        os.makedirs(new_path.parent, exist_ok=True)
        os.rename(base_dir / name, new_path)
        return f"File '{name}' successfully renamed to '{new_name}'."
    except Exception as e:
        return f"An error occurred: {e}"