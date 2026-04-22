from tools.base import BaseTool, ToolResult
import httpx
import json


class GitHubTool(BaseTool):
    name = "github"
    description = "Interact with GitHub API - manage repos, issues, PRs, and more"

    def run(self, action: str = "", owner: str = "", repo: str = "", title: str = "", body: str = "", 
          state: str = "open", base: str = "main", head: str = "", query: str = "", 
          per_page: int = 10) -> ToolResult:
        try:
            # Code from original run function here
            token = os.getenv("GITHUB_TOKEN") or os.getenv("GITHUB_API_TOKEN") or os.getenv("GH_TOKEN")
            if not token:
                return ToolResult(success=False, output="", error="No GitHub token found. Set GITHUB_TOKEN, GITHUB_API_TOKEN, or GH_TOKEN")
            
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
                "X-GitHub-Api-Version": "2022-11-28"
            }
            
            base_url = "https://api.github.com"
            client = httpx.Client(timeout=30)
            
            if action == "get_user":
                resp = client.get(f"{base_url}/user", headers=headers)
                if resp.status_code == 200:
                    user = resp.json()
                    return ToolResult(success=True, output=f"User: {user.get('login')}\nName: {user.get('name')}\nBio: {user.get('bio')}\nRepos: {user.get('public_repos')}")
                return ToolResult(success=False, output="", error=f"Error: {resp.status_code}")
            
            # ... más acciones aquí
            
            return ToolResult(success=False, output="", error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))


# Legacy functions for compatibility
PLUGIN_NAME = "github"
PLUGIN_DESCRIPTION = "Interact with GitHub API - manage repos, issues, PRs, and more"

GITHUB_SCHEMA = {
    "type": "function",
    "function": {
        "name": "github",
        "description": "Perform GitHub operations like listing repos, getting issues, creating PRs, etc.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["list_repos", "get_repo", "list_issues", "create_issue", "list_pulls", "create_pr", "get_user", "search_repos"],
                    "description": "The GitHub action to perform"
                },
                "owner": {"type": "string", "description": "Repository owner (required for most actions)"},
                "repo": {"type": "string", "description": "Repository name (required for repo-related actions)"},
                "title": {"type": "string", "description": "Title for issues or PRs"},
                "body": {"type": "string", "description": "Body content for issues or PRs"},
                "state": {"type": "string", "enum": ["open", "closed"], "description": "State for issues or PRs"},
                "base": {"type": "string", "description": "Base branch for PR"},
                "head": {"type": "string", "description": "Head branch for PR"},
                "query": {"type": "string", "description": "Search query for repos"},
                "per_page": {"type": "number", "description": "Number of results per page (default 10)"},
            }
        },
        "required": ["action"]
    }
}


def get_github_token() -> str:
    """Get GitHub token from environment or config."""
    import os
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        token = os.getenv("GITHUB_API_TOKEN")
    if not token:
        token = os.getenv("GH_TOKEN")
    return token


def run(action: str, owner: str = "", repo: str = "", title: str = "", body: str = "", 
       state: str = "open", base: str = "main", head: str = "", query: str = "", 
       per_page: int = 10) -> str:
    """Execute GitHub API actions."""
    token = get_github_token()
    if not token:
        return "Error: No GitHub token found. Set GITHUB_TOKEN, GITHUB_API_TOKEN, or GH_TOKEN environment variable."
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    base_url = "https://api.github.com"
    
    try:
        client = httpx.Client(timeout=30)
        
        if action == "get_user":
            resp = client.get(f"{base_url}/user", headers=headers)
            if resp.status_code == 200:
                user = resp.json()
                return f"User: {user.get('login')}\nName: {user.get('name')}\nBio: {user.get('bio')}\nRepos: {user.get('public_repos')}"
            return f"Error: {resp.status_code} - {resp.text}"
        
        elif action == "list_repos":
            url = f"{base_url}/user/repos?per_page={per_page}&sort=updated"
            if query:
                url = f"{base_url}/search/repos?q={query}&per_page={per_page}"
            resp = client.get(url, headers=headers)
            if resp.status_code == 200:
                repos = resp.json().get("items" if query else "respositories", [])[:per_page]
                if not repos:
                    repos = resp.json().get("respositories", [])
                result = []
                for r in repos:
                    result.append(f"• {r.get('full_name')} - ⭐{r.get('stargazers_count', 0)} | {r.get('language', 'N/A')}")
                return "\n".join(result) if result else "No repositories found."
            return f"Error: {resp.status_code} - {resp.text}"
        
        elif action == "get_repo":
            if not owner or not repo:
                return "Error: owner and repo required for get_repo"
            resp = client.get(f"{base_url}/repos/{owner}/{repo}", headers=headers)
            if resp.status_code == 200:
                r = resp.json()
                return f"{r.get('full_name')}\nDescription: {r.get('description')}\nStars: {r.get('stargazers_count')}\nForks: {r.get('forks_count')}\nLanguage: {r.get('language')}\nURL: {r.get('html_url')}"
            return f"Error: {resp.status_code} - {resp.text}"
        
        elif action == "list_issues":
            if not owner or not repo:
                return "Error: owner and repo required for list_issues"
            resp = client.get(f"{base_url}/repos/{owner}/{repo}/issues?state=all&per_page={per_page}", headers=headers)
            if resp.status_code == 200:
                issues = resp.json()
                result = []
                for issue in issues:
                    if "pull_request" not in issue:  # Skip PRs
                        result.append(f"• #{issue.get('number')} [{issue.get('state')}] {issue.get('title')} (by {issue.get('user', {}).get('login')})")
                return "\n".join(result) if result else "No issues found."
            return f"Error: {resp.status_code} - {resp.text}"
        
        elif action == "create_issue":
            if not owner or not repo or not title:
                return "Error: owner, repo, and title required for create_issue"
            data = {"title": title}
            if body:
                data["body"] = body
            resp = client.post(f"{base_url}/repos/{owner}/{repo}/issues", headers=headers, json=data)
            if resp.status_code == 201:
                issue = resp.json()
                return f"Issue created: #{issue.get('number')} - {issue.get('title')}\n{issue.get('html_url')}"
            return f"Error: {resp.status_code} - {resp.text}"
        
        elif action == "list_pulls":
            if not owner or not repo:
                return "Error: owner and repo required for list_pulls"
            resp = client.get(f"{base_url}/repos/{owner}/{repo}/pulls?state=all&per_page={per_page}", headers=headers)
            if resp.status_code == 200:
                pulls = resp.json()
                result = []
                for pr in pulls:
                    result.append(f"• #{pr.get('number')} [{pr.get('state')}] {pr.get('title')} -> {pr.get('base', {}).get('ref')}")
                return "\n".join(result) if result else "No pull requests found."
            return f"Error: {resp.status_code} - {resp.text}"
        
        elif action == "create_pr":
            if not owner or not repo or not title or not head or not base:
                return "Error: owner, repo, title, head, and base required for create_pr"
            if not body:
                body = f"Created via HelloChusquis"
            data = {"title": title, "body": body, "base": base, "head": head}
            resp = client.post(f"{base_url}/repos/{owner}/{repo}/pulls", headers=headers, json=data)
            if resp.status_code == 201:
                pr = resp.json()
                return f"PR created: #{pr.get('number')} - {pr.get('title')}\n{pr.get('html_url')}"
            return f"Error: {resp.status_code} - {resp.text}"
        
        elif action == "search_repos":
            if not query:
                return "Error: query required for search_repos"
            resp = client.get(f"{base_url}/search/repos?q={query}&per_page={per_page}", headers=headers)
            if resp.status_code == 200:
                repos = resp.json().get("items", [])[:per_page]
                result = []
                for r in repos:
                    result.append(f"• {r.get('full_name')} - ⭐{r.get('stargazers_count', 0)} | {r.get('language', 'N/A')}")
                return "\n".join(result) if result else "No repositories found."
            return f"Error: {resp.status_code} - {resp.text}"
        
        else:
            return f"Error: Unknown action '{action}'. Available: list_repos, get_repo, list_issues, create_issue, list_pulls, create_pr, get_user, search_repos"
    
    except httpx.TimeoutException:
        return "Error: Request timed out after 30 seconds."
    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    # Quick test
    print("GitHub plugin loaded. Use 'github' tool in HelloChusquis.")