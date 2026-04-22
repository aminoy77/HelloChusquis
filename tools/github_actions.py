from tools.base import BaseTool, ToolResult
import httpx
import os


PLUGIN_NAME = "github_actions"
PLUGIN_DESCRIPTION = "Run and manage GitHub Actions workflows"

GITHUB_ACTIONS_SCHEMA = {
    "type": "function",
    "function": {
        "name": "github_actions",
        "description": "Trigger and monitor GitHub Actions workflows",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["list_workflows", "run_workflow", "list_runs", "get_run", "cancel_run"],
                    "description": "GitHub Actions action"
                },
                "owner": {"type": "string", "description": "Repository owner"},
                "repo": {"type": "string", "description": "Repository name"},
                "workflow": {"type": "string", "description": "Workflow file or ID"},
                "ref": {"type": "string", "description": "Git ref (branch, tag, commit)"},
                "run_id": {"type": "number", "description": "Run ID"},
                "inputs": {"type": "string", "description": "Workflow inputs (JSON)"},
            },
            "required": ["action", "owner", "repo"]
        }
    }
}


def get_token() -> str:
    return os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")


def run(action: str, owner: str = "", repo: str = "", workflow: str = "", 
      ref: str = "main", run_id: int = 0, inputs: str = "") -> str:
    """GitHub Actions operations."""
    token = get_token()
    if not token:
        return "Error: GITHUB_TOKEN not set"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    base_url = f"https://api.github.com/repos/{owner}/{repo}"
    
    try:
        client = httpx.Client(timeout=30)
        
        if action == "list_workflows":
            resp = client.get(f"{base_url}/actions/workflows", headers=headers)
            if resp.status_code == 200:
                workflows = resp.json().get("workflows", [])
                result = ["Workflows:"]
                for w in workflows:
                    result.append(f"• {w.get('name')} (id: {w.get('id')}) - {w.get('state')}")
                return "\n".join(result)
            return f"Error: {resp.status_code}"
        
        elif action == "run_workflow":
            if not workflow:
                return "Error: workflow name or ID required"
            
            data = {"ref": ref}
            if inputs:
                data["inputs"] = {"data": inputs}
            
            resp = client.post(
                f"{base_url}/actions/workflows/{workflow}/dispatches",
                headers=headers,
                json=data
            )
            if resp.status_code == 204:
                return f"✓ Triggered workflow '{workflow}' on {ref}"
            return f"Error: {resp.status_code}"
        
        elif action == "list_runs":
            resp = client.get(f"{base_url}/actions/runs", headers=headers)
            if resp.status_code == 200:
                runs = resp.json().get("workflow_runs", [])[:10]
                result = ["Recent runs:"]
                for r in runs:
                    status = r.get("status", "")
                    conclusion = r.get("conclusion", "")
                    result.append(f"• {r.get('name')} - {status}/{conclusion} - {r.get('created_at', '')[:10]}")
                return "\n".join(result)
            return f"Error: {resp.status_code}"
        
        elif action == "get_run":
            if not run_id:
                return "Error: run_id required"
            
            resp = client.get(f"{base_url}/actions/runs/{run_id}", headers=headers)
            if resp.status_code == 200:
                r = resp.json()
                return f"Run #{run_id}\nStatus: {r.get('status')}\nConclusion: {r.get('conclusion')}\nJobs: {r.get('jobs_url', '')[:50]}..."
            return f"Error: {resp.status_code}"
        
        elif action == "cancel_run":
            if not run_id:
                return "Error: run_id required"
            
            resp = client.post(f"{base_url}/actions/runs/{run_id}/cancel", headers=headers)
            if resp.status_code == 204:
                return f"✓ Cancelled run #{run_id}"
            return f"Error: {resp.status_code}"
        
        else:
            return f"Error: Unknown action {action}"
    
    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    print("GitHub Actions plugin loaded.")