from tools.base import BaseTool, ToolResult
import httpx
import os


PLUGIN_NAME = "linear"
PLUGIN_DESCRIPTION = "Manage Linear issues and projects"

LINEAR_SCHEMA = {
    "type": "function",
    "function": {
        "name": "linear",
        "description": "Create and manage Linear issues",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["list_issues", "create_issue", "get_issue", "update_issue", "list_projects"],
                    "description": "Linear action"
                },
                "team_id": {"type": "string", "description": "Team ID"},
                "project_id": {"type": "string", "description": "Project ID"},
                "title": {"type": "string", "description": "Issue title"},
                "description": {"type": "string", "description": "Issue description"},
                "priority": {"type": "number", "description": "Priority (0-4)"},
                "status": {"type": "string", "description": "Status (todo, in_progress, done)"},
                "issue_id": {"type": "string", "description": "Issue ID"},
                "assignee_id": {"type": "string", "description": "Assignee user ID"},
            },
            "required": ["action"]
        }
    }
}


def run(action: str, team_id: str = "", project_id: str = "", title: str = "",
      description: str = "", priority: int = 2, status: str = "", 
      issue_id: str = "", assignee_id: str = "") -> str:
    """Linear API operations."""
    token = os.getenv("LINEAR_API_KEY")
    if not token:
        return "Error: LINEAR_API_KEY not found"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    base_url = "https://api.linear.app/graphql"
    
    try:
        client = httpx.Client(timeout=30)
        
        if action == "list_projects":
            query = """
            query { teams { nodes { id name projects { nodes { id name } } } } }
            """
            resp = client.post(base_url, json={"query": query}, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                teams = data.get("data", {}).get("teams", {}).get("nodes", [])
                result = []
                for team in teams:
                    result.append(f"Team: {team.get('name')}")
                    for proj in team.get("projects", {}).get("nodes", []):
                        result.append(f"  • {proj.get('name')} ({proj.get('id')})")
                return "\n".join(result) if result else "No projects found"
            return f"Error: {resp.status_code}"
        
        elif action == "list_issues":
            query = """
            query Issues($teamId: ID!) {
                issues(filter: {team: {id: {eq: $teamId}}}) {
                    nodes { id title priority status assignee { name } }
                }
            }
            """
            vars = {"teamId": team_id} if team_id else {}
            resp = client.post(base_url, json={"query": query, "variables": vars}, headers=headers)
            if resp.status_code == 200:
                issues = resp.json().get("data", {}).get("issues", {}).get("nodes", [])
                result = [f"• [{i.get('priority')}] {i.get('id')} - {i.get('title')}" for i in issues[:10]]
                return "\n".join(result) if result else "No issues found"
            return f"Error: {resp.status_code}"
        
        elif action == "create_issue":
            if not team_id or not title:
                return "Error: team_id and title required"
            
            mutation = """
            mutation CreateIssue($input: IssueCreateInput!) {
                issueCreate(input: $input) { success issue { id title } }
            }
            """
            input_data = {"teamId": team_id, "title": title}
            if description:
                input_data["description"] = description
            if priority is not None:
                input_data["priority"] = priority
            
            resp = client.post(base_url, json={"query": mutation, "variables": {"input": input_data}}, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                issue = data.get("data", {}).get("issueCreate", {}).get("issue", {})
                return f"✓ Issue created: {issue.get('id')} - {issue.get('title')}"
            return f"Error: {resp.status_code}"
        
        elif action == "get_issue":
            if not issue_id:
                return "Error: issue_id required"
            
            query = """
            query Issue($id: String!) {
                issue(id: $id) { id title description priority status assignee { name } }
            }
            """
            resp = client.post(base_url, json={"query": query, "variables": {"id": issue_id}}, headers=headers)
            if resp.status_code == 200:
                issue = resp.json().get("data", {}).get("issue", {})
                return f"{issue.get('id')}: {issue.get('title')}\nStatus: {issue.get('status')}\nPriority: {issue.get('priority')}"
            return f"Error: {resp.status_code}"
        
        elif action == "update_issue":
            if not issue_id:
                return "Error: issue_id required"
            
            mutation = """
            mutation UpdateIssue($id: String!, $input: IssueUpdateInput!) {
                issueUpdate(id: $id, input: $input) { success }
            }
            """
            update_input = {}
            if status:
                update_input["state"] = status
            if priority is not None:
                update_input["priority"] = priority
            
            resp = client.post(base_url, json={
                "query": mutation, 
                "variables": {"id": issue_id, "input": update_input}
            }, headers=headers)
            if resp.status_code == 200:
                return f"✓ Issue {issue_id} updated"
            return f"Error: {resp.status_code}"
        
        else:
            return f"Error: Unknown action {action}"
    
    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    print("Linear plugin loaded.")