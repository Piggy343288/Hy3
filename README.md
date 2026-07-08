# Hy3 Showcase

基于 [Hy3](https://github.com/Tencent-Hunyuan/Hy3) 构建的 Streamlit 展示应用，演示 Hy3 的核心能力。

## 功能

- **💬 基础对话** — 单轮 & 多轮对话，附完整响应详情
- **🔍 推理模式对比** — 同一个问题在 `no_think` / `low` / `high` 三种模式下的输出对比
- **⌨️ 代码生成** — 用自然语言生成代码，展示深度推理能力
- **📡 流式输出** — 实时逐 token 展示生成过程

## 前提

Hy3 服务已部署并可访问。参考 [Hy3 Deployment](https://github.com/Tencent-Hunyuan/Hy3#deployment)。

## 快速开始

```bash
pip install -r requirements.txt

# 默认连接本地部署
streamlit run app.py

# 或指定自定义地址
HY3_BASE_URL=https://your-api.example.com/v1 \
HY3_API_KEY=your-key \
HY3_MODEL=hy3 \
streamlit run app.py
```

打开浏览器访问 `http://localhost:8501`。

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `HY3_BASE_URL` | `http://127.0.0.1:8000/v1` | API 地址 |
| `HY3_API_KEY` | `EMPTY` | API Key |
| `HY3_MODEL` | `hy3` | 模型名 |

## Demo

![demo](media/demo.gif)

> 录制 ≤ 1 min 的 demo 视频放入 `media/` 目录。
