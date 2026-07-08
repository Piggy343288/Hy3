"""
Hy3 Playground — 基于 Hy3 核心能力的轻量级 Web 展示应用

演示 Hy3 的三大核心能力：
  1. 推理模式（Reasoning）：no_think / low / high 三档对比
  2. 工具调用（Tool Calling）：计算器 / 日期差 / 词频统计 的真实调用链路
  3. 流式输出（Streaming）：逐 token 实时渲染

运行：
  pip install -r requirements.txt
  python app.py

环境变量：
  HY3_BASE_URL  (默认 http://127.0.0.1:8000/v1)
  HY3_API_KEY   (默认 EMPTY)
  HY3_MODEL     (默认 hy3)
  PORT          (默认 8000，与 Hy3 冲突时可改成 8501)
"""

import os
import json
import threading
from datetime import date

from flask import Flask, render_template, request, Response, jsonify, stream_with_context
from openai import OpenAI

app = Flask(__name__)

BASE_URL = os.getenv("HY3_BASE_URL", "http://127.0.0.1:8000/v1")
API_KEY = os.getenv("HY3_API_KEY", "EMPTY")
MODEL = os.getenv("HY3_MODEL", "hy3")
PORT = int(os.getenv("PORT", "8000"))


def client() -> OpenAI:
    return OpenAI(base_url=BASE_URL, api_key=API_KEY)


# ---------------------------------------------------------------------------
# 1. Reasoning Lab — 三档模式并行对比
# ---------------------------------------------------------------------------
@app.route("/api/reason")
def api_reason():
    question = request.args.get("q", "").strip()
    if not question:
        return jsonify({"error": "empty question"}), 400

    modes = [
        ("no_think", "直接回答"),
        ("low", "快速思考"),
        ("high", "深度思考"),
    ]

    results = {}

    def run(mode: str):
        try:
            resp = client().chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": question}],
                temperature=0.7,
                max_tokens=2048,
                extra_body={"chat_template_kwargs": {"reasoning_effort": mode}},
            )
            results[mode] = {
                "ok": True,
                "content": resp.choices[0].message.content,
                "usage": dict(resp.usage) if resp.usage else {},
            }
        except Exception as e:  # noqa: BLE001
            results[mode] = {"ok": False, "error": str(e)}

    threads = [threading.Thread(target=run, args=(m[0],)) for m in modes]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    return jsonify({
        "question": question,
        "results": {
            "no_think": results.get("no_think"),
            "low": results.get("low"),
            "high": results.get("high"),
        },
    })


# ---------------------------------------------------------------------------
# 2. Tool Calling — 真实工具链路
# ---------------------------------------------------------------------------
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "计算数学表达式，如 (25+17)*3",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "数学表达式"}
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "days_between",
            "description": "计算两个日期之间的天数差，格式 YYYY-MM-DD",
            "parameters": {
                "type": "object",
                "properties": {
                    "start": {"type": "string", "description": "开始日期 YYYY-MM-DD"},
                    "end": {"type": "string", "description": "结束日期 YYYY-MM-DD"},
                },
                "required": ["start", "end"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "word_count",
            "description": "统计一段文本的字数 / 词数",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "待统计文本"}
                },
                "required": ["text"],
            },
        },
    },
]


def _call_tool(name: str, args: dict) -> str:
    if name == "calculator":
        try:
            return json.dumps({"result": eval(args["expression"], {"__builtins__": {}}, {})})
        except Exception as e:  # noqa: BLE001
            return json.dumps({"error": str(e)})
    if name == "days_between":
        d1 = date.fromisoformat(args["start"])
        d2 = date.fromisoformat(args["end"])
        return json.dumps({"days": abs((d2 - d1).days)})
    if name == "word_count":
        text = args["text"]
        return json.dumps({"chars": len(text), "words": len(text.split())})
    return json.dumps({"error": f"unknown tool {name}"})


@app.route("/api/tool", methods=["POST"])
def api_tool():
    data = request.get_json(force=True)
    query = (data.get("q") or "").strip()
    if not query:
        return jsonify({"error": "empty query"}), 400

    messages = [{"role": "user", "content": query}]
    events = []

    try:
        for _ in range(5):
            resp = client().chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                temperature=0.3,
                max_tokens=1024,
            )
            msg = resp.choices[0].message
            if not msg.tool_calls:
                events.append({"type": "answer", "content": msg.content})
                break

            messages.append(msg)
            for tc in msg.tool_calls:
                fn = tc.function
                events.append({"type": "call", "name": fn.name, "args": fn.arguments})
                result = _call_tool(fn.name, json.loads(fn.arguments))
                events.append({"type": "result", "name": fn.name, "content": result})
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })
        else:
            events.append({"type": "answer", "content": "（达到最大轮数）"})
    except Exception as e:  # noqa: BLE001
        events.append({"type": "error", "content": str(e)})

    return jsonify({"events": events})


# ---------------------------------------------------------------------------
# 3. Streaming Chat
# ---------------------------------------------------------------------------
@app.route("/api/chat")
def api_chat():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "empty"}), 400

    @stream_with_context
    def gen():
        try:
            resp = client().chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": q}],
                temperature=0.7,
                max_tokens=2048,
                stream=True,
            )
            for chunk in resp:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield f"data: {json.dumps({'content': delta.content})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:  # noqa: BLE001
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(gen(), mimetype="text/event-stream")


@app.route("/")
def index():
    return render_template("index.html", model=MODEL, base_url=BASE_URL)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=False)
