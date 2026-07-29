from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ToolResult:
    success: bool
    output: str = ""
    error: str = ""
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