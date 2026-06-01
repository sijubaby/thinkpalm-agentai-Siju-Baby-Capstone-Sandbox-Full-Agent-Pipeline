from __future__ import annotations

from maritime_qa.agents.base import BaseAgent
from maritime_qa.memory.store import SessionMemory
from maritime_qa.tools.tool_invoke import invoke_tool


class SpecAnalystAgent(BaseAgent):
    """Parses maritime feature specs and extracts compliance hints."""

    name = "spec_analyst"

    def run(self, memory: SessionMemory) -> None:
        spec_text = memory.get("spec_text", "")
        domain = memory.get("domain", "crew-cert")
        spec_path = memory.get("spec_path")

        memory.append_message(self.name, f"Invoking tool parse_maritime_spec for domain={domain}")
        result = invoke_tool(
            memory,
            self.name,
            "parse_maritime_spec",
            {"spec_text": spec_text, "domain": domain, "spec_path": spec_path},
        )
        memory.set("parsed_spec", result)
        req_count = len(result.get("requirements", []))
        hint_count = len(result.get("compliance_hints", []))
        memory.append_message(
            self.name,
            f"Handoff → Test Author: {req_count} requirements, {hint_count} compliance hints.",
        )
