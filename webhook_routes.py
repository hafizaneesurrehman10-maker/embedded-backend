from fastapi import APIRouter, Request, Response
from config import WEBHOOK_VERIFY_TOKEN

router = APIRouter(prefix="/webhook", tags=["webhook"])


@router.get("")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == WEBHOOK_VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")

    return Response(status_code=403)