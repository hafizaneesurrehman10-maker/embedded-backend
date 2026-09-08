from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from schemas import ExchangeCodeRequest
from database import get_db
from models import WhatsAppCustomer
import meta_client

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
    else:
        new_customer = WhatsAppCustomer(
            waba_id=payload.waba_id,
            phone_number_id=payload.phone_number_id,
            access_token="managed_by_system_user",  # placeholder, see note below
            pin_code=pin,
            status="active",
        )
        db.add(new_customer)

    await db.commit()

    return {
        "success": True,
        "waba_id": payload.waba_id,
        "phone_number_id": payload.phone_number_id,
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