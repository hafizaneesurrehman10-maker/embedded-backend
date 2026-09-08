import httpx
from fastapi import APIRouter, Request, Response, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from config import WEBHOOK_VERIFY_TOKEN
from database import get_db
from models import WhatsAppCustomer

router = APIRouter(prefix="/webhook", tags=["webhook"])


@router.get("")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == WEBHOOK_VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")

    return Response(status_code=403)


@router.post("")
async def receive_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.json()

    try:
        entry = payload["entry"][0]
        waba_id = entry["id"]
        change = entry["changes"][0]["value"]
        phone_number_id = change.get("metadata", {}).get("phone_number_id")
    except (KeyError, IndexError):
        # Not a message event (could be a status update with different shape) — accept and ignore
        return Response(status_code=200)

    # Look up which customer this belongs to
    result = await db.execute(
        select(WhatsAppCustomer).where(WhatsAppCustomer.waba_id == waba_id)
    )
    customer = result.scalar_one_or_none()

    if not customer or not customer.customer_webhook_url:
        # Unknown customer or no destination configured — log and drop
        print(f"⚠️ No webhook destination for waba_id={waba_id}, phone_number_id={phone_number_id}")
        return Response(status_code=200)

    # Forward the raw payload to the customer's own webhook
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(customer.customer_webhook_url, json=payload)
    except httpx.RequestError as e:
        print(f"❌ Failed to forward to {customer.customer_webhook_url}: {e}")

    # Always return 200 quickly to Meta, regardless of forwarding outcome
    return Response(status_code=200)