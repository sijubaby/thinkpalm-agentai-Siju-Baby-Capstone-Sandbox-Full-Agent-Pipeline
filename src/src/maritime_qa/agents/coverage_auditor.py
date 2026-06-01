from __future__ import annotations

from pathlib import Path

from maritime_qa.agents.base import BaseAgent
from maritime_qa.memory.store import SessionMemory
from maritime_qa.tools.tool_invoke import invoke_tool


class CoverageAuditorAgent(BaseAgent):
    """Maps generated tests to spec; runs Playwright; produces compliance gap report."""

    name = "coverage_auditor"

    def run(self, memory: SessionMemory) -> None:
        parsed = memory.get("parsed_spec")
        if not parsed:
            raise RuntimeError("SpecAnalyst must run before CoverageAuditor")

        gherkin_text = memory.get("gherkin_text", "")
        playwright_text = memory.get("playwright_text", "")
        output_dir = memory.get("output_dir", "out")
        run_playwright_flag = memory.get("run_playwright", True)

        playwright_results = None
        if run_playwright_flag:
            memory.append_message(self.name, "Invoking external tool run_playwright")
            playwright_results = invoke_tool(
                memory,
                self.name,
                "run_playwright",
                {
                    "test_path": memory.get("playwright_path", "tests/e2e/test_generated_maritime.py"),
                    "project_root": str(Path.cwd()),
                },
            )
            memory.set("playwright_results", playwright_results)

        memory.append_message(self.name, "Invoking tool generate_coverage_report")
        report = invoke_tool(
            memory,
            self.name,
            "generate_coverage_report",
            {
                "parsed_spec": parsed,
                "gherkin_text": gherkin_text,
                "playwright_text": playwright_text,
                "output_dir": str(output_dir),
                "playwright_results": playwright_results,
            },
        )
        memory.set("coverage_report", report)
        memory.append_message(
            self.name,
            f"Pipeline complete: {report['coverage_percent']}% coverage, "
            f"{report['compliance_gap_count']} compliance flag(s).",
        )
