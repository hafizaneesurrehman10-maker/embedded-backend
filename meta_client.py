import httpx
from fastapi import HTTPException
from config import GRAPH_API_BASE, SYSTEM_USER_TOKEN

TIMEOUT = httpx.Timeout(30.0, connect=10.0)


async def register_phone_number(phone_number_id: str, pin: str) -> dict:
    url = f"{GRAPH_API_BASE}/{phone_number_id}/register"
    headers = {"Authorization": f"Bearer {SYSTEM_USER_TOKEN}"}
    body = {"messaging_product": "whatsapp", "pin": pin}

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(url, headers=headers, json=body)
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Meta API request failed: {str(e)}")

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.json())

    return resp.json()


async def subscribe_app_to_waba(waba_id: str) -> dict:
    url = f"{GRAPH_API_BASE}/{waba_id}/subscribed_apps"
    headers = {"Authorization": f"Bearer {SYSTEM_USER_TOKEN}"}

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(url, headers=headers)
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Meta API request failed: {str(e)}")

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.json())

    return resp.json()


async def send_message(phone_number_id: str, to: str, body_text: str) -> dict:
    """We'll use this in the next step, but adding it now for completeness."""
    url = f"{GRAPH_API_BASE}/{phone_number_id}/messages"
    headers = {"Authorization": f"Bearer {SYSTEM_USER_TOKEN}"}
    body = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": body_text},
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(url, headers=headers, json=body)
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Meta API request failed: {str(e)}")

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.json())

    return resp.json()