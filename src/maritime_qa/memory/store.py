from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class SessionMemory:
    """Short-term memory for the current pipeline run (agent handoffs)."""

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}
        self.messages: list[dict[str, str]] = []
        self.tool_calls: list[dict[str, Any]] = []

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def append_message(self, agent: str, content: str) -> None:
        self.messages.append(
            {"agent": agent, "content": content, "ts": datetime.now(timezone.utc).isoformat()}
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "data": dict(self._data),
            "messages": list(self.messages),
            "tool_calls": list(self.tool_calls),
        }


class RunStore:
    """Long-term memory — persist each run under runs/<run_id>/."""

    def __init__(self, base_dir: str | Path = "runs") -> None:
        self.base_dir = Path(base_dir)

    def new_run_id(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:8]

    def save(self, run_id: str, session: SessionMemory, artifacts: dict[str, str]) -> Path:
        run_dir = self.base_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        snapshot = session.snapshot()
        (run_dir / "session.json").write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
        (run_dir / "tool_calls.json").write_text(
            json.dumps(snapshot.get("tool_calls", []), indent=2), encoding="utf-8"
        )
        if parsed := session.get("parsed_spec"):
            (run_dir / "parsed_spec.json").write_text(
                json.dumps(parsed, indent=2), encoding="utf-8"
            )
        meta = {"run_id": run_id, "artifacts": artifacts, "saved_at": datetime.now(timezone.utc).isoformat()}
        (run_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        return run_dir
