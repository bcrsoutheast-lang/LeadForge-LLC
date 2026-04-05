from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from supabase import create_client
from datetime import datetime, timezone
import stripe
import os
import html
import json

app = FastAPI()

# TEMPLATES + STATIC
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="templates/static"), name="static")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ENV
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
LEAD_UNLOCK_PRICE = os.getenv("LEAD_UNLOCK_PRICE", "1000")

BACKEND_BASE_URL = "https://leadforge-llc.onrender.com"
FRONTEND_BASE_URL = "https://lead-forge-frontend-git-main-bcrsoutheast-langs-projects.vercel.app"

# SERVICES
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY


# =========================
# MODELS
# =========================
class ContractorCreate(BaseModel):
    company_name: str
    contact_name: str
    phone: str
    email: str
    service_type: str
    city: str | None = ""
    state: str | None = ""
    zip_code: str | None = ""


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


# =========================
# HELPERS
# =========================
def now_iso():
    return datetime.now(timezone.utc).isoformat()


def safe(value):
    return "" if value is None else html.escape(str(value))


def fetch_lead(lead_id):
    result = supabase.table("leads").select("*").eq("id", lead_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Lead not found")
    return result.data[0]


# =========================
# ROUTES
# =========================

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )


@app.get("/health")
def health():
    return {"status": "ok"}


# =========================
# CONTRACTORS
# =========================

@app.post("/contractors")
def create_contractor(contractor: ContractorCreate):
    supabase.table("contractors").insert({
        "company_name": contractor.company_name,
        "contact_name": contractor.contact_name,
        "phone": contractor.phone,
        "email": contractor.email,
        "service_type": contractor.service_type,
        "city": contractor.city,
        "state": contractor.state,
        "zip_code": contractor.zip_code,
        "approved": False,
        "created_at": now_iso()
    }).execute()

    return {"message": "Contractor submitted"}


@app.get("/contractors")
def get_contractors():
    result = supabase.table("contractors").select("*").eq("approved", True).execute()
    return result.data


# =========================
# LEADS
# =========================

@app.post("/leads")
def create_lead(lead: LeadCreate):
    result = supabase.table("leads").insert({
        "homeowner_name": lead.homeowner_name,
        "phone": lead.phone,
        "email": lead.email,
        "city": lead.city,
        "state": lead.state,
        "zip_code": lead.zip_code,
        "service": lead.service,
        "project_details": lead.project_details,
        "contractor_id": lead.contractor_id,
        "contractor_name": lead.contractor_name,
        "unlocked": False,
        "created_at": now_iso()
    }).execute()

    return {"message": "Lead created", "data": result.data}


# =========================
# STRIPE
# =========================

@app.post("/create-checkout-session")
def create_checkout(request: CheckoutRequest):
    lead = fetch_lead(request.lead_id)

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {"name": "Lead Unlock"},
                "unit_amount": int(LEAD_UNLOCK_PRICE),
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=f"{BACKEND_BASE_URL}/lead-detail/{request.lead_id}",
        cancel_url=f"{BACKEND_BASE_URL}/unlock/{request.lead_id}",
        metadata={"lead_id": request.lead_id}
    )

    return {"url": session.url}


# =========================
# ADMIN (simple)
# =========================

@app.get("/admin", response_class=HTMLResponse)
def admin():
    contractors = supabase.table("contractors").select("*").execute().data
    leads = supabase.table("leads").select("*").execute().data

    return f"""
    <h1>Admin</h1>

    <h2>Contractors</h2>
    <pre>{contractors}</pre>

    <h2>Leads</h2>
    <pre>{leads}</pre>
    """


# =========================
# CONTRACTOR SIGNUP PAGE
# =========================

@app.get("/contractor-signup", response_class=HTMLResponse)
def contractor_signup():
    return """
    <h1>Contractor Signup</h1>
    <p>Form connected to backend.</p>
    <a href="/">Back</a>
    """
