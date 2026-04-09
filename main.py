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
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")
SESSION_SECRET = os.getenv("SESSION_SECRET", "secret")
BASE_URL = os.getenv("BASE_URL", "https://leadforge-llc.onrender.com")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID", "")

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
)

# -----------------------------
# HELPERS
# -----------------------------
def esc(x): return html.escape(str(x)) if x else ""
def now(): return datetime.utcnow().isoformat()

def unlock_lead(lead_id):
    if supabase:
        supabase.table("leads").update({"unlocked": True}).eq("id", lead_id).execute()

def fetch_contractors():
    return supabase.table("contractors").select("*").execute().data if supabase else []

def fetch_leads():
    return supabase.table("leads").select("*").execute().data if supabase else []

def fetch_lead_by_id(lead_id):
    res = supabase.table("leads").select("*").eq("id", lead_id).execute()
    return res.data[0] if res.data else None

# -----------------------------
# BASIC
# -----------------------------
@app.get("/")
def home():
    return HTMLResponse("""
    <h1>VaultForge</h1>
    <a href="/services">Services</a><br>
    <a href="/contractors">Contractors</a><br>
    <a href="/join-contractor">Join Contractor</a><br>
    <a href="/admin">Admin</a>
    """)

@app.get("/health")
def health():
    return {"ok": True}

# -----------------------------
# SERVICES
# -----------------------------
@app.get("/services")
def services():
    return HTMLResponse("""
    <h2>Services</h2>
    <a href="/contractors?service=roofing">Roofing</a><br>
    <a href="/contractors?service=plumbing">Plumbing</a><br>
    """)

# -----------------------------
# CONTRACTORS
# -----------------------------
@app.get("/contractors")
def contractors(service: str = ""):
    rows = fetch_contractors()
    rows = [r for r in rows if r.get("approved")]

    html_out = "<h2>Contractors</h2>"

    for c in rows:
        html_out += f"""
        <div>
        <h3>{esc(c.get("company_name"))}</h3>
        <p>{esc(c.get("service"))}</p>
        <a href="/request/{c.get("id")}">Request</a>
        </div>
        """

    return HTMLResponse(html_out)

# -----------------------------
# JOIN CONTRACTOR
# -----------------------------
@app.get("/join-contractor")
def join_form():
    return HTMLResponse("""
    <form method="post">
    <input name="company_name" placeholder="Company" required>
    <input name="service" placeholder="Service" required>
    <button>Submit</button>
    </form>
    """)

@app.post("/join-contractor")
def join_submit(company_name: str = Form(...), service: str = Form(...)):
    supabase.table("contractors").insert({
        "id": str(uuid4()),
        "company_name": company_name,
        "service": service,
        "approved": False
    }).execute()

    return RedirectResponse("/join-contractor-success", 303)

@app.get("/join-contractor-success")
def join_success():
    return HTMLResponse("<h1>Submitted</h1>")

# -----------------------------
# REQUEST
# -----------------------------
@app.get("/request/{contractor_id}")
def request_form(contractor_id: str):
    return HTMLResponse(f"""
    <form method="post">
    <input name="owner_name" required>
    <input name="phone" required>
    <input name="service" required>
    <button>Submit</button>
    </form>
    """)

@app.post("/request/{contractor_id}")
def request_submit(contractor_id: str, owner_name: str = Form(...), phone: str = Form(...), service: str = Form(...)):
    supabase.table("leads").insert({
        "id": str(uuid4()),
        "contractor_id": contractor_id,
        "owner_name": owner_name,
        "phone": phone,
        "service": service,
        "unlocked": False
    }).execute()

    return RedirectResponse("/request-success", 303)

@app.get("/request-success")
def request_success():
    return HTMLResponse("<h1>Sent</h1>")

# -----------------------------
# ADMIN
# -----------------------------
@app.get("/admin")
def admin():
    contractors = fetch_contractors()
    leads = fetch_leads()

    html_out = "<h1>Admin</h1>"

    for c in contractors:
        html_out += f"<h2>{esc(c.get('company_name'))}</h2>"

        for l in leads:
            if l.get("contractor_id") == c.get("id"):
                html_out += f"""
                <p>{esc(l.get("owner_name"))} | {esc(l.get("phone"))}</p>
                """

    return HTMLResponse(html_out)

# -----------------------------
# STRIPE
# -----------------------------
@app.get("/unlock/{lead_id}")
def unlock(lead_id: str):
    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[{"price": STRIPE_PRICE_ID, "quantity": 1}],
        success_url=f"{BASE_URL}/stripe-success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{BASE_URL}",
        metadata={"lead_id": lead_id}
    )
    return RedirectResponse(session.url)

@app.get("/stripe-success")
def stripe_success(session_id: str = ""):
    session = stripe.checkout.Session.retrieve(session_id)

    if session.payment_status == "paid":
        lead_id = session.metadata.get("lead_id")
        unlock_lead(lead_id)

        return HTMLResponse("<h1>Unlocked</h1><a href='/'>Home</a>")

    return HTMLResponse("Payment failed")
