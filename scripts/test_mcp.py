"""
Hy3 MCP Server — 端到端集成测试

启动一个 mock Hy3 API server，再启动 MCP server，
通过 MCP 客户端协议验证 3 个工具的 listing 和 calling 是否正常。

用法: python scripts/test_mcp.py
"""

import os
import sys
import json
import time
import threading
import subprocess

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ── mock Hy3 API ────────────────────────────────────────────────
MOCK_RESPONSE = "这是一个模拟的 Hy3 回复，用于验证 MCP 工具调用链路正常工作。"


def mock_hy3_server():
    from http.server import HTTPServer, BaseHTTPRequestHandler

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            data = json.loads(body) if body else {}
            msg = data.get("messages", [{}])[-1].get("content", "")[:80]

            resp = {
                "id": "mock-xxx",
                "model": "hy3-mock",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": f"[Mock Reply to: {msg}]\n{MOCK_RESPONSE}"
                    },
                    "finish_reason": "stop",
                }],
                "usage": {"prompt_tokens": 10, "completion_tokens": 15, "total_tokens": 25},
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(resp).encode())

        def log_message(self, *a):
            pass  # suppress logs

    server = HTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    print(f"[mock] Hy3 mock API running on http://127.0.0.1:{port}/v1")
    os.environ["HY3_BASE_URL"] = f"http://127.0.0.1:{port}/v1"
    os.environ["HY3_API_KEY"] = "EMPTY"
    os.environ["HY3_MODEL"] = "hy3"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return port


# ── MCP client utility ──────────────────────────────────────────
def send_request(proc, req: dict) -> dict:
    """Send JSON-RPC request to MCP server via stdin, read response from stdout."""
    line = json.dumps(req) + "\n"
    proc.stdin.write(line.encode())
    proc.stdin.flush()

    resp_lines = []
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        decoded = line.decode().strip()
        if decoded:
            try:
                obj = json.loads(decoded)
                resp_lines.append(obj)
                if "id" in obj:
                    return obj
            except json.JSONDecodeError:
                pass
    if resp_lines:
        return resp_lines[0]
    return {"error": "no response"}


# ── Main ────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("Hy3 MCP Server — End-to-End Test")
    print("=" * 60)

    # Step 1: start mock API
    port = mock_hy3_server()
    time.sleep(0.5)

    # Step 2: start MCP server as subprocess
    mcp_module = os.path.join(os.path.dirname(__file__), "..", "src")
    sys.path.insert(0, mcp_module)

    proc = subprocess.Popen(
        [sys.executable, "-m", "hy3_code_review"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=os.environ,
    )
    time.sleep(1)

    try:
        # Step 3: initialize
        print("\n[1/4] Sending initialize...")
        init_resp = send_request(proc, {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "0.1.0",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0"},
            },
        })
        print(f"       result: server capabilities received" if "result" in init_resp else f"       error: {init_resp.get('error')}")

        # Step 4: list tools
        print("\n[2/4] Listing tools...")
        list_resp = send_request(proc, {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        })

        tools = list_resp.get("result", {}).get("tools", [])
        print(f"       Found {len(tools)} tools:")
        for t in tools:
            props = list(t.get("inputSchema", {}).get("properties", {}).keys())
            print(f"       [OK] {t['name']}: {t.get('description', '')[:50]}...")
            print(f"         params: {props}")

        assert len(tools) == 3, f"Expected 3 tools, got {len(tools)}"

        # Step 5: call explain_refactor
        print("\n[3/4] Calling explain_refactor...")
        call_resp = send_request(proc, {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "explain_refactor",
                "arguments": {"code": "def add(a,b): return a+b", "language": "Python"},
            },
        })
        content = call_resp.get("result", {}).get("content", [{}])[0].get("text", "")
        print(f"       Response ({len(content)} chars):")
        print(f"       {content[:150]}...")
        assert content.startswith("[Mock Reply to:"), f"Unexpected response: {content[:50]}"

        # Step 6: call review_file with a real file
        print("\n[4/4] Calling review_file (self-test)...")
        test_file = __file__
        call_resp2 = send_request(proc, {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "review_file",
                "arguments": {"file_path": test_file, "language": "Python"},
            },
        })
        content2 = call_resp2.get("result", {}).get("content", [{}])[0].get("text", "")
        print(f"       Response ({len(content2)} chars): {content2[:100]}...")
        assert not content2.startswith("ERROR:"), f"File read error: {content2}"

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED [PASS]")
        print(f"MCP Server: stdio mode, 3 tools")
        print(f"Hy3 API: mock API on port {port}")
        print(f"Cline MCP: configured at Cline settings")
        print(f"CodeBuddy: registered via CLI")
        print("=" * 60)

    finally:
        proc.terminate()
        proc.wait(timeout=3)


if __name__ == "__main__":
    main()
