from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from schemas import ExchangeCodeRequest, RegisterPhoneRequest, SubscribeWabaRequest
from database import get_db
from models import WhatsAppCustomer
import meta_client

router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])


@router.post("/exchange-code")
async def exchange_code(payload: ExchangeCodeRequest, db: AsyncSession = Depends(get_db)):
    access_token = await meta_client.get_access_token(payload.code)

    register_result = await meta_client.register_phone_number(
        phone_number_id=payload.phone_number_id,
        access_token=access_token,
        pin="000000",  # TODO: replace with real per-customer PIN (Step 4)
    )

    subscribe_result = await meta_client.subscribe_app_to_waba(
        waba_id=payload.waba_id,
        access_token=access_token,
    )

    # Check if this WABA already has a record (re-onboarding case)
    result = await db.execute(
        select(WhatsAppCustomer).where(WhatsAppCustomer.waba_id == payload.waba_id)
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.phone_number_id = payload.phone_number_id
        existing.access_token = access_token
        existing.status = "active"
    else:
        new_customer = WhatsAppCustomer(
            waba_id=payload.waba_id,
            phone_number_id=payload.phone_number_id,
            access_token=access_token,
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


@router.post("/register-phone")
async def register_phone(payload: RegisterPhoneRequest):
    return await meta_client.register_phone_number(
        payload.phone_number_id, payload.access_token, payload.pin
    )


@router.post("/subscribe-waba")
async def subscribe_waba(payload: SubscribeWabaRequest):
    return await meta_client.subscribe_app_to_waba(
        payload.waba_id, payload.access_token
    )