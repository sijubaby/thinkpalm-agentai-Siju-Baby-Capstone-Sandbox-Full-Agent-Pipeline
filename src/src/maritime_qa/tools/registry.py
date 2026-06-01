"""Tool registry for agent tool-calling (OpenAI function schemas + dispatch)."""

from __future__ import annotations

from typing import Any, Callable

from maritime_qa.tools.coverage import generate_coverage_report
from maritime_qa.tools.gherkin import write_gherkin
from maritime_qa.tools.parse_spec import parse_maritime_spec
from maritime_qa.tools.playwright_gen import write_playwright
from maritime_qa.tools.playwright_runner import run_playwright

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "parse_maritime_spec",
            "description": "Parse a maritime feature spec markdown file into structured JSON.",
            "parameters": {
                "type": "object",
                "properties": {
                    "spec_text": {"type": "string"},
                    "domain": {"type": "string", "enum": ["crew-cert", "ais", "port-workflow"]},
                    "spec_path": {"type": "string"},
                },
                "required": ["spec_text", "domain"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_gherkin",
            "description": "Generate Gherkin feature file from parsed spec JSON.",
            "parameters": {
                "type": "object",
                "properties": {
                    "parsed_spec": {"type": "object"},
                    "output_path": {"type": "string"},
                },
                "required": ["parsed_spec", "output_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_playwright",
            "description": "Generate pytest-playwright test file from parsed spec.",
            "parameters": {
                "type": "object",
                "properties": {
                    "parsed_spec": {"type": "object"},
                    "domain": {"type": "string"},
                    "output_path": {"type": "string"},
                },
                "required": ["parsed_spec", "domain", "output_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_coverage_report",
            "description": "Build coverage gap report with compliance flags.",
            "parameters": {
                "type": "object",
                "properties": {
                    "parsed_spec": {"type": "object"},
                    "gherkin_text": {"type": "string"},
                    "playwright_text": {"type": "string"},
                    "output_dir": {"type": "string"},
                    "playwright_results": {"type": "object"},
                },
                "required": ["parsed_spec", "gherkin_text", "playwright_text", "output_dir"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_playwright",
            "description": "External tool: execute generated Playwright tests via pytest.",
            "parameters": {
                "type": "object",
                "properties": {
                    "test_path": {"type": "string"},
                    "project_root": {"type": "string"},
                },
                "required": ["test_path"],
            },
        },
    },
]

_DISPATCH: dict[str, Callable[..., Any]] = {
    "parse_maritime_spec": parse_maritime_spec,
    "write_gherkin": write_gherkin,
    "write_playwright": write_playwright,
    "generate_coverage_report": generate_coverage_report,
    "run_playwright": run_playwright,
}


def dispatch_tool(name: str, arguments: dict[str, Any]) -> Any:
    if name not in _DISPATCH:
        raise ValueError(f"Unknown tool: {name}")
    return _DISPATCH[name](**arguments)
