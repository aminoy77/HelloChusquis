"""Safe Linear GraphQL helpers with parameterized external values."""

from __future__ import annotations

from httpx import AsyncClient

_URL = "https://api.linear.app/graphql"


def _create_workspace_payload(name: str) -> dict:
    return {
        "query": "mutation ($name: String!) { createWorkspace(input: { name: $name }) { success workspace { id } } }",
        "variables": {"name": str(name)},
    }


async def _post(api_key: str, payload: dict) -> dict:
    async with AsyncClient(timeout=30, follow_redirects=False) as client:
        response = await client.post(_URL, json=payload, headers={"Authorization": api_key})
        response.raise_for_status()
        return response.json()


async def create_workspace(name: str, api_key: str) -> dict:
    """Create a Linear workspace with a parameterized mutation."""
    return await _post(api_key, _create_workspace_payload(name))


async def list_issues(api_key: str, team_id: str | None = None) -> dict:
    """List issues, optionally filtered by a team variable."""
    query = "query ($teamId: ID) { issues(filter: { team: { id: { eq: $teamId } } }) { nodes { id title state } } }" if team_id else "{ issues { nodes { id title state } } }"
    return await _post(api_key, {"query": query, "variables": {"teamId": str(team_id)} if team_id else {}})


async def create_issue(api_key: str, title: str, team_id: str, **kwargs) -> dict:
    """Create a Linear issue using input variables."""
    payload = {
        "query": "mutation ($title: String!, $teamId: ID!) { createIssue(input: { title: $title, teamId: $teamId }) { success issue { id } } }",
        "variables": {"title": str(title), "teamId": str(team_id)},
    }
    return await _post(api_key, payload)


async def get_issue(api_key: str, issue_id: str) -> dict:
    """Get an issue using a GraphQL variable."""
    return await _post(api_key, {"query": "query ($id: String!) { issue(id: $id) { id title description } }", "variables": {"id": str(issue_id)}})


async def update_issue(api_key: str, issue_id: str, **kwargs) -> dict:
    """Update an issue using variable-based update input."""
    payload = {
        "query": "mutation ($id: String!, $input: IssueUpdateInput!) { updateIssue(id: $id, input: $input) { success issue { id } } }",
        "variables": {"id": str(issue_id), "input": kwargs},
    }
    return await _post(api_key, payload)
