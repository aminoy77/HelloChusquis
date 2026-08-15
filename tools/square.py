from __future__ import annotations

import os
import httpx

PLUGIN_NAME = "square"
PLUGIN_DESCRIPTION = "Square payments, orders, and catalog"


def run(action: str, **kwargs) -> str:
    token = os.getenv("SQUARE_ACCESS_TOKEN")
    location_id = os.getenv("SQUARE_LOCATION_ID")
    if not token:
        return "Error: No Square access token found. Set SQUARE_ACCESS_TOKEN environment variable."

    base_url = "https://connect.squareup.com/v2"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    try:
        if action == "list_payments":
            r = httpx.get(f"{base_url}/payments", headers=headers, timeout=30)
            data = r.json()
            return str(data.get("payments", data))

        elif action == "create_payment":
            amount = kwargs.get("amount")
            if not amount:
                return "Error: amount required for create_payment"
            currency = kwargs.get("currency", "USD")
            source_id = kwargs.get("source_id", "cnon:card-nonce-ok")
            payload = {
                "source_id": source_id,
                "idempotency_key": kwargs.get("idempotency_key", ""),
                "amount_money": {"amount": int(float(amount) * 100), "currency": currency},
            }
            if location_id:
                payload["location_id"] = location_id
            r = httpx.post(f"{base_url}/payments", headers=headers, json=payload, timeout=30)
            return _fmt(r)

        elif action == "list_orders":
            r = httpx.get(f"{base_url}/orders", headers=headers, timeout=30)
            data = r.json()
            return str(data.get("orders", data))

        elif action == "list_locations":
            r = httpx.get(f"{base_url}/locations", headers=headers, timeout=30)
            data = r.json()
            return str(data.get("locations", data))

        else:
            return f"Error: Unknown action '{action}'. Available: list_payments, create_payment, list_orders, list_locations"
    except httpx.TimeoutException:
        return "Error: Request timed out after 30 seconds."
    except Exception as e:
        return f"Error: {e}"


def _fmt(r: httpx.Response) -> str:
    try:
        return str(r.json())
    except Exception:
        return r.text[:500]