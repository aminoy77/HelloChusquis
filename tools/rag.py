from tools.base import BaseTool, ToolResult
import os
import json
import httpx


PLUGIN_NAME = "rag"
PLUGIN_DESCRIPTION = "RAG - Upload documents for contextual knowledge"

RAG_SCHEMA = {
    "type": "function",
    "function": {
        "name": "rag",
        "description": "Add documents to knowledge base, query with context",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["add", "query", "list", "clear"]},
                "file": {"type": "string", "description": "File to add"},
                "text": {"type": "string", "description": "Text to add"},
                "query": {"type": "string", "description": "Query to ask"},
                "collection": {"type": "string", "description": "Collection name"},
            },
            "required": ["action"]
        }
    }
}


# Simple RAG using file-based storage
RAG_DIR = os.path.expanduser("~/.hellochusquis/rag")


def get_embeddings(text: str) -> list:
    """Simple embedding using hash (placeholder)."""
    return [hash(text) % 1000]


def run(action: str, file: str = "", text: str = "", query: str = "", collection: str = "default") -> str:
    """RAG operations."""
    os.makedirs(RAG_DIR, exist_ok=True)
    
    coll_dir = os.path.join(RAG_DIR, collection)
    os.makedirs(coll_dir, exist_ok=True)
    
    if action == "add":
        if file:
            if not os.path.exists(file):
                return f"Error: File not found: {file}"
            with open(file, "r") as f:
                content = f.read()
        elif text:
            content = text
        else:
            return "Error: file or text required"
        
        # Save document
        doc_id = str(hash(content))[:16]
        doc_file = os.path.join(coll_dir, f"{doc_id}.txt")
        with open(doc_file, "w") as f:
            f.write(content)
        
        return f"✓ Added document to collection '{collection}'"
    
    elif action == "query":
        if not query:
            return "Error: query required"
        
        # Simple search - find most relevant document
        docs = []
        for f in os.listdir(coll_dir):
            if f.endswith(".txt"):
                with open(os.path.join(coll_dir, f), "r") as f:
                    content = f.read()
                    # Simple relevance score
                    score = sum(1 for word in query.lower().split() if word in content.lower())
                    docs.append((score, content))
        
        if not docs:
            return "No documents in collection."
        
        # Get best match
        docs.sort(reverse=True)
        best = docs[0][1][:1000]
        
        # Use LLM to answer from context
        try:
            from core.provider import ProviderPool
            pool = ProviderPool()
            
            prompt = f"""Based on this context, answer the question:

Context: {best}

Question: {query}

Answer:"""
            
            response = pool.chat_with_retry([{"role": "user", "content": prompt}])
            choices = response.get("choices", [])
            if not choices:
                return f"Found relevant: {best[:500]}..."
            content = choices[0].get("message", {}).get("content", "")
            return content or f"Found relevant: {best[:500]}..."
        
        except Exception as e:
            return f"Found relevant: {best[:500]}..."
    
    elif action == "list":
        files = os.listdir(coll_dir)
        return f"Collection '{collection}': {len(files)} documents"
    
    elif action == "clear":
        import shutil
        shutil.rmtree(coll_dir)
        return f"✓ Cleared collection '{collection}'"
    
    else:
        return f"Unknown action: {action}"


if __name__ == "__main__":
    print("RAG plugin loaded.")