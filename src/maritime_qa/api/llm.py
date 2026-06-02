"""LLM integration (Groq / OpenAI) with tool-calling for dynamic pipeline results."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from maritime_qa.api.llm_config import LlmConfig, is_llm_available, resolve_llm_config
from maritime_qa.memory.store import SessionMemory
from maritime_qa.tools.registry import TOOL_SCHEMAS
from maritime_qa.tools.tool_invoke import invoke_tool

AGENT_TOOLS: dict[str, list[str]] = {
    "spec_analyst": ["parse_maritime_spec"],
    "test_author": ["write_gherkin", "write_playwright"],
    "coverage_auditor": ["generate_coverage_report", "run_playwright"],
}

AGENT_INSTRUCTIONS: dict[str, str] = {
    "spec_analyst": (
        "You are a maritime QA Spec Analyst for ThinkPalm fleet software. "
        "You MUST call parse_maritime_spec with the full feature text and the domain from context. "
        "Do not skip the tool."
    ),
    "test_author": (
        "You are a maritime Test Author. You MUST call write_gherkin then write_playwright "
        "using parsed_spec and paths from context. Generate tests that match the feature description."
    ),
    "coverage_auditor": (
        "You are a Coverage Auditor. Call generate_coverage_report with parsed_spec, gherkin_text, "
        "playwright_text, and output_dir. If run_playwright is true, call run_playwright first."
    ),
}


def run_agent_with_llm(
    memory: SessionMemory,
    agent_name: str,
    llm_provider: str | None = None,
) -> None:
    """Run one agent via Groq/OpenAI tool-calling, or direct tools if unavailable."""
    cfg = resolve_llm_config(llm_provider)
    if not cfg:
        _run_agent_direct(memory, agent_name)
        return

    try:
        from openai import OpenAI
    except ImportError:
        _run_agent_direct(memory, agent_name)
        return

    memory.set("llm_provider", cfg.provider)
    memory.set("llm_model", cfg.model)

    allowed = AGENT_TOOLS.get(agent_name, [])
    tools = [t for t in TOOL_SCHEMAS if t["function"]["name"] in allowed]
    client = OpenAI(api_key=cfg.api_key, base_url=cfg.base_url)

    context = {
        "domain": memory.get("domain"),
        "output_dir": memory.get("output_dir"),
        "run_playwright": memory.get("run_playwright"),
        "spec_text": memory.get("spec_text", ""),
        "parsed_spec": memory.get("parsed_spec"),
        "gherkin_path": memory.get("gherkin_path"),
        "playwright_path": memory.get("playwright_path"),
    }

    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": (
                f"{AGENT_INSTRUCTIONS[agent_name]} "
                f"Provider: {cfg.provider}. Use tools for all structured outputs."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Agent: {agent_name}. Execute required tools.\n"
                f"Context:\n{json.dumps(context, default=str)[:12000]}"
            ),
        },
    ]

    memory.append_message(agent_name, f"LLM ({cfg.label}) starting tool loop")

    for _ in range(8):
        try:
            response = client.chat.completions.create(
                model=cfg.model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.2,
            )
        except Exception as exc:
            err = str(exc)
            if "proxies" in err:
                err += " — run: pip install \"httpx>=0.23,<0.28\""
            memory.append_message(agent_name, f"LLM error: {err} — falling back to direct tools")
            _run_agent_direct(memory, agent_name)
            return

        msg = response.choices[0].message
        if not msg.tool_calls:
            memory.append_message(agent_name, msg.content or "LLM step complete")
            break

        messages.append(msg.model_dump())
        for call in msg.tool_calls:
            name = call.function.name
            try:
                args = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            args = _enrich_tool_args(memory, name, args)
            invoke_tool(memory, agent_name, name, args)
            result_summary = memory.tool_calls[-1].get("result_summary", "ok")
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": result_summary,
                }
            )
    else:
        _run_agent_direct(memory, agent_name)


def _enrich_tool_args(memory: SessionMemory, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
    out = Path(memory.get("output_dir", "out"))
    if tool_name == "parse_maritime_spec":
        args.setdefault("spec_text", memory.get("spec_text", ""))
        args.setdefault("domain", memory.get("domain", "crew-cert"))
        args.setdefault("spec_path", memory.get("spec_path"))
    elif tool_name == "write_gherkin":
        args.setdefault("parsed_spec", memory.get("parsed_spec"))
        args.setdefault("output_path", str(out / "generated.feature"))
    elif tool_name == "write_playwright":
        args.setdefault("parsed_spec", memory.get("parsed_spec"))
        args.setdefault("domain", memory.get("domain"))
        args.setdefault("output_path", str(out / "test_generated_maritime.py"))
    elif tool_name == "generate_coverage_report":
        args.setdefault("parsed_spec", memory.get("parsed_spec"))
        args.setdefault("gherkin_text", memory.get("gherkin_text", ""))
        args.setdefault("playwright_text", memory.get("playwright_text", ""))
        args.setdefault("output_dir", str(out))
        if memory.get("playwright_results"):
            args.setdefault("playwright_results", memory.get("playwright_results"))
    elif tool_name == "run_playwright":
        args.setdefault("test_path", memory.get("playwright_path", ""))
        args.setdefault("project_root", str(Path.cwd()))
    return args


def _run_agent_direct(memory: SessionMemory, agent_name: str) -> None:
    from maritime_qa.agents.coverage_auditor import CoverageAuditorAgent
    from maritime_qa.agents.spec_analyst import SpecAnalystAgent
    from maritime_qa.agents.test_author import TestAuthorAgent

    mapping = {
        "spec_analyst": SpecAnalystAgent,
        "test_author": TestAuthorAgent,
        "coverage_auditor": CoverageAuditorAgent,
    }
    mapping[agent_name]().run(memory)
