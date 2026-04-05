from datetime import datetime
import os

import stripe
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from supabase import Client, create_client


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Templates
templates = Jinja2Templates(directory="templates")

# Static folders
if os.path.isdir("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

if os.path.isdir("templates/static"):
    app.mount("/templates/static", StaticFiles(directory="templates/static"), name="templates_static")

# Root-level uploaded image fallback
if os.path.isfile("IMG_2026.png"):
    app.mount("/", StaticFiles(directory="."), name="root_files")

# Environment
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID", "")
BASE_URL = os.getenv("BASE_URL", "https://leadforge-llc.onrender.com")

supabase: Client | None = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY


# -----------------------------
# Models
# -----------------------------
class ContractorCreate(BaseModel):
    company_name: str
    contact_name: str
    phone: str
    email: str
    service_type: str


class LeadCreate(BaseModel):
    homeowner_name: str
    phone: str
    service: str
    project_details: str
    contractor_id: str


# -----------------------------
# Helpers
# -----------------------------
def require_supabase() -> Client:
    if supabase is None:
        raise HTTPException(status_code=500, detail="Supabase is not configured")
    return supabase


# -----------------------------
# Pages
# -----------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/homeowner", response_class=HTMLResponse)
def homeowner_page(request: Request):
    return templates.TemplateResponse("homeowner.html", {"request": request})


@app.get("/contractor-signup", response_class=HTMLResponse)
def contractor_signup_page():
    return HTMLResponse(
        """
        <html>
            <head>
                <title>Contractor Signup</title>
            </head>
            <body>
                <h1>Contractor Signup</h1>
                <p>Form connected to backend.</p>
                <a href="/">Back</a>
            </body>
        </html>
        """
    )


@app.get("/health")
def health():
    return {"status": "ok"}


# -----------------------------
# Contractors
# -----------------------------
@app.get("/contractors")
def get_contractors():
    db = require_supabase()
    result = (
        db.table("contractors")
        .select("*")
        .eq("approved", True)
        .execute()
    )
    return result.data or []


@app.post("/contractors")
def create_contractor(contractor: ContractorCreate):
    db = require_supabase()

    payload = {
        "company_name": contractor.company_name,
        "contact_name": contractor.contact_name,
        "phone": contractor.phone,
        "email": contractor.email,
        "service_type": contractor.service_type,
        "approved": False,
    }

    result = db.table("contractors").insert(payload).execute()
    return {
        "message": "Contractor created",
        "data": result.data,
    }


# -----------------------------
# Leads
# -----------------------------
@app.post("/leads")
def create_lead(lead: LeadCreate):
    db = require_supabase()

    payload = {
        "homeowner_name": lead.homeowner_name,
        "phone": lead.phone,
        "service": lead.service,
        "project_details": lead.project_details,
        "contractor_id": lead.contractor_id,
        "unlocked": False,
    }

    result = db.table("leads").insert(payload).execute()
    return {
        "message": "Lead created",
        "data": result.data,
    }


# -----------------------------
# Admin
# -----------------------------
@app.get("/admin", response_class=HTMLResponse)
def admin_page():
    db = require_supabase()

    contractors = db.table("contractors").select("*").execute().data or []
    leads = db.table("leads").select("*").execute().data or []

    html = f"""
    <html>
        <head>
            <title>Admin</title>
        </head>
        <body>
            <h1>Admin</h1>

            <h2>Contractors</h2>
            <pre>{contractors}</pre>

            <h2>Leads</h2>
            <pre>{leads}</pre>
        </body>
    </html>
    """
    return HTMLResponse(content=html)


# -----------------------------
# Unlock / Stripe
# -----------------------------
@app.get("/unlock/{lead_id}", response_class=HTMLResponse)
def unlock_page(lead_id: str):
    db = require_supabase()

    lead_result = db.table("leads").select("*").eq("id", lead_id).execute()
    if not lead_result.data:
        return HTMLResponse("<h1>Lead not found</h1>", status_code=404)

    lead = lead_result.data[0]

    html = f"""
    <html>
        <head>
            <title>Unlock Lead</title>
        </head>
        <body>
            <h1>Unlock Opportunity</h1>
            <p><strong>Service:</strong> {lead.get("service", "")}</p>
            <p><strong>Project:</strong> {lead.get("project_details", "")}</p>
            <p><strong>Status:</strong> {"Unlocked" if lead.get("unlocked") else "Locked"}</p>

            <form action="/create-checkout-session" method="post">
                <input type="hidden" name="lead_id" value="{lead_id}">
                <button type="submit">Unlock for $10</button>
            </form>

            <p><a href="/">Back</a></p>
        </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.post("/create-checkout-session")
async def create_checkout_session(request: Request):
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe is not configured")

    form = await request.form()
    lead_id = form.get("lead_id")

    if not lead_id:
        raise HTTPException(status_code=400, detail="Missing lead_id")

    if STRIPE_PRICE_ID:
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[{"price": STRIPE_PRICE_ID, "quantity": 1}],
            success_url=f"{BASE_URL}/lead-detail/{lead_id}",
            cancel_url=f"{BASE_URL}/unlock/{lead_id}",
            metadata={"lead_id": lead_id},
        )
    else:
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {"name": "Lead Unlock"},
                        "unit_amount": 1000,
                    },
                    "quantity": 1,
                }
            ],
            success_url=f"{BASE_URL}/lead-detail/{lead_id}",
            cancel_url=f"{BASE_URL}/unlock/{lead_id}",
            metadata={"lead_id": lead_id},
        )

    return RedirectResponse(url=session.url, status_code=303)


@app.get("/lead-detail/{lead_id}", response_class=HTMLResponse)
def lead_detail(lead_id: str):
    db = require_supabase()

    lead_result = db.table("leads").select("*").eq("id", lead_id).execute()
    if not lead_result.data:
        return HTMLResponse("<h1>Lead not found</h1>", status_code=404)

    lead = lead_result.data[0]

    if not lead.get("unlocked"):
        db.table("leads").update({"unlocked": True}).eq("id", lead_id).execute()
        lead["unlocked"] = True

    html = f"""
    <html>
        <head>
            <title>Lead Detail</title>
        </head>
        <body>
            <h1>Lead Detail</h1>
            <p><strong>Name:</strong> {lead.get("homeowner_name", "")}</p>
            <p><strong>Phone:</strong> {lead.get("phone", "")}</p>
            <p><strong>Service:</strong> {lead.get("service", "")}</p>
            <p><strong>Project Details:</strong> {lead.get("project_details", "")}</p>
            <p><strong>Contractor ID:</strong> {lead.get("contractor_id", "")}</p>
            <p><a href="/">Back</a></p>
        </body>
    </html>
    """
    return HTMLResponse(content=html)
