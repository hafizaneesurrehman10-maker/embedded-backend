from fastapi import APIRouter
from schemas import ExchangeCodeRequest, RegisterPhoneRequest, SubscribeWabaRequest
import meta_client

router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])


@router.post("/exchange-code")
async def exchange_code(payload: ExchangeCodeRequest):
    access_token = await meta_client.get_access_token(payload.code)

    register_result = await meta_client.register_phone_number(
        phone_number_id=payload.phone_number_id,
        access_token=access_token,
        pin="000000",  # TODO: replace with real per-customer PIN
    )

    subscribe_result = await meta_client.subscribe_app_to_waba(
        waba_id=payload.waba_id,
        access_token=access_token,
    )

    # TODO: persist access_token, waba_id, phone_number_id to your database here

    return {
        "access_token": access_token,
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