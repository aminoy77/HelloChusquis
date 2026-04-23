from httpx import AsyncClient


async def send_sms(to: str, message: str, api_key: str) -> dict:
    """Send SMS via Vonage."""
    url = "https://rest.nexmo.com/sms/json"
    async with AsyncClient() as client:
        r = await client.post(url, json={
            "api_key": api_key,
            "to": to,
            "from": "Vonage",
            "text": message
        })
        return r.json()


async def verify_request(api_key: str, phone: str) -> dict:
    """Verify phone number."""
    url = "https://api.nexmo.com/verify/json"
    async with AsyncClient() as client:
        r = await client.post(url, json={"number": phone, "brand": "HelloChusquis"}, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()


async def check_verify(api_key: str, request_id: str, code: str) -> dict:
    """Check verification code."""
    url = "https://api.nexmo.com/verify/json/check"
    async with AsyncClient() as client:
        r = await client.post(url, json={"request_id": request_id, "code": code}, headers={"Authorization": f"Bearer {api_key}"})
        return r.json()