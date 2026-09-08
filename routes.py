from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from schemas import ExchangeCodeRequest, RegisterPhoneRequest, SubscribeWabaRequest
from database import get_db
from models import WhatsAppCustomer
from utils import generate_pin
import meta_client
import datetime

router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])



@router.post("/exchange-code")
async def exchange_code(payload: ExchangeCodeRequest, db: AsyncSession = Depends(get_db)):
    short_lived_token = await meta_client.get_access_token(payload.code)

    # Exchange for a long-lived token
    long_lived_data = await meta_client.get_long_lived_token(short_lived_token)
    access_token = long_lived_data["access_token"]
    expires_in_seconds = long_lived_data.get("expires_in", 60 * 24 * 3600)  # fallback ~60 days
    expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=expires_in_seconds)

    pin = "000000"

    try:
        register_result = await meta_client.register_phone_number(
            phone_number_id=payload.phone_number_id,
            access_token=access_token,
            pin=pin,
        )
    except HTTPException as e:
        register_result = {"skipped": True, "reason": e.detail}

    subscribe_result = await meta_client.subscribe_app_to_waba(
        waba_id=payload.waba_id,
        access_token=access_token,
    )

    result = await db.execute(
        select(WhatsAppCustomer).where(WhatsAppCustomer.waba_id == payload.waba_id)
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.phone_number_id = payload.phone_number_id
        existing.access_token = access_token
        existing.token_expires_at = expires_at
        existing.pin_code = pin
        existing.status = "active"
    else:
        new_customer = WhatsAppCustomer(
            waba_id=payload.waba_id,
            phone_number_id=payload.phone_number_id,
            access_token=access_token,
            token_expires_at=expires_at,
            pin_code=pin,
            status="active",
        )
        db.add(new_customer)

    await db.commit()

    return {
        "success": True,
        "waba_id": payload.waba_id,
        "phone_number_id": payload.phone_number_id,
        "token_expires_at": expires_at.isoformat(),
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