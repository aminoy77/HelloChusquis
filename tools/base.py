from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResult:
    success: bool
    output: str = ""
    error: str = ""
    # Structured payload from auto-generated API tools (petstore et al);
    # agent loop reads .output, so run() should also fill output when it
    # matters — data is for callers that want the raw response.
    data: Any = None


class BaseTool(ABC):
    name: str
    description: str
    config: dict = {}

    @abstractmethod
    def run(self, action: str = "list", **kwargs) -> ToolResult:
        pass

    def to_schema(self) -> dict:
        raise NotImplementedError


# Backward compatibility alias
Tool = BaseTool