import httpx
from fastapi import APIRouter, Request, Response, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import WhatsAppCustomer, ProcessedMessage
from sqlalchemy.exc import IntegrityError
from config import WEBHOOK_VERIFY_TOKEN
from database import get_db

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
        messages = change.get("messages", [])
    except (KeyError, IndexError):
        return Response(status_code=200)

    # Deduplicate using the message's wamid, if this event contains one
    if messages:
        wamid = messages[0].get("id")
        if wamid:
            try:
                db.add(ProcessedMessage(wamid=wamid))
                await db.commit()
            except IntegrityError:
                # Already processed this exact message before — skip silently
                await db.rollback()
                print(f"🔁 Duplicate webhook for wamid={wamid}, skipping")
                return Response(status_code=200)

    result = await db.execute(
        select(WhatsAppCustomer).where(WhatsAppCustomer.waba_id == waba_id)
    )
    customer = result.scalar_one_or_none()

    if not customer or not customer.customer_webhook_url:
        print(f"⚠️ No webhook destination for waba_id={waba_id}, phone_number_id={phone_number_id}")
        return Response(status_code=200)

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(customer.customer_webhook_url, json=payload)
            print(f"✅ Forwarded to {customer.customer_webhook_url}, status={resp.status_code}")
    except httpx.RequestError as e:
        print(f"FORWARD ERROR - type: {type(e).__name__} - message: {str(e)}")

    return Response(status_code=200)