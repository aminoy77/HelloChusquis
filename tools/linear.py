from httpx import AsyncClient


async def create_workspace(name: str, api_key: str) -> dict:
    """Create Linear workspace."""
    url = "https://api.linear.app/graphql"
    async with AsyncClient() as client:
        r = await client.post(url, json={"query": f'mmutation {{ createWorkspace(input: {{ name: "{name}" }}) {{ id }} }}'}, headers={"Authorization": api_key})
        return r.json()


async def list_issues(api_key: str, team_id: str = None) -> dict:
    """List Linear issues."""
    url = "https://api.linear.app/graphql"
    async with AsyncClient() as client:
        r = await client.post(url, json={"query": "{ issues { nodes { id title state } } }"}, headers={"Authorization": api_key})
        return r.json()


async def create_issue(api_key: str, title: str, team_id: str, **kwargs) -> dict:
    """Create Linear issue."""
    url = "https://api.linear.app/graphql"
    query = f'mutation {{ createIssue(input: {{ title: "{title}", teamId: "{team_id}" }}) {{ id }} }}'
    async with AsyncClient() as client:
        r = await client.post(url, json={"query": query}, headers={"Authorization": api_key})
        return r.json()


async def get_issue(api_key: str, issue_id: str) -> dict:
    """Get Linear issue."""
    url = "https://api.linear.app/graphql"
    async with AsyncClient() as client:
        r = await client.post(url, json={"query": f'{{ issue(id: "{issue_id}") {{ id title description }} }}'}, headers={"Authorization": api_key})
        return r.json()


async def update_issue(api_key: str, issue_id: str, **kwargs) -> dict:
    """Update Linear issue."""
    url = "https://api.linear.app/graphql"
    async with AsyncClient() as client:
        r = await client.post(url, json={"query": f'mutation {{ updateIssue(id: "{issue_id}") {{ id }} }}'}, headers={"Authorization": api_key})
        return r.json()