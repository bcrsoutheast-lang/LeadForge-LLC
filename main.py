from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from supabase import create_client, Client
from datetime import datetime
from uuid import uuid4
import os
import html
import stripe

app = FastAPI()

# -----------------------------
# ENV
# -----------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "changeme").strip()
SESSION_SECRET = os.getenv("SESSION_SECRET", "leadforge-session-secret").strip()
BASE_URL = os.getenv("BASE_URL", "https://leadforge-llc.onrender.com").strip()
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "").strip()
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID", "").strip()

supabase: Client | None = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

stripe.api_key = STRIPE_SECRET_KEY

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    same_site="lax",
    https_only=True,
)

# -----------------------------
# HELPERS
# -----------------------------
def esc(value):
    return html.escape(str(value)) if value else ""

def now_iso():
    return datetime.utcnow().isoformat()

def unlock_lead(lead_id):
    if supabase:
        supabase.table("leads").update({"unlocked": True}).eq("id", lead_id).execute()

def fetch_lead_by_id(lead_id):
    if not supabase:
        return None
    res = supabase.table("leads").select("*").eq("id", lead_id).limit(1).execute()
    return res.data[0] if res.data else None

# -----------------------------
# BASIC ROUTES
# -----------------------------
@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse)
def home():
    return HTMLResponse("<h1>VaultForge Live</h1>")

# -----------------------------
# STRIPE UNLOCK
# -----------------------------
@app.get("/unlock/{lead_id}")
def unlock_checkout(lead_id: str):

    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[{
            "price": STRIPE_PRICE_ID,
            "quantity": 1,
        }],
        success_url=f"{BASE_URL}/stripe-success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{BASE_URL}",
        metadata={
            "lead_id": lead_id,
        },
    )

    return RedirectResponse(url=session.url, status_code=303)

# -----------------------------
# FIXED STRIPE SUCCESS
# -----------------------------
@app.get("/stripe-success", response_class=HTMLResponse)
def stripe_success(session_id: str = ""):

    if not session_id:
        return HTMLResponse("Missing session ID", status_code=400)

    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except Exception as e:
        return HTMLResponse(f"Stripe error: {str(e)}", status_code=500)

    payment_status = getattr(session, "payment_status", "")
    metadata = getattr(session, "metadata", {}) or {}

    lead_id = metadata.get("lead_id", "")

    if payment_status == "paid" and lead_id:

        unlock_lead(lead_id)

        lead = fetch_lead_by_id(lead_id)

        return HTMLResponse(f"""
        <h1>Payment Successful</h1>
        <p>Lead unlocked.</p>

        <h3>Homeowner Info:</h3>
        <p>Name: {esc(lead.get("owner_name"))}</p>
        <p>Phone: {esc(lead.get("phone"))}</p>
        <p>Email: {esc(lead.get("email"))}</p>
        <p>City: {esc(lead.get("city"))}</p>
        <p>State: {esc(lead.get("state"))}</p>
        <p>ZIP: {esc(lead.get("zip"))}</p>
        <p>Service: {esc(lead.get("service"))}</p>
        <p>Project: {esc(lead.get("project_details"))}</p>

        <br><br>
        <a href="/">Back Home</a>
        """)

    return HTMLResponse("Payment not completed", status_code=400)
