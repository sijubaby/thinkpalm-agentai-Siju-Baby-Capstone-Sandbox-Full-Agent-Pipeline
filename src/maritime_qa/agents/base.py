from __future__ import annotations

from abc import ABC, abstractmethod

from maritime_qa.memory.store import SessionMemory


class BaseAgent(ABC):
    name: str = "base"

    @abstractmethod
    def run(self, memory: SessionMemory) -> None:
        ...
