from httpx import AsyncClient


async def create_invoice(customer_id: str, line_items: list, access_token: str) -> dict:
    """Create QuickBooks invoice."""
    url = "https://quickbooks.api.intuit.com/v3/company/{company_id}/invoice"
    async with AsyncClient() as client:
        r = await client.post(url, json={"CustomerRef": {"value": customer_id}, "Line": line_items}, headers={"Authorization": f"Bearer {access_token}"})
        return r.json()


async def get_invoice(invoice_id: str, access_token: str) -> dict:
    """Get QuickBooks invoice."""
    url = f"https://quickbooks.api.intuit.com/v3/company/{{company_id}}/invoice/{invoice_id}"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {access_token}"})
        return r.json()


async def create_customer(name: str, email: str, access_token: str) -> dict:
    """Create QuickBooks customer."""
    url = "https://quickbooks.api.intuit.com/v3/company/{company_id}/customer"
    async with AsyncClient() as client:
        r = await client.post(url, json={"DisplayName": name, "PrimaryEmailAddr": {"Address": email}}, headers={"Authorization": f"Bearer {access_token}"})
        return r.json()


async def get_customers(access_token: str, max_results: int = 10) -> dict:
    """Get QuickBooks customers."""
    url = "https://quickbooks.api.intuit.com/v3/company/{company_id}/query"
    async with AsyncClient() as client:
        r = await client.get(url, params={"query": f"SELECT * FROM Customer MAXRESULTS {max_results}"}, headers={"Authorization": f"Bearer {access_token}"})
        return r.json()


async def create_vendor(name: str, access_token: str) -> dict:
    """Create QuickBooks vendor."""
    url = "https://quickbooks.api.intuit.com/v3/company/{company_id}/vendor"
    async with AsyncClient() as client:
        r = await client.post(url, json={"DisplayName": name}, headers={"Authorization": f"Bearer {access_token}"})
        return r.json()