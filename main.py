from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import ALLOWED_ORIGINS
from routes import router
from webhook_routes import router as webhook_router
from database import init_db

app = FastAPI(title="SANA WhatsApp Onboarding Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(webhook_router)


@app.on_event("startup")
async def on_startup():
    await init_db()