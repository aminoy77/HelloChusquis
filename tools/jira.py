from tools.base import BaseTool, ToolResult
import httpx
import os


PLUGIN_NAME = "jira"
PLUGIN_DESCRIPTION = "Interact with Jira issues and projects"

JIRA_SCHEMA = {
    "type": "function",
    "function": {
        "name": "jira",
        "description": "Create issues, search, and manage Jira",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["create_issue", "search_issues", "get_issue", "assign_issue", "add_comment", "list_projects", "list_transitions"],
                    "description": "The Jira action to perform"
                },
                "project": {"type": "string", "description": "Project key (e.g., PROJ)"},
                "issue_key": {"type": "string", "description": "Issue key (e.g., PROJ-123)"},
                "summary": {"type": "string", "description": "Issue summary"},
                "description": {"type": "string", "description": "Issue description"},
                "issue_type": {"type": "string", "description": "Issue type (Bug, Task, Story, etc.)"},
                "assignee": {"type": "string", "description": "Assignee username"},
                "comment": {"type": "string", "description": "Comment text"},
                "query": {"type": "string", "description": "JQL search query"},
                "max_results": {"type": "number", "description": "Number of results (default 10)"},
            },
            "required": ["action"]
        }
    }
}


def get_jira_credentials() -> dict:
    """Get Jira credentials from environment."""
    return {
        "url": os.getenv("JIRA_URL"),
        "email": os.getenv("JIRA_EMAIL"),
        "token": os.getenv("JIRA_TOKEN") or os.getenv("JIRA_API_TOKEN"),
    }


def run(action: str, project: str = "", issue_key: str = "", summary: str = "", 
       description: str = "", issue_type: str = "Task", assignee: str = "", 
       comment: str = "", query: str = "", max_results: int = 10) -> str:
    """Execute Jira API actions."""
    creds = get_jira_credentials()
    
    if not creds["url"] or not creds["email"] or not creds["token"]:
        return "Error: Jira credentials not found. Set JIRA_URL, JIRA_EMAIL, and JIRA_TOKEN."
    
    base_url = creds["url"].rstrip("/")
    auth = (creds["email"], creds["token"])
    headers = {"Content-Type": "application/json"}
    
    try:
        client = httpx.Client(timeout=30, auth=auth)
        
        if action == "list_projects":
            resp = client.get(f"{base_url}/rest/api/3/project", headers=headers)
            if resp.status_code == 200:
                projects = resp.json()
                result = []
                for p in projects:
                    result.append(f"• {p.get('key')} - {p.get('name', 'N/A')}")
                return "\n".join(result) if result else "No projects found."
            return f"Error: {resp.status_code} - {resp.text[:200]}"
        
        elif action == "create_issue":
            if not project or not summary:
                return "Error: project and summary required for create_issue"
            
            payload = {
                "fields": {
                    "project": {"key": project},
                    "summary": summary,
                    "description": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": description or summary}]}]},
                    "issuetype": {"name": issue_type}
                }
            }
            
            resp = client.post(f"{base_url}/rest/api/3/issue", headers=headers, json=payload)
            if resp.status_code == 201:
                issue = resp.json()
                key = issue.get("key")
                return f"Issue created! :white_check_mark:\n{key}\n{base_url}/browse/{key}"
            return f"Error: {resp.status_code} - {resp.text[:200]}"
        
        elif action == "get_issue":
            if not issue_key:
                return "Error: issue_key required for get_issue"
            
            resp = client.get(f"{base_url}/rest/api/3/issue/{issue_key}", headers=headers)
            if resp.status_code == 200:
                issue = resp.json()
                fields = issue.get("fields", {})
                return f"{issue_key}: {fields.get('summary')}\nStatus: {fields.get('status', {}).get('name')}\nType: {fields.get('issuetype', {}).get('name')}\nAssignee: {fields.get('assignee', {}).get('displayName', 'Unassigned')}\nURL: {base_url}/browse/{issue_key}"
            return f"Error: {resp.status_code} - {resp.text[:200]}"
        
        elif action == "assign_issue":
            if not issue_key or not assignee:
                return "Error: issue_key and assignee required for assign_issue"
            
            # Get accountId for assignee
            search_resp = client.get(f"{base_url}/rest/api/3/user/search?query={assignee}", headers=headers)
            if search_resp.status_code != 200:
                return f"Error: Could not find user: {assignee}"
            
            users = search_resp.json()
            if not users:
                return f"Error: User '{assignee}' not found."
            
            account_id = users[0].get("accountId")
            
            payload = {"name": assignee, "accountId": account_id}
            resp = client.put(f"{base_url}/rest/api/3/issue/{issue_key}/assignee", headers=headers, json=payload)
            if resp.status_code == 204 or resp.status_code == 200:
                return f"Issue {issue_key} assigned to {assignee}! :white_check_mark:"
            return f"Error: {resp.status_code} - {resp.text[:200]}"
        
        elif action == "add_comment":
            if not issue_key or not comment:
                return "Error: issue_key and comment required for add_comment"
            
            payload = {"body": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": comment}]}]}}
            resp = client.post(f"{base_url}/rest/api/3/issue/{issue_key}/comment", headers=headers, json=payload)
            if resp.status_code == 201:
                return f"Comment added to {issue_key}! :white_check_mark:"
            return f"Error: {resp.status_code} - {resp.text[:200]}"
        
        elif action == "search_issues":
            jql = query or f"project = {project} ORDER BY created DESC"
            if not query and not project:
                jql = " ORDER BY created DESC"
            
            resp = client.get(f"{base_url}/rest/api/3/search", headers=headers, params={"jql": jql, "maxResults": max_results})
            if resp.status_code == 200:
                issues = resp.json().get("issues", [])
                result = []
                for i in issues:
                    fields = i.get("fields", {})
                    result.append(f"• {i.get('key')}: {fields.get('summary', 'N/A')[:50]} [{fields.get('status', {}).get('name', 'N/A')}]")
                return "\n".join(result) if result else "No issues found."
            return f"Error: {resp.status_code} - {resp.text[:200]}"
        
        elif action == "list_transitions":
            if not issue_key:
                return "Error: issue_key required for list_transitions"
            
            resp = client.get(f"{base_url}/rest/api/3/issue/{issue_key}/transitions", headers=headers)
            if resp.status_code == 200:
                transitions = resp.json().get("transitions", [])
                result = []
                for t in transitions:
                    result.append(f"→ {t.get('name', 'N/A')} ({t.get('to', {}).get('name', 'N/A')})")
                return "\n".join(result) if result else "No transitions available."
            return f"Error: {resp.status_code} - {resp.text[:200]}"
        
        else:
            return f"Error: Unknown action '{action}'. Available: create_issue, search_issues, get_issue, assign_issue, add_comment, list_projects, list_transitions"
    
    except httpx.TimeoutException:
        return "Error: Request timed out after 30 seconds."
    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    print("Jira plugin loaded. Use 'jira' tool in HelloChusquis.")