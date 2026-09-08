import httpx
from fastapi import HTTPException
from config import GRAPH_API_BASE, META_APP_ID, META_APP_SECRET


async def get_access_token(code: str) -> str:
    """Exchange a one-time auth code for a business access token."""
    url = f"{GRAPH_API_BASE}/oauth/access_token"
    params = {
        "client_id": META_APP_ID,
        "client_secret": META_APP_SECRET,
        "code": code,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.json())

    return resp.json()["access_token"]


async def register_phone_number(phone_number_id: str, access_token: str, pin: str) -> dict:
    """Activate a phone number for Cloud API messaging."""
    url = f"{GRAPH_API_BASE}/{phone_number_id}/register"
    headers = {"Authorization": f"Bearer {access_token}"}
    body = {"messaging_product": "whatsapp", "pin": pin}

    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=headers, json=body)

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.json())

    return resp.json()


async def subscribe_app_to_waba(waba_id: str, access_token: str) -> dict:
    """Subscribe this app to receive webhook events for a WABA."""
    url = f"{GRAPH_API_BASE}/{waba_id}/subscribed_apps"
    headers = {"Authorization": f"Bearer {access_token}"}

    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=headers)

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.json())

    return resp.json()