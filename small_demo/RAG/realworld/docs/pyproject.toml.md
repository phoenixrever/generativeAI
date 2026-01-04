这份指南将你之前零散的知识点进行了系统化整合。它不仅解释了 `pyproject.toml` 的每一个字段，还涵盖了从环境搭建到代码规范的全流程。

---

# 🚀 Python 项目现代构建与配置全指南

## 一、 核心枢纽：`pyproject.toml` 深度解析

`pyproject.toml` 是现代 Python 项目的“大脑”，它取代了传统的 `setup.py`，实现了配置的标准化。

### 1. 构建后台 `[build-system]`

这是“制造机器的机器”，定义了如何将你的源代码打包。

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

```

### 2. 项目名片 `[project]`

定义项目的身份与核心需求。

- **基础信息**：`name` (项目名), `version` (版本号)。
- **核心依赖 (`dependencies`)**：项目运行必装的库（如 `chromadb`, `requests`）。
- **可选附件 (`optional-dependencies`)**：
- `gemini`: 只有需要 AI 功能的用户才安装。
- `all`: 开发者模式，安装包括 `black`、`pytest` 在内的所有工具。

### 3. 快捷命令 `[project.scripts]`

这是让你的程序像系统工具一样运行的关键。

```toml
realworld-cli = "realworld.cli.cli:main"

```

- **左侧**：你在终端输入的命令名。
- **右侧**：指向 `src/realworld/cli/cli.py` 文件中的 `main` 函数。

### 4. 工具配置 `[tool.*]`

为开发工具（如代码格式化工具 `Black`、类型检查工具 `Mypy`）提供统一设置，确保团队代码风格一致。

---

## 二、 环境管理：选择你的“隔离房间”

为了防止不同项目的依赖冲突，必须使用虚拟环境。

| 工具      | 适用场景    | 核心优势                                  |
| --------- | ----------- | ----------------------------------------- |
| **venv**  | 轻量开发    | Python 自带，无须额外安装。               |
| **Conda** | 数据科学/AI | 可管理非 Python 依赖（如 CUDA、C++ 库）。 |
| **uv**    | 极致效率    | Rust 编写，安装速度比 pip 快 10-100 倍。  |

---

## 三、 实战：从零启动项目

当你克隆了一个包含 `pyproject.toml` 的项目后，请遵循以下标准流程：

### 1. 创建并激活环境

```bash
# 使用 venv
python -m venv .venv
# 激活 (Windows)
.venv\Scripts\activate
# 激活 (Mac/Linux)
source .venv/bin/activate

```

### 2. 安装项目

```bash
# 模式 A：普通用户安装（只装运行环境）
pip install .

# 模式 B：开发者安装（-e 代表可编辑模式，改代码实时生效，安装所有工具）
pip install -e ".[all]"

```

### 3. 运行与体检

- **运行**：直接输入 `realworld-cli`。
- **体检**：运行 `black .` 自动美化代码，运行 `mypy src` 检查逻辑错误。

---

## 四、 推荐的项目结构 (Folder Structure)

建议采用 **`src-layout`**，这是目前 Python 社区最推荐的结构，能有效避免导入冲突：

```text
my_project/
├── pyproject.toml      # 核心配置
├── README.md           # 项目说明书
├── .gitignore          # 忽略不需要上传的文件
├── src/                # 源代码目录
│   └── realworld/      # 你的包名
│       ├── __init__.py
│       ├── main.py     # 核心逻辑
│       └── cli/        # 命令行接口
│           └── cli.py  # 包含 main() 函数
└── tests/              # 测试用例

```

---

**下一步建议：**
你现在的“地基”已经打得很牢固了。你是希望我帮你**一键生成上述的文件夹目录及基础文件**，还是想深入聊聊如何编写 `src/realworld/main.py` 里的 **RAG（检索增强生成）逻辑代码**？
