import os
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.getenv("META_APP_ID")
APP_SECRET = os.getenv("META_APP_SECRET")
GRAPH_API_VERSION = "v23.0"

app = FastAPI()

# Allow your frontend (Netlify) to call this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sana-whatsap-onboarding.netlify.app"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ExchangeCodeRequest(BaseModel):
    code: str
    waba_id: str
    phone_number_id: str


@app.post("/api/whatsapp/exchange-code")
async def exchange_code(payload: ExchangeCodeRequest):
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/oauth/access_token"
    params = {
        "client_id": APP_ID,
        "client_secret": APP_SECRET,
        "code": payload.code,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.json())

    data = resp.json()
    access_token = data.get("access_token")

    # TODO (next step): save access_token, waba_id, phone_number_id
    # against this customer's record in your database

    return {
        "access_token": access_token,
        "waba_id": payload.waba_id,
        "phone_number_id": payload.phone_number_id,
    }