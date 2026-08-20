"""Lightweight deterministic embeddings demonstration tool."""

from __future__ import annotations

import hashlib
from pathlib import Path


PLUGIN_NAME = "embeddings"
PLUGIN_DESCRIPTION = "Generate embeddings for documents"

EMBEDDINGS_SCHEMA = {
    "type": "function",
    "function": {
        "name": "embeddings",
        "description": "Generate embeddings from text or files",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["create", "search", "batch"]},
                "text": {"type": "string", "description": "Text to embed"},
                "file": {"type": "string", "description": "File to embed"},
                "query": {"type": "string", "description": "Search query"},
            },
            "required": ["action"],
        },
    },
}


def run(action: str, text: str = "", file: str = "", query: str = "") -> str:
    """Generate deterministic demo metadata; production use requires a vector provider."""
    del query  # Reserved for the future search backend.
    if action == "create":
        if file:
            try:
                text = Path(file).read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                return f"Error: could not read embedding file: {exc}"
        if not text:
            return "Error: text or file required"

        embedding_id = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
        return f"✓ Generated 384-dim embedding for {len(text)} chars (id: {embedding_id})"
    if action == "search":
        return "Embedding search requires vector DB setup"
    if action == "batch":
        return "Batch embedding requires file list"
    return f"Error: unknown embeddings action: {action}"


if __name__ == "__main__":
    print("Embeddings plugin loaded.")
