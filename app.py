"""
Hy3 Showcase — 展示 Hy3 核心能力的 Streamlit 应用

运行:
  pip install -r requirements.txt
  streamlit run app.py

环境变量:
  HY3_BASE_URL (默认 http://127.0.0.1:8000/v1)
  HY3_API_KEY (默认 EMPTY)
  HY3_MODEL   (默认 hy3)
"""

import os
import time
from openai import OpenAI

import streamlit as st

BASE_URL = os.getenv("HY3_BASE_URL", "http://127.0.0.1:8000/v1")
API_KEY = os.getenv("HY3_API_KEY", "EMPTY")
MODEL = os.getenv("HY3_MODEL", "hy3")


def get_client():
    return OpenAI(base_url=BASE_URL, api_key=API_KEY)


st.set_page_config(page_title="Hy3 Showcase", page_icon="🧠", layout="wide")
st.title("🧠 Hy3 Showcase")
st.caption(f"Model: `{MODEL}` | Base URL: `{BASE_URL}`")

tab1, tab2, tab3, tab4 = st.tabs([
    "💬 基础对话", "🔍 推理模式对比", "⌨️ 代码生成", "📡 流式输出"
])

# ===== Tab 1: Basic Chat =====
with tab1:
    st.header("基础对话")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("单轮对话")
        single_q = st.text_input("输入问题", key="single_q",
                                 value="用比喻解释什么是 Transformer 的注意力机制")
        if st.button("发送", key="single_btn") and single_q:
            with st.spinner("生成中..."):
                client = get_client()
                resp = client.chat.completions.create(
                    model=MODEL,
                    messages=[{"role": "user", "content": single_q}],
                    temperature=0.7, max_tokens=512,
                )
                st.markdown("**回答:**")
                st.write(resp.choices[0].message.content)
                with st.expander("响应详情"):
                    st.json({
                        "id": resp.id,
                        "model": resp.model,
                        "usage": dict(resp.usage) if resp.usage else None,
                        "finish_reason": resp.choices[0].finish_reason,
                    })

    with col2:
        st.subheader("多轮对话")
        if "multi_messages" not in st.session_state:
            st.session_state.multi_messages = [
                {"role": "user", "content": "我喜欢猫。"}
            ]

        for msg in st.session_state.multi_messages:
            role = "🤖" if msg["role"] == "assistant" else "👤"
            st.markdown(f"**{role}:** {msg['content']}")

        multi_q = st.text_input("继续对话", key="multi_q",
                                value="它们为什么受欢迎？")
        if st.button("发送", key="multi_btn") and multi_q:
            st.session_state.multi_messages.append(
                {"role": "user", "content": multi_q})
            with st.spinner("生成中..."):
                client = get_client()
                resp = client.chat.completions.create(
                    model=MODEL,
                    messages=st.session_state.multi_messages,
                    temperature=0.9, max_tokens=512,
                )
                reply = resp.choices[0].message.content
                st.session_state.multi_messages.append(
                    {"role": "assistant", "content": reply})
            st.rerun()

        if st.button("清空历史"):
            st.session_state.multi_messages = [
                {"role": "user", "content": "我喜欢猫。"}]
            st.rerun()

# ===== Tab 2: Reasoning Mode =====
with tab2:
    st.header("推理模式对比")

    question = st.text_area("测试问题", value="一个水池有一个进水管和一个出水管。单独开进水管 6 小时可以注满水池，单独开出水管 8 小时可以排空水池。如果同时打开两个水管，需要多少小时才能将水池注满？", height=80)

    if st.button("三种模式对比"):
        client = get_client()
        for mode, label in [("no_think", "no_think（直接回答）"),
                             ("low", "low（快速思考）"),
                             ("high", "high（深度思考）")]:
            with st.spinner(f"正在生成 {label}..."):
                start = time.perf_counter()
                resp = client.chat.completions.create(
                    model=MODEL,
                    messages=[{"role": "user", "content": question}],
                    temperature=0.7, max_tokens=1024,
                    extra_body={
                        "chat_template_kwargs": {
                            "reasoning_effort": mode
                        }
                    },
                )
                elapsed = time.perf_counter() - start
                content = resp.choices[0].message.content

                with st.container():
                    st.markdown(f"**{label}** — *{elapsed:.1f}s*")
                    st.text(content)
                    st.divider()

# ===== Tab 3: Code Generation =====
with tab3:
    st.header("代码生成")

    code_prompt = st.text_area("描述要生成的代码",
                               value="用 Python 写一个函数，读取 CSV 文件并返回按某列排序的结果。使用命令行参数指定文件名和排序列。",
                               height=100)

    if st.button("生成代码"):
        with st.spinner("正在生成..."):
            client = get_client()
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[{
                    "role": "user",
                    "content": f"生成代码，只输出代码，不要解释。\n\n{code_prompt}"
                }],
                temperature=0.5, max_tokens=2048,
            )
            code = resp.choices[0].message.content
            st.code(code, language="python")
            with st.expander("响应详情"):
                st.json({
                    "usage": dict(resp.usage) if resp.usage else None,
                    "finish_reason": resp.choices[0].finish_reason,
                })

# ===== Tab 4: Streaming =====
with tab4:
    st.header("流式输出")

    stream_q = st.text_input("输入问题（流式模式）", key="stream_q",
                             value="用 100 字介绍机器学习中的过拟合现象")

    if st.button("开始流式输出"):
        client = get_client()
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": stream_q}],
            temperature=0.7, max_tokens=512,
            stream=True,
        )

        placeholder = st.empty()
        full = ""
        for chunk in resp:
            delta = chunk.choices[0].delta
            if delta.content:
                full += delta.content
                placeholder.markdown(full + "▌")

        placeholder.markdown(full)
        st.caption(f"共 {len(full)} 字符")
