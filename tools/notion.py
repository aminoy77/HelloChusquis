from tools.base import BaseTool, ToolResult
import httpx
import os
import json


PLUGIN_NAME = "notion"
PLUGIN_DESCRIPTION = "Interact with Notion workspaces - create pages, update databases, query data"

NOTION_SCHEMA = {
    "type": "function",
    "function": {
        "name": "notion",
        "description": "Perform Notion operations like creating pages, querying databases, etc.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["create_page", "update_page", "query_database", "list_databases", "get_page", "append_block"],
                    "description": "The Notion action to perform"
                },
                "page_id": {"type": "string", "description": "Page ID (UUID format)"},
                "database_id": {"type": "string", "description": "Database ID (UUID format)"},
                "title": {"type": "string", "description": "Page title"},
                "content": {"type": "string", "description": "Page content or query filter"},
                "properties": {"type": "string", "description": "JSON properties for new page"},
                "icon": {"type": "string", "description": "Page icon (emoji)"},
                "block_id": {"type": "string", "description": "Block ID to append to"},
                "children": {"type": "number", "description": "Number of results (default 10)"},
            },
            "required": ["action"]
        }
    }
}


def get_notion_token() -> str:
    """Get Notion token from environment."""
    return os.getenv("NOTION_TOKEN") or os.getenv("NOTION_API_KEY")


def run(action: str, page_id: str = "", database_id: str = "", title: str = "", 
       content: str = "", properties: str = "", icon: str = "📝", 
       block_id: str = "", children: int = 10) -> str:
    """Execute Notion API actions."""
    token = get_notion_token()
    if not token:
        return "Error: No Notion token found. Set NOTION_TOKEN or NOTION_API_KEY environment variable."
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    base_url = "https://api.notion.com/v1"
    
    try:
        client = httpx.Client(timeout=30)
        
        if action == "list_databases":
            resp = client.get(f"{base_url}/databases", headers=headers)
            if resp.status_code == 200:
                dbs = resp.json().get("results", [])[:10]
                result = []
                for db in dbs:
                    title_obj = db.get("title", [])
                    db_title = ""
                    if title_obj and isinstance(title_obj, list):
                        db_title = "".join([t.get("plain_text", "") for t in title_obj])
                    result.append(f"• {db_title or db.get('id', 'N/A')} ({db.get('id', 'N/A')})")
                return "\n".join(result) if result else "No databases found."
            return f"Error: {resp.status_code} - {resp.text}"
        
        elif action == "get_page":
            if not page_id:
                return "Error: page_id required for get_page"
            page_id = page_id.replace("-", "")
            resp = client.get(f"{base_url}/pages/{page_id}", headers=headers)
            if resp.status_code == 200:
                page = resp.json()
                title_obj = page.get("properties", {})
                return f"Page: {page.get('id', 'N/A')}\nLast edited: {page.get('last_edited_time', 'N/A')}"
            return f"Error: {resp.status_code} - {resp.text}"
        
        elif action == "create_page":
            if not database_id or not title:
                return "Error: database_id and title required for create_page"
            
            database_id = database_id.replace("-", "")
            
            # Build page properties
            page_properties = {
                "Name": {
                    "title": [{"text": {"content": title}}]
                }
            }
            
            # Parse custom properties if provided
            if properties:
                try:
                    page_properties = json.loads(properties)
                except:
                    pass
            
            payload = {
                "parent": {"database_id": database_id},
                "properties": page_properties,
                "icon": {"emoji": icon}
            }
            
            resp = client.post(f"{base_url}/pages", headers=headers, json=payload)
            if resp.status_code == 200:
                page = resp.json()
                return f"Page created! :white_check_mark:\nID: {page.get('id', 'N/A')}\nURL: https://notion.so/{page.get('id', '').replace('-', '')}"
            return f"Error: {resp.status_code} - {resp.text}"
        
        elif action == "update_page":
            if not page_id:
                return "Error: page_id required for update_page"
            
            page_id = page_id.replace("-", "")
            
            payload = {}
            if content:
                payload = {
                    "children": [
                        {
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [{"text": {"content": {"content": content}}}]
                            }
                        }
                    ]
                }
            
            resp = client.patch(f"{base_url}/blocks/{page_id}/children", headers=headers, json=payload)
            if resp.status_code == 200:
                return f"Page updated! :white_check_mark:"
            return f"Error: {resp.status_code} - {resp.text}"
        
        elif action == "query_database":
            if not database_id:
                return "Error: database_id required for query_database"
            
            database_id = database_id.replace("-", "")
            
            payload = {}
            if content:
                try:
                    payload = json.loads(content)  # Filter/sort
                except:
                    payload = {}
            
            resp = client.post(f"{base_url}/databases/{database_id}/query", headers=headers, json=payload)
            if resp.status_code == 200:
                results = resp.json().get("results", [])[:children]
                result = []
                for r in results:
                    # Try to get title
                    props = r.get("properties", {})
                    page_title = "Untitled"
                    for key, val in props.items():
                        if val.get("type") == "title":
                            title_arr = val.get("title", [])
                            if title_arr:
                                page_title = title_arr[0].get("plain_text", "Untitled")
                                break
                    result.append(f"• {page_title}")
                return "\n".join(result) if result else "No results found."
            return f"Error: {resp.status_code} - {resp.text}"
        
        elif action == "append_block":
            if not block_id or not content:
                return "Error: block_id and content required for append_block"
            
            block_id = block_id.replace("-", "")
            
            payload = {
                "children": [
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"text": {"content": {"content": content}}}]
                        }
                    }
                ]
            }
            
            resp = client.patch(f"{base_url}/blocks/{block_id}/children", headers=headers, json=payload)
            if resp.status_code == 200:
                return f"Block appended! :white_check_mark:"
            return f"Error: {resp.status_code} - {resp.text}"
        
        else:
            return f"Error: Unknown action '{action}'. Available: create_page, update_page, query_database, list_databases, get_page, append_block"
    
    except httpx.TimeoutException:
        return "Error: Request timed out after 30 seconds."
    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    print("Notion plugin loaded. Use 'notion' tool in HelloChusquis.")