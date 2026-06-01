from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from maritime_qa.memory.store import SessionMemory
from maritime_qa.tools.registry import dispatch_tool


def invoke_tool(memory: SessionMemory, agent: str, tool_name: str, arguments: dict[str, Any]) -> Any:
    """Record tool call in session memory then dispatch."""
    log_args: dict[str, Any] = {}
    for key, value in arguments.items():
        if key == "parsed_spec":
            log_args[key] = "<structured spec>"
        elif key in ("gherkin_text", "playwright_text") and isinstance(value, str):
            log_args[key] = f"<{len(value)} chars>"
        elif isinstance(value, str) and len(value) > 300:
            log_args[key] = value[:300] + "..."
        else:
            log_args[key] = value

    memory.tool_calls.append(
        {
            "type": "call",
            "agent": agent,
            "tool": tool_name,
            "arguments": log_args,
            "ts": datetime.now(timezone.utc).isoformat(),
        }
    )
    result = dispatch_tool(tool_name, arguments)
    _apply_tool_result(memory, tool_name, result)
    memory.tool_calls.append(
        {
            "type": "result",
            "agent": agent,
            "tool": tool_name,
            "result_summary": _summarize(result),
            "ts": datetime.now(timezone.utc).isoformat(),
        }
    )
    return result


def _apply_tool_result(memory: SessionMemory, tool_name: str, result: Any) -> None:
    if not isinstance(result, dict):
        return
    if tool_name == "parse_maritime_spec":
        memory.set("parsed_spec", result)
    elif tool_name == "write_gherkin":
        memory.set("gherkin_path", result.get("path"))
        memory.set("gherkin_text", result.get("content", ""))
    elif tool_name == "write_playwright":
        memory.set("playwright_path", result.get("path"))
        memory.set("playwright_text", result.get("content", ""))
        content = result.get("content")
        if content:
            e2e = Path("tests/e2e/test_generated_maritime.py")
            e2e.parent.mkdir(parents=True, exist_ok=True)
            e2e.write_text(content, encoding="utf-8")
    elif tool_name == "generate_coverage_report":
        memory.set("coverage_report", result)
    elif tool_name == "run_playwright":
        memory.set("playwright_results", result)


def _summarize(result: Any) -> str:
    if isinstance(result, dict):
        if "coverage_percent" in result:
            return f"coverage={result['coverage_percent']}% gaps={len(result.get('gaps', []))}"
        if "success" in result:
            return f"playwright success={result['success']} {result.get('summary', '')}"
        return f"keys={list(result.keys())[:6]}"
    return str(result)[:200]
