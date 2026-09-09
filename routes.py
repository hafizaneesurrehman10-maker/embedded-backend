from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import Header
from schemas import ExchangeCodeRequest, SendMessageRequest , UpdateWebhookRequest
from database import get_db
from models import WhatsAppCustomer
import meta_client
from fastapi import HTTPException


router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])


@router.post("/exchange-code")
async def exchange_code(payload: ExchangeCodeRequest, db: AsyncSession = Depends(get_db)):
    pin = "000000"

    try:
        register_result = await meta_client.register_phone_number(
            phone_number_id=payload.phone_number_id,
            pin=pin,
        )
    except Exception as e:
        register_result = {"skipped": True, "reason": str(e)}

    subscribe_result = await meta_client.subscribe_app_to_waba(
        waba_id=payload.waba_id,
    )

    result = await db.execute(
        select(WhatsAppCustomer).where(WhatsAppCustomer.waba_id == payload.waba_id)
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.phone_number_id = payload.phone_number_id
        existing.pin_code = pin
        existing.status = "active"
        api_key = existing.api_key
    else:
        import secrets
        api_key = "tqa_" + secrets.token_hex(12)  # adjust prefix per-tenant later if you want
        new_customer = WhatsAppCustomer(
            waba_id=payload.waba_id,
            phone_number_id=payload.phone_number_id,
            pin_code=pin,
            status="active",
            api_key=api_key,
        )
        db.add(new_customer)

    await db.commit()

    return {
        "success": True,
        "waba_id": payload.waba_id,
        "phone_number_id": payload.phone_number_id,
        "api_key": api_key,
        "send_endpoint": "https://embedded-backend-e3jc.onrender.com/api/whatsapp/send",
        "register_result": register_result,
        "subscribe_result": subscribe_result,
    }

@router.get("/customers")
async def list_customers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(WhatsAppCustomer))
    customers = result.scalars().all()
    return [
        {
            "id": c.id,
            "waba_id": c.waba_id,
            "phone_number_id": c.phone_number_id,
            "business_name": c.business_name,
            "status": c.status,
            "created_at": c.created_at,
        }
        for c in customers
    ]



@router.post("/send")
async def send_message(
    payload: SendMessageRequest,
    x_api_key: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WhatsAppCustomer).where(WhatsAppCustomer.api_key == x_api_key)
    )
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(status_code=401, detail="Invalid API key")

    send_result = await meta_client.send_message(
        phone_number_id=customer.phone_number_id,
        to=payload.to,
        body_text=payload.message,
    )

    return {"success": True, "result": send_result}





@router.put("/webhook-url")
async def update_webhook_url(
    payload: UpdateWebhookRequest,
    x_api_key: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WhatsAppCustomer).where(WhatsAppCustomer.api_key == x_api_key)
    )
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(status_code=401, detail="Invalid API key")

    customer.customer_webhook_url = payload.webhook_url
    await db.commit()

    return {"success": True, "webhook_url": payload.webhook_url}