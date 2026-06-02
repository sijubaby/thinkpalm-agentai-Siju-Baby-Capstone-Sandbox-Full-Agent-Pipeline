from __future__ import annotations

from pathlib import Path

from maritime_qa.agents.base import BaseAgent
from maritime_qa.memory.store import SessionMemory
from maritime_qa.tools.tool_invoke import invoke_tool


class TestAuthorAgent(BaseAgent):
    """Generates Gherkin and Playwright tests via tool calls."""

    name = "test_author"

    def run(self, memory: SessionMemory) -> None:
        parsed = memory.get("parsed_spec")
        if not parsed:
            raise RuntimeError("SpecAnalyst must run before TestAuthor")

        output_dir = Path(memory.get("output_dir", "out"))
        domain = memory.get("domain", "crew-cert")
        gherkin_path = output_dir / "generated.feature"
        playwright_path = output_dir / "test_generated_maritime.py"

        memory.append_message(self.name, "Invoking tool write_gherkin")
        gherkin = invoke_tool(
            memory,
            self.name,
            "write_gherkin",
            {"parsed_spec": parsed, "output_path": str(gherkin_path)},
        )
        memory.set("gherkin_path", gherkin["path"])
        memory.set("gherkin_text", gherkin["content"])

        memory.append_message(self.name, "Invoking tool write_playwright")
        pw = invoke_tool(
            memory,
            self.name,
            "write_playwright",
            {
                "parsed_spec": parsed,
                "domain": domain,
                "output_path": str(playwright_path),
            },
        )
        memory.set("playwright_path", pw["path"])
        memory.set("playwright_text", pw["content"])

        e2e_copy = Path("tests/e2e/test_generated_maritime.py")
        e2e_copy.parent.mkdir(parents=True, exist_ok=True)
        e2e_copy.write_text(pw["content"], encoding="utf-8")
        memory.append_message(
            self.name,
            f"Handoff → Coverage Auditor: artifacts in {output_dir}",
        )
