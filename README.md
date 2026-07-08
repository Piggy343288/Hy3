# Hy3 Code Review — MCP Server

基于 [Hy3](https://github.com/Tencent-Hunyuan/Hy3) 的 MCP 代码审查助手。通过 [MCP 协议](https://modelcontextprotocol.io/) 接入，支持 Cline / CodeBuddy / Cursor 等任意 MCP 客户端即插即用。

## 场景

**深度代码审查（Code Review）** — Hy3 分析代码差异、审查源文件、解释并重构代码片段。

## Tools

| Tool | 参数 | 功能 |
|------|------|------|
| `review_diff` | `repo_path`(必填), `staged`(可选) | 读取 git diff → Hy3 审查提交差异（bug / 安全 / 风格） |
| `review_file` | `file_path`(必填), `language`(可选) | 读取源文件 → Hy3 分析代码质量 |
| `explain_refactor` | `code`(必填), `language`(可选) | 解释代码逻辑并给出重构建议 |

## 安装

```bash
git clone https://github.com/Piggy343288/Hy3.git
cd Hy3
git checkout hy3-mcp-server
cd hy3-mcp-server
pip install -e .
```

## 配置

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `HY3_BASE_URL` | `http://127.0.0.1:8000/v1` | Hy3 API 地址 |
| `HY3_API_KEY` | `EMPTY` | API Key |
| `HY3_MODEL` | `hy3` | 模型名 |

### 客户端配置

#### CodeBuddy

CodeBuddy 支持项目级 MCP 配置。在项目根目录创建 `.codebuddy/mcp.json`：

```json
{
  "mcp_servers": [
    {
      "name": "hy3-code-review",
      "command": "hy3-code-review",
      "env": {
        "HY3_BASE_URL": "http://127.0.0.1:8000/v1",
        "HY3_API_KEY": "EMPTY",
        "HY3_MODEL": "hy3"
      }
    }
  ]
}
```

或通过 CLI 添加（已验证 CodeBuddy CLI v2.117.2）：

```bash
# 本地部署的 Hy3
codebuddy mcp add hy3-code-review hy3-code-review
# 然后编辑 %USERPROFILE%\.codebuddy.json 添加 env 字段
```

编辑后 `.codebuddy.json` 中的 MCP Server 配置如下：

```json
{
  "projects": {
    "YOUR_PROJECT_PATH": {
      "mcpServers": {
        "hy3-code-review": {
          "type": "stdio",
          "command": "hy3-code-review",
          "args": [],
          "env": {
            "HY3_BASE_URL": "http://127.0.0.1:8000/v1",
            "HY3_API_KEY": "EMPTY",
            "HY3_MODEL": "hy3"
          }
        }
      }
    }
  }
}
```

添加后重启 CodeBuddy，即可在 Chat 中调用 Hy3 进行代码审查。

#### Cline / Roo Code

在 VS Code 的项目 `.vscode/mcp.json` 中添加：

```json
{
  "servers": {
    "hy3-code-review": {
      "type": "stdio",
      "command": "hy3-code-review",
      "args": [],
      "env": {
        "HY3_BASE_URL": "http://127.0.0.1:8000/v1",
        "HY3_API_KEY": "EMPTY"
      }
    }
  }
}
```

#### Cursor

Cursor Settings → Features → MCP Servers → Add：

- Name: `hy3-code-review`
- Type: `command`
- Command: `hy3-code-review`

环境变量同上。

## 使用示例

### review_diff

在 MCP 客户端中运行：

```
请 review 当前分支的变更
```

MCP Server 自动读取 `git diff` 并调用 Hy3 审查。

### review_file

```
请审查 src/main.py 的代码质量
```

### explain_refactor

```
请解释下面这段代码并给出重构建议：

def process(items):
    r = []
    for i in items:
        if i not in r:
            r.append(i)
    return r
```

## 验证

```bash
# 启动 MCP Inspector（调试工具）
npx @modelcontextprotocol/inspector hy3-code-review

# 或直接运行
hy3-code-review
# 然后通过 MCP 客户端连接
```

## 项目结构

```
hy3-mcp-server/
├── pyproject.toml           # 打包配置
├── README.md
├── src/
│   └── hy3_code_review/
│       ├── __init__.py
│       ├── __main__.py      # 入口
│       ├── server.py         # MCP Server 实现（3 tools）
│       └── hy3_client.py     # Hy3 API 封装
```

## Demo

> 录制 ≤ 1 min 的 demo 视频 / GIF 放入 `media/` 目录。
