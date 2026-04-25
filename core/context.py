"""Context manager for HelloChusquis."""

from dataclasses import dataclass, field
from typing import Any, Dict, List
import json
from pathlib import Path


@dataclass
class Context:
    """Message context with history and state."""
    messages: List[Dict[str, str]] = field(default_factory=list)
    state: Dict[str, Any] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
    
    def get_messages(self, limit: int = None):
        if limit:
            return self.messages[-limit:]
        return self.messages
    
    def set_var(self, key: str, value: Any):
        self.variables[key] = value
    
    def get_var(self, key: str, default: Any = None):
        return self.variables.get(key, default)
    
    def clear(self):
        self.messages.clear()
        self.variables.clear()
    
    def export(self) -> str:
        return json.dumps({
            "messages": self.messages,
            "state": self.state,
            "variables": self.variables
        }, indent=2)
    
    def import_(self, data: str):
        d = json.loads(data)
        self.messages = d.get("messages", [])
        self.variables = d.get("variables", {})


class ContextManager:
    """Manage multiple contexts."""
    
    def __init__(self):
        self.contexts: Dict[str, Context] = {}
        self.current: str = "default"
    
    def create_context(self, name: str) -> Context:
        ctx = Context()
        self.contexts[name] = ctx
        return ctx
    
    def switch(self, name: str):
        if name not in self.contexts:
            self.create_context(name)
        self.current = name
    
    def get_context(self, name: str = None) -> Context:
        return self.contexts.get(name or self.current)
    
    def delete(self, name: str):
        if name in self.contexts:
            del self.contexts[name]
    
    def list_contexts(self) -> List[str]:
        return list(self.contexts.keys())


# Singleton
_manager = None

def get_context_manager() -> ContextManager:
    global _manager
    if _manager is None:
        _manager = ContextManager()
    return _manager