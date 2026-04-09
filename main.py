from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from supabase import create_client
from uuid import uuid4
from datetime import datetime
import stripe
import os

app = FastAPI()

# ENV
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID")
BASE_URL = "https://leadforge-llc.onrender.com"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
stripe.api_key = STRIPE_SECRET_KEY

app.add_middleware(SessionMiddleware, secret_key="secret")

# ---------------- HOME ----------------
@app.get("/")
def home():
    return HTMLResponse("""
    <h1>VaultForge</h1>
    <a href="/services">Services</a><br>
    <a href="/contractors">Contractors</a><br>
    <a href="/join-contractor">Join Contractor</a><br>
    <a href="/admin">Admin</a>
    """)

# ---------------- SERVICES ----------------
@app.get("/services")
def services():
    return HTMLResponse("""
    <h2>Services</h2>
    <a href="/contractors?service=roofing">Roofing</a><br>
    <a href="/contractors?service=plumbing">Plumbing</a>
    """)

# ---------------- CONTRACTORS ----------------
@app.get("/contractors")
def contractors(service: str = ""):
    data = supabase.table("contractors").select("*").execute().data
    html = "<h2>Contractors</h2>"

    for c in data:
        if c.get("approved"):
            html += f"""
            <div>
                <h3>{c.get("company_name")}</h3>
                <p>{c.get("service")}</p>
                <a href="/request/{c.get("id")}">Request</a>
            </div>
            """

    return HTMLResponse(html)

# ---------------- JOIN ----------------
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
        "approved": False,
        "created_at": datetime.utcnow().isoformat()
    }).execute()

    return RedirectResponse("/join-contractor-success", 303)

@app.get("/join-contractor-success")
def join_success():
    return HTMLResponse("<h1>Submitted</h1>")

# ---------------- REQUEST ----------------
@app.get("/request/{contractor_id}")
def request_form(contractor_id: str):
    return HTMLResponse("""
    <form method="post">
    <input name="owner_name" placeholder="Name" required>
    <input name="phone" placeholder="Phone" required>
    <input name="service" placeholder="Service" required>
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
        "unlocked": False,
        "created_at": datetime.utcnow().isoformat()
    }).execute()

    return RedirectResponse("/request-success", 303)

@app.get("/request-success")
def success():
    return HTMLResponse("<h1>Request Sent</h1>")

# ---------------- ADMIN ----------------
@app.get("/admin")
def admin():
    contractors = supabase.table("contractors").select("*").execute().data
    leads = supabase.table("leads").select("*").execute().data

    html = "<h1>Admin</h1>"

    for c in contractors:
        html += f"<h2>{c.get('company_name')}</h2>"

        for l in leads:
            if l.get("contractor_id") == c.get("id"):
                html += f"{l.get('owner_name')} | {l.get('phone')}<br>"

    return HTMLResponse(html)

# ---------------- STRIPE ----------------
@app.get("/unlock/{lead_id}")
def unlock(lead_id: str):
    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[{"price": STRIPE_PRICE_ID, "quantity": 1}],
        success_url=f"{BASE_URL}/stripe-success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=BASE_URL,
        metadata={"lead_id": lead_id}
    )
    return RedirectResponse(session.url)

@app.get("/stripe-success")
def stripe_success(session_id: str = ""):
    session = stripe.checkout.Session.retrieve(session_id)

    if session.payment_status == "paid":
        lead_id = session.metadata.get("lead_id")

        supabase.table("leads").update({
            "unlocked": True
        }).eq("id", lead_id).execute()

        return HTMLResponse("<h1>Lead Unlocked</h1><a href='/'>Home</a>")

    return HTMLResponse("Payment failed")
