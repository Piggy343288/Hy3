# Hy3 Playground

一个基于 [Hy3](https://github.com/Tencent-Hunyuan/Hy3) 的轻量级 Web 展示应用，演示 Hy3 的三大核心能力：**推理（Reasoning）**、**工具调用（Tool Calling）**、**流式输出（Streaming）**。

## 功能

| 模块 | 能力 | 说明 |
|------|------|------|
| 🔍 推理模式对比 | Reasoning | 同一问题在 `no_think` / `low` / `high` 三档并行输出，直观对比思考深度 |
| 🔧 工具调用 | Tool Calling | Hy3 自动编排计算器 / 日期差 / 词频统计 工具，实时展示调用链路 |
| 📡 流式对话 | Streaming | 逐 token 实时渲染，SSE 推送 |

## 前提

Hy3 服务已部署并可访问（本地 vLLM/SGLang，或 OpenRouter 云端）。

## 快速开始

```bash
pip install -r requirements.txt

# 默认连接本地部署
python app.py

# 或自定义
HY3_BASE_URL=https://openrouter.ai/api/v1 \
HY3_API_KEY=sk-or-xxx \
HY3_MODEL=tencent/hy3 \
PORT=8501 \
python app.py
```

打开浏览器访问 `http://localhost:<PORT>`（默认 8000，与 Hy3 端口冲突时可改 `PORT`）。

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `HY3_BASE_URL` | `http://127.0.0.1:8000/v1` | API 地址 |
| `HY3_API_KEY` | `EMPTY` | API Key |
| `HY3_MODEL` | `hy3` | 模型名 |
| `PORT` | `8000` | 服务端口 |

## 项目结构

```
hy3-showcase/
├── app.py                 # Flask 后端 + 三个 API 路由
├── templates/index.html   # 前端（原生 HTML/CSS/JS）
├── requirements.txt
└── README.md
```

## Demo

录制 ≤ 1 min 的 demo 视频或 GIF 放入 `media/` 目录，展示三个 Tab 的实际运行效果。

## Screenshot

![screenshot](media/screenshot.png)
