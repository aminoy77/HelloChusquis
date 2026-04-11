from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ToolResult:
    success: bool
    output: str
    error: str = ""


class BaseTool(ABC):
    name: str
    description: str

    @abstractmethod
    def run(self, **kwargs) -> ToolResult:
        pass

    def to_schema(self) -> dict:
        raise NotImplementedError