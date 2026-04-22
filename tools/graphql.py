from tools.base import BaseTool, ToolResult
import httpx
import os


PLUGIN_NAME = "graphql"
PLUGIN_DESCRIPTION = "Execute GraphQL queries"

GRAPHQL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "graphql",
        "description": "Execute GraphQL operations",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["query", "mutation", "introspect"]},
                "endpoint": {"type": "string", "description": "GraphQL endpoint URL"},
                "query": {"type": "string", "description": "GraphQL query or mutation"},
                "variables": {"type": "string", "description": "Variables as JSON"},
                "headers": {"type": "string", "description": "Headers as JSON"},
            },
            "required": ["action", "query"]
        }
    }
}


def run(action: str, endpoint: str = "", query: str = "", 
       variables: str = "", headers: str = "") -> str:
    """Execute GraphQL."""
    if not endpoint:
        return "Error: endpoint URL required"
    
    header_dict = {"Content-Type": "application/json"}
    if headers:
        import json
        header_dict.update(json.loads(headers))
    
    # Add auth if token present
    token = os.getenv("GRAPHQL_TOKEN")
    if token:
        header_dict["Authorization"] = f"Bearer {token}"
    
    payload = {"query": query}
    if variables:
        import json
        payload["variables"] = json.loads(variables)
    
    try:
        resp = httpx.post(endpoint, json=payload, headers=header_dict, timeout=30)
        
        if resp.status_code == 200:
            result = resp.json()
            if result.get("errors"):
                return "Errors: " + str(result["errors"])
            return str(result.get("data", ""))[:500]
        return f"Error: {resp.status_code} - {resp.text[:200]}"
    
    except Exception as e:
        return f"Error: {str(e)}"


# Email draft
def email_draft(action: str = "", to: str = "", subject: str = "", 
               context: str = "") -> str:
    """Generate email drafts using AI."""
    if not to or not context:
        return "Error: to and context required"
    
    try:
        from core.provider import ProviderPool
        pool = ProviderPool()
        
        prompt = f"""Generate a professional email draft:

To: {to}
Subject: {subject}
Context/Purpose: {context}

Write a clear, professional email:"""
        
        response = pool.chat_with_retry([{"role": "user", "content": prompt}])
        return response["choices"][0]["message"]["content"]
    
    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    print("GraphQL and Email plugins loaded.")