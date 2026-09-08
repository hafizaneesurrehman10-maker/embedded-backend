import httpx
from fastapi import HTTPException
from config import GRAPH_API_BASE, META_APP_ID, META_APP_SECRET

# Give Meta's API more time to respond (register/subscribe can be slower)
TIMEOUT = httpx.Timeout(30.0, connect=10.0)


async def get_access_token(code: str) -> str:
    url = f"{GRAPH_API_BASE}/oauth/access_token"
    params = {
        "client_id": META_APP_ID,
        "client_secret": META_APP_SECRET,
        "code": code,
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(url, params=params)
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Meta API request failed: {str(e)}")

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.json())

    return resp.json()["access_token"]


async def register_phone_number(phone_number_id: str, access_token: str, pin: str) -> dict:
    url = f"{GRAPH_API_BASE}/{phone_number_id}/register"
    headers = {"Authorization": f"Bearer {access_token}"}
    body = {"messaging_product": "whatsapp", "pin": pin}

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(url, headers=headers, json=body)
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Meta API request failed: {str(e)}")

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.json())

    return resp.json()


async def subscribe_app_to_waba(waba_id: str, access_token: str) -> dict:
    url = f"{GRAPH_API_BASE}/{waba_id}/subscribed_apps"
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(url, headers=headers)
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Meta API request failed: {str(e)}")

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.json())

    return resp.json()