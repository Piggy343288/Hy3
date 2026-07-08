import os
from openai import OpenAI


BASE_URL = os.environ.get("HY3_BASE_URL", "http://127.0.0.1:8000/v1")
API_KEY = os.environ.get("HY3_API_KEY", "EMPTY")
MODEL = os.environ.get("HY3_MODEL", "hy3")

_client: OpenAI | None = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
    return _client


def chat(prompt: str, system: str | None = None, temperature: float = 0.3) -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    resp = get_client().chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=4096,
        extra_body={"chat_template_kwargs": {"reasoning_effort": "low"}},
    )
    return resp.choices[0].message.content
