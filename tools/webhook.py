from tools.base import BaseTool, ToolResult
import httpx
import os
import json


PLUGIN_NAME = "webhook"
PLUGIN_DESCRIPTION = "Receive and manage webhooks"

WEBHOOK_SCHEMA = {
    "type": "function",
    "function": {
        "name": "webhook",
        "description": "Create webhook listener or trigger webhooks",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["send", "list"],
                    "description": "Webhook action"
                },
                "url": {"type": "string", "description": "Webhook URL"},
                "payload": {"type": "string", "description": "JSON payload to send"},
                "method": {"type": "string", "description": "HTTP method"},
                "headers": {"type": "string", "description": "Custom headers (JSON)"},
            },
            "required": ["action"]
        }
    }
}


def run(action: str, url: str = "", payload: str = "{}", 
      method: str = "POST", headers: str = "") -> str:
    """Send webhooks."""
    if action == "send":
        if not url:
            return "Error: url required"
        
        try:
            payload_json = json.loads(payload)
        except:
            payload_json = {"message": payload}
        
        header_dict = {"Content-Type": "application/json"}
        if headers:
            header_dict.update(json.loads(headers))
        
        try:
            resp = httpx.request(method, url, json=payload_json, headers=header_dict, timeout=30)
            return f"Sent to {url}\nStatus: {resp.status_code}\nResponse: {resp.text[:200]}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    elif action == "list":
        return "Webhooks configured in hellochusquis.yaml"
    
    else:
        return f"Error: Unknown action {action}"


if __name__ == "__main__":
    print("Webhook plugin loaded.")