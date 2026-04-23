from httpx import AsyncClient


async def create_sheet(title: str, sheet_title: str, api_key: str) -> dict:
    """Create Google Sheet."""
    url = "https://sheets.googleapis.com/v4/spreadsheets"
    async with AsyncClient() as client:
        r = await client.post(url, json={"properties": {"title": title}, "sheets": [{"properties": {"title": sheet_title}}]}, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def get_sheet(spreadsheet_id: str, range_: str, api_key: str) -> dict:
    """Get Google Sheet data."""
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{range_}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def update_sheet(spreadsheet_id: str, range_: str, values: list, api_key: str) -> dict:
    """Update Google Sheet."""
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{range_}"
    async with AsyncClient() as client:
        r = await client.put(url, json={"values": values}, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def append_row(spreadsheet_id: str, range_: str, values: list, api_key: str) -> dict:
    """Append row to Google Sheet."""
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{range_}:append"
    async with AsyncClient() as client:
        r = await client.post(url, json={"values": values}, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def list_sheets(api_key: str) -> dict:
    """List Google Sheets."""
    url = "https://www.googleapis.com/drive/v3/files"
    async with AsyncClient() as client:
        r = await client.get(url, params={"q": "mimeType='application/vnd.google-apps.spreadsheet'"}, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()