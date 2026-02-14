这是一份为你准备的 **PowerShell (PS) 配置 Conda 环境**的保姆级指南。按照这个顺序操作，可以解决 99% 的路径找不到、环境不激活以及权限报错问题。

---

## 🛠️ PowerShell 配置 Conda 全流程

### 第一步：在 CMD 中唤醒初始化

由于 PowerShell 的权限限制，直接在 PS 里执行初始化有时会失败。我们先借助“老朋友” CMD 来铺路：

1. 打开 **CMD**（命令提示符）。
2. 输入并回车：
```cmd
conda init powershell

```


3. 看到提示 `modified` 或 `no change` 后，直接关闭 CMD。

---

### 第二步：解除 PowerShell 脚本禁令 (关键)

这是最容易卡住的一步。Windows 默认禁止 PowerShell 运行任何脚本（包括 Conda 的激活脚本）。

1. 在 Antigravity 的终端（或系统搜索 PowerShell）中，输入：
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

```


2. 当系统询问是否更改时，输入 **`Y`** 并回车。
> **为什么要这么做？** 这允许运行你本地编写或来自受信任来源（如 Anaconda）的脚本。



---

### 第三步：验证并强制激活

**彻底关闭** Antigravity，然后重新打开它的终端。

1. 观察终端开头。如果出现了 **`(base)`**，恭喜你，配置成功！
2. 如果没出现，手动尝试激活：
```powershell
conda activate base

```


3. 输入以下命令确认 Python 路径：
```powershell
Get-Command python

```



---

### 第四步：在 Antigravity 中完成“最后 1 厘米”

为了让 Antigravity 的 AI 助手也能同步使用这个环境：

1. 按下 `Ctrl + Shift + P`。
2. 搜索并选择 **`Python: Select Interpreter`**。
3. 在列表中点击那个带有 **`('base': conda)`** 字样的选项。

---

## ❓ 常见问题排查

### 1. 输入 `conda` 依然提示“无法识别”？

这说明 Anaconda 的安装目录没在系统 PATH 里。

* **解决方法：** 找到你的 Anaconda 安装路径（如 `C:\Users\Admin\anaconda3\Scripts`），手动将其添加到 Windows 的“系统环境变量” -> “Path” 中。

### 2. 觉得 `(base)` 前缀太丑？

如果你不想每次都看到那个括号，可以输入：

```powershell
conda config --set auto_activate_base false

```

*注：关闭后，你每次需要用 Python 前得手动输入 `conda activate`。*

### 3. 如何确认 pytest 能用了？

在配置好的 PS 终端输入：

```powershell
python -m pytest --version

```

如果显示了版本号，说明你的 **PowerShell + Conda + Python 模块** 这一套链路已经全线打通。

---

**配置好了吗？** 既然环境已经稳如泰山，你想让我帮你写一个简单的 Python 自动化脚本，在 Antigravity 里运行一下试试看吗？
