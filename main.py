from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from pydantic import BaseModel
from supabase import create_client
from datetime import datetime, timezone
import stripe
import os
import html
import json

app = FastAPI()

templates = Jinja2Templates(directory="templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
LEAD_UNLOCK_PRICE = os.getenv("LEAD_UNLOCK_PRICE", "1000")
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "https://leadforge-llc.onrender.com")
FRONTEND_BASE_URL = os.getenv(
    "FRONTEND_BASE_URL",
    "https://lead-forge-frontend-git-main-bcrsoutheast-langs-projects.vercel.app",
)

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Missing SUPABASE_URL or SUPABASE_KEY environment variables")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY


class ContractorCreate(BaseModel):
    company_name: str
    contact_name: str
    phone: str
    email: str
    service_type: str
    city: str | None = ""
    state: str | None = ""
    zip_code: str | None = ""
    website: str | None = ""
    notes: str | None = ""


class LeadCreate(BaseModel):
    homeowner_name: str
    phone: str
    email: str
    city: str | None = ""
    state: str | None = ""
    zip_code: str | None = ""
    service: str | None = ""
    project_details: str | None = ""
    contractor_id: str | None = None
    contractor_name: str | None = ""


class CheckoutRequest(BaseModel):
    lead_id: str


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def safe(value):
    if value is None:
        return ""
    return html.escape(str(value))


def js_string(value):
    return json.dumps("" if value is None else str(value))


def fetch_lead_or_404(lead_id: str):
    result = (
        supabase.table("leads")
        .select("*")
        .eq("id", lead_id)
        .limit(1)
        .execute()
    )
    data = result.data or []
    if not data:
        raise HTTPException(status_code=404, detail="Lead not found")
    return data[0]


def fetch_contractor_or_404(contractor_id: str):
    result = (
        supabase.table("contractors")
        .select("*")
        .eq("id", contractor_id)
        .limit(1)
        .execute()
    )
    data = result.data or []
    if not data:
        raise HTTPException(status_code=404, detail="Contractor not found")
    return data[0]


# ✅ NEW ROOT (HOMEPAGE)
@app.get("/", response_class=HTMLResponse)
def homepage(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
def health():
    return {"status": "ok"}
