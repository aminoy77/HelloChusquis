from httpx import AsyncClient


async def run_action(repository: str, workflow_id: str, ref: str, inputs: dict, token: str) -> dict:
    """Run GitHub Actions workflow."""
    url = f"https://api.github.com/repos/{repository}/actions/workflows/{workflow_id}/dispatches"
    async with AsyncClient() as client:
        r = await client.post(url, json={"ref": ref, "inputs": inputs}, headers={"Authorization": f"Bearer {token}"})
        return {"status": "dispatched"}


async def list_workflows(repository: str, token: str) -> dict:
    """List GitHub Actions workflows."""
    url = f"https://api.github.com/repos/{repository}/actions/workflows"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {token}"})
        return r.json()


async def get_workflow_run(repository: str, run_id: int, token: str) -> dict:
    """Get workflow run."""
    url = f"https://api.github.com/repos/{repository}/actions/runs/{run_id}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {token}"})
        return r.json()


async def list_runs(repository: str, workflow_id: str, token: str) -> dict:
    """List workflow runs."""
    url = f"https://api.github.com/repos/{repository}/actions/workflows/{workflow_id}/runs"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {token}"})
        return r.json()


async def cancel_run(repository: str, run_id: int, token: str) -> dict:
    """Cancel workflow run."""
    url = f"https://api.github.com/repos/{repository}/actions/runs/{run_id}/cancel"
    async with AsyncClient() as client:
        r = await client.post(url, headers={"Authorization": f"Bearer {token}"})
        return {"status": "cancelled"}