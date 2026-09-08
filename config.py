import os
from dotenv import load_dotenv

load_dotenv()

META_APP_ID = os.getenv("META_APP_ID")
META_APP_SECRET = os.getenv("META_APP_SECRET")
SYSTEM_USER_TOKEN = os.getenv("SYSTEM_USER_TOKEN")
GRAPH_API_VERSION = "v23.0"
GRAPH_API_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

ALLOWED_ORIGINS = [
    "https://sana-whatsap-onboarding.netlify.app",
]