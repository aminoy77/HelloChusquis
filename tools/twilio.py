from httpx import AsyncClient


async def send_message(auth: str, to: str, message: str) -> dict:
    """Send SMS via Twilio."""
    url = "https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    async with AsyncClient() as client:
        r = await client.post(url, data={"To": to, "Body": message}, 
            headers={"Authorization": f"Bearer {auth}"})
        return r.json()


async def list_messages(auth: str, to: str = None) -> dict:
    """List Twilio messages."""
    url = f"https://api.twilio.com/2010-04-01/Accounts/{{account_sid}}/Messages.json"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {auth}"})
        return r.json()


async def make_call(auth: str, to: str, url: str) -> dict:
    """Make Twilio call."""
    call_url = "https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Calls.json"
    async with AsyncClient() as client:
        r = await client.post(call_url, data={"To": to, "Url": url}, 
            headers={"Authorization": f"Bearer {auth}"})
        return r.json()


async def get_call_log(auth: str, sid: str) -> dict:
    """Get Twilio call log."""
    url = f"https://api.twilio.com/2010-04-01/Accounts/{{account_sid}}/Calls/{sid}.json"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {auth}"})
        return r.json()


async def lookup_phone(auth: str, phone: str) -> dict:
    """Lookup phone number."""
    url = f"https://api.twilio.com/2010-04-01/Addresses/{phone}/Lookup.json"
    async with AsyncClient() as client:
        r = await client.get(url, headers={"Authorization": f"Bearer {auth}"})
        return r.json()