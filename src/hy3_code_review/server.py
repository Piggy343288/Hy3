"""
Hy3 Code Review — MCP Server

Provides code review, file analysis, and refactoring suggestions
powered by Hy3 reasoning capabilities.

Tools:
  - review_diff      Review a git diff for bugs, style, and security
  - review_file      Review a source file for code quality
  - explain_refactor Explain a code snippet and suggest refactoring
"""

import os
import subprocess
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .hy3_client import chat

server = Server("hy3-code-review")

REVIEW_SYSTEM = """You are an expert code reviewer. Analyze code for:
1. Bugs and logic errors
2. Security vulnerabilities
3. Performance issues
4. Code style and maintainability
5. Missing error handling

Be specific, cite line numbers when possible, and give actionable fixes."""


def _read_file(path: str) -> str:
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return f"ERROR: file not found: {path}"
    if not p.is_file():
        return f"ERROR: not a file: {path}"
    return p.read_text(encoding="utf-8", errors="replace")


def _run_git_diff(repo_path: str, staged: bool = False) -> str:
    p = Path(repo_path).expanduser().resolve()
    if not p.is_dir():
        return f"ERROR: not a directory: {repo_path}"
    try:
        args = ["git", "diff"]
        if staged:
            args.append("--staged")
        result = subprocess.run(args, capture_output=True, text=True, cwd=p, timeout=30)
        output = result.stdout or result.stderr
        if not output.strip():
            return "(no diff)"
        return output
    except subprocess.TimeoutExpired:
        return "ERROR: git diff timed out"
    except FileNotFoundError:
        return "ERROR: git not found"
    except Exception as e:
        return f"ERROR: {e}"


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="review_diff",
            description="Review a git diff — reads git diff from a repo and analyzes it for bugs, style, and security",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo_path": {
                        "type": "string",
                        "description": "Path to the git repository",
                    },
                    "staged": {
                        "type": "boolean",
                        "description": "Review staged diff only (vs unstaged)",
                        "default": False,
                    },
                },
                "required": ["repo_path"],
            },
        ),
        Tool(
            name="review_file",
            description="Review a source code file — reads a file and analyzes code quality, bugs, and style",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the source file to review",
                    },
                    "language": {
                        "type": "string",
                        "description": "Programming language (auto-detected if omitted)",
                    },
                },
                "required": ["file_path"],
            },
        ),
        Tool(
            name="explain_refactor",
            description="Explain a code snippet and suggest refactoring improvements",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Code snippet to explain and refactor",
                    },
                    "language": {
                        "type": "string",
                        "description": "Programming language",
                    },
                },
                "required": ["code"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "review_diff":
        repo = arguments["repo_path"]
        staged = arguments.get("staged", False)
        diff = _run_git_diff(repo, staged=staged)
        if diff.startswith("ERROR"):
            return [TextContent(type="text", text=diff)]
        prompt = f"Review this git diff (repo: {repo}):\n\n```diff\n{diff[:32000]}\n```"
        result = chat(prompt, system=REVIEW_SYSTEM)
        return [TextContent(type="text", text=result)]

    if name == "review_file":
        fp = arguments["file_path"]
        lang = arguments.get("language", "")
        content = _read_file(fp)
        if content.startswith("ERROR"):
            return [TextContent(type="text", text=content)]
        header = f"Language: {lang}\n\n" if lang else ""
        prompt = f"{header}Review this source file ({fp}):\n\n```\n{content[:32000]}\n```"
        result = chat(prompt, system=REVIEW_SYSTEM)
        return [TextContent(type="text", text=result)]

    if name == "explain_refactor":
        code = arguments["code"]
        lang = arguments.get("language", "")
        header = f"Language: {lang}\n\n" if lang else ""
        prompt = (
            f"{header}Explain what this code does, then suggest refactoring "
            f"improvements (readability, performance, error handling):\n\n"
            f"```\n{code[:16000]}\n```"
        )
        result = chat(prompt)
        return [TextContent(type="text", text=result)]

    raise ValueError(f"Unknown tool: {name}")


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())
