from tools.base import BaseTool, ToolResult
import httpx
import os
import json
import base64


PLUGIN_NAME = "gmail"
PLUGIN_DESCRIPTION = "Send emails and manage Gmail"

GMAIL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "gmail",
        "description": "Send emails and manage Gmail messages",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["send_email", "list_emails", "get_email", "search_emails", "get_labels"],
                    "description": "The Gmail action to perform"
                },
                "to": {"type": "string", "description": "Recipient email address"},
                "subject": {"type": "string", "description": "Email subject"},
                "body": {"type": "string", "description": "Email body content"},
                "cc": {"type": "string", "description": "CC recipients (comma separated)"},
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "number", "description": "Number of results (default 10)"},
                "label": {"type": "string", "description": "Label name or ID"},
            },
            "required": ["action"]
        }
    }
}


def get_gmail_credentials() -> str:
    """Get Gmail OAuth token from environment."""
    return os.getenv("GMAIL_OAUTH_TOKEN") or os.getenv("GMAIL_TOKEN")


def encode_email(sender: str, to: str, subject: str, body: str, cc: str = "") -> str:
    """Encode email to RFC 2822 format."""
    message = f"From: {sender}\nTo: {to}\n"
    if cc:
        message += f"Cc: {cc}\n"
    message += f"Subject: {subject}\n\n{body}"
    return base64.urlsafe_b64encode(message.encode()).decode()


def run(action: str, to: str = "", subject: str = "", body: str = "", cc: str = "", 
       query: str = "", max_results: int = 10, label: str = "") -> str:
    """Execute Gmail API actions."""
    token = get_gmail_credentials()
    if not token:
        return "Error: Gmail token not found. Set GMAIL_OAUTH_TOKEN."
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    base_url = "https://gmail.googleapis.com/gmail/v1/users/me"
    
    try:
        client = httpx.Client(timeout=30)
        
        if action == "get_labels":
            resp = client.get(f"{base_url}/labels", headers=headers)
            if resp.status_code == 200:
                labels = resp.json().get("labels", [])
                result = []
                for l in labels:
                    result.append(f"• {l.get('name')} [{l.get('type', 'N/A')}]")
                return "\n".join(result) if result else "No labels found."
            return f"Error: {resp.status_code} - {resp.text[:200]}"
        
        elif action == "send_email":
            if not to or not subject or not body:
                return "Error: to, subject, and body required for send_email"
            
            # Get user info for sender
            user_resp = client.get(f"{base_url}/profile", headers=headers)
            if user_resp.status_code != 200:
                return "Error: Could not get user profile."
            
            sender = user_resp.json().get("emailAddress", "me")
            
            # Create email
            email = f"From: {sender}\nTo: {to}\n"
            if cc:
                email += f"Cc: {cc}\n"
            email += f"Subject: {subject}\nContent-Type: text/plain; charset=utf-8\n\n{body}"
            
            encoded = base64.urlsafe_b64encode(email.encode()).decode().replace("+", "-").replace("/", "_")
            
            payload = {"raw": encoded}
            resp = client.post(f"{base_url}/messages/send", headers=headers, json=payload)
            if resp.status_code == 200:
                msg = resp.json()
                return f"Email sent! :white_check_mark:\nID: {msg.get('id')}"
            return f"Error: {resp.status_code} - {resp.text[:200]}"
        
        elif action == "list_emails":
            # Build query
            q = query or "in:inbox"
            if label:
                q = f"label:{label}"
            
            resp = client.get(f"{base_url}/messages", headers=headers, params={"maxResults": max_results, "q": q})
            if resp.status_code == 200:
                messages = resp.json().get("messages", [])
                result = []
                for m in messages[:max_results]:
                    result.append(f"• {m.get('id', 'N/A')}")
                return "\n".join(result) if result else "No emails found."
            return f"Error: {resp.status_code} - {resp.text[:200]}"
        
        elif action == "search_emails":
            if not query:
                return "Error: query required for search_emails"
            
            resp = client.get(f"{base_url}/messages", headers=headers, params={"maxResults": max_results, "q": query})
            if resp.status_code == 200:
                messages = resp.json().get("messages", [])
                result = []
                for m in messages[:max_results]:
                    result.append(f"• {m.get('id', 'N/A')}")
                return "\n".join(result) if result else "No emails found."
            return f"Error: {resp.status_code} - {resp.text[:200]}"
        
        elif action == "get_email":
            if not query:
                return "Error: message ID required for get_email (use query param)"
            
            # Assume query is the message ID
            resp = client.get(f"{base_url}/messages/{query}", headers=headers)
            if resp.status_code == 200:
                msg = resp.json()
                headers_dict = msg.get("payload", {}).get("headers", {})
                
                # Get headers
                subject = next((h.get("value", "") for h in headers_dict if h.get("name", "").lower() == "subject"), "No Subject")
                from_addr = next((h.get("value", "") for h in headers_dict if h.get("name", "").lower() == "from"), "Unknown")
                date = next((h.get("value", "") for h in headers_dict if h.get("name", "").lower() == "date"), "Unknown")
                
                return f"From: {from_addr}\nSubject: {subject}\nDate: {date}\nID: {msg.get('id')}"
            return f"Error: {resp.status_code} - {resp.text[:200]}"
        
        else:
            return f"Error: Unknown action '{action}'. Available: send_email, list_emails, get_email, search_emails, get_labels"
    
    except httpx.TimeoutException:
        return "Error: Request timed out after 30 seconds."
    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    print("Gmail plugin loaded. Use 'gmail' tool in HelloChusquis.")