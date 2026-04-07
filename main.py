import os
import secrets
from datetime import datetime
from html import escape
from typing import Optional
from uuid import uuid4

import stripe
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware
from supabase import Client, create_client


# =========================================================
# CONFIG
# =========================================================

APP_TITLE = "LeadForge"
BASE_URL = os.getenv("BASE_URL", "https://leadforge-llc.onrender.com").rstrip("/")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "").strip()
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID", "").strip()

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "").strip()
SESSION_SECRET = os.getenv("SESSION_SECRET", "change-this-session-secret-now").strip()

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

supabase: Optional[Client] = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(title=APP_TITLE)

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
    session_cookie="leadforge_session",
    same_site="lax",
    https_only=True,
)

app.mount("/static", StaticFiles(directory="static"), name="static")


# =========================================================
# MODELS
# =========================================================

class ContractorCreate(BaseModel):
    business_name: str
    owner_name: str
    email: str
    phone: str
    service: str
    city: str
    state: str
    zip: str
    description: Optional[str] = ""
    website: Optional[str] = ""


class LeadCreate(BaseModel):
    contractor_id: str
    owner_name: str
    phone: str
    email: Optional[str] = ""
    service: str
    project_details: str
    city: str
    state: str
    zip: str


# =========================================================
# HELPERS
# =========================================================

def db_required() -> Client:
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    return supabase


def stripe_configured() -> bool:
    return bool(STRIPE_SECRET_KEY and STRIPE_PRICE_ID)


def now_iso() -> str:
    return datetime.utcnow().isoformat()


def make_token() -> str:
    return secrets.token_urlsafe(24)


def safe(value) -> str:
    if value is None:
        return ""
    return escape(str(value))


def normalize_phone(phone: str) -> str:
    return "".join(ch for ch in (phone or "") if ch.isdigit())


def html_page(title: str, body: str) -> HTMLResponse:
    return HTMLResponse(
        f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0" />
            <title>{safe(title)}</title>
            <style>
                * {{
                    box-sizing: border-box;
                }}
                body {{
                    margin: 0;
                    padding: 0;
                    font-family: Arial, Helvetica, sans-serif;
                    background: #f6f7fb;
                    color: #111827;
                }}
                .wrap {{
                    max-width: 1100px;
                    margin: 0 auto;
                    padding: 24px;
                }}
                .card {{
                    background: white;
                    border-radius: 16px;
                    padding: 22px;
                    box-shadow: 0 8px 24px rgba(0,0,0,0.06);
                    margin-bottom: 20px;
                }}
                h1, h2, h3 {{
                    margin-top: 0;
                }}
                .grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                    gap: 16px;
                }}
                .btn {{
                    display: inline-block;
                    padding: 12px 18px;
                    border-radius: 10px;
                    text-decoration: none;
                    border: none;
                    cursor: pointer;
                    font-weight: 700;
                    background: #111827;
                    color: white;
                }}
                .btn-secondary {{
                    background: #e5e7eb;
                    color: #111827;
                }}
                .btn-danger {{
                    background: #b91c1c;
                    color: white;
                }}
                .btn-success {{
                    background: #166534;
                    color: white;
                }}
                .btn-warning {{
                    background: #92400e;
                    color: white;
                }}
                .muted {{
                    color: #6b7280;
                }}
                input, textarea, select {{
                    width: 100%;
                    padding: 12px;
                    border: 1px solid #d1d5db;
                    border-radius: 10px;
                    margin-top: 6px;
                    margin-bottom: 14px;
                    font-size: 16px;
                    background: white;
                }}
                label {{
                    font-weight: 700;
                    display: block;
                    margin-top: 10px;
                }}
                .row {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 14px;
                }}
                .pill {{
                    display: inline-block;
                    padding: 6px 10px;
                    border-radius: 999px;
                    background: #eef2ff;
                    font-size: 13px;
                    font-weight: 700;
                }}
                .locked {{
                    color: #b45309;
                    font-weight: 700;
                }}
                .unlocked {{
                    color: #166534;
                    font-weight: 700;
                }}
                .topbar {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    gap: 16px;
                    margin-bottom: 20px;
                }}
                .small {{
                    font-size: 14px;
                }}
                .table-wrap {{
                    width: 100%;
                    overflow-x: auto;
                }}
                table {{
                    width: 100%;
                    min-width: 900px;
                    border-collapse: collapse;
                    margin-top: 10px;
                }}
                th, td {{
                    padding: 10px;
                    border-bottom: 1px solid #e5e7eb;
                    text-align: left;
                    vertical-align: top;
                    word-break: break-word;
                }}
                .linkbox {{
                    display: block;
                    width: 100%;
                    padding: 12px;
                    border: 1px solid #d1d5db;
                    border-radius: 10px;
                    background: #f9fafb;
                    color: #111827;
                    text-decoration: none;
                    word-break: break-all;
                }}
                @media (max-width: 700px) {{
                    .row {{
                        grid-template-columns: 1fr;
                    }}
                    .topbar {{
                        flex-direction: column;
                        align-items: flex-start;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="wrap">
                {body}
            </div>
        </body>
        </html>
        """
    )


def admin_redirect_if_not_logged_in(request: Request):
    if request.session.get("is_admin") is True:
        return None
    return RedirectResponse(url="/admin-login", status_code=303)


def get_contractors(all_rows: bool = False):
    db = db_required()
    query = db.table("contractors").select("*").order("created_at", desc=True)
    if not all_rows:
        query = query.eq("approved", True)
    result = query.execute()
    return result.data or []


def get_contractor_by_id(contractor_id: str):
    db = db_required()
    result = db.table("contractors").select("*").eq("id", contractor_id).limit(1).execute()
    rows = result.data or []
    return rows[0] if rows else None


def get_leads_by_contractor(contractor_id: str):
    db = db_required()
    result = (
        db.table("leads")
        .select("*")
        .eq("contractor_id", contractor_id)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []


def get_lead_by_id(lead_id: str):
    db = db_required()
    result = db.table("leads").select("*").eq("id", lead_id).limit(1).execute()
    rows = result.data or []
    return rows[0] if rows else None


def get_all_leads():
    db = db_required()
    result = db.table("leads").select("*").order("created_at", desc=True).execute()
    return result.data or []


def existing_active_lead(contractor_id: str, phone: str):
    normalized = normalize_phone(phone)
    if not normalized:
        return []

    leads = get_leads_by_contractor(contractor_id)
    matches = []
    for lead in leads:
        if normalize_phone(lead.get("phone", "")) == normalized:
            matches.append(lead)
    return matches


def contractor_dashboard_link(contractor: dict) -> str:
    contractor_id = contractor.get("id", "")
    token = contractor.get("access_token", "") or ""
    if not contractor_id or not token:
        return ""
    return f"{BASE_URL}/contractor/{contractor_id}?token={token}"


def ensure_contractor_token(contractor_id: str) -> str:
    contractor = get_contractor_by_id(contractor_id)
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")

    existing = contractor.get("access_token")
    if existing:
        return existing

    token = make_token()
    db = db_required()
    db.table("contractors").update({"access_token": token}).eq("id", contractor_id).execute()
    return token


def require_contractor_token(contractor: dict, token: Optional[str]) -> str:
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")

    saved_token = contractor.get("access_token")
    if not saved_token:
        raise HTTPException(
            status_code=403,
            detail="Contractor access token not set. Approve contractor again or generate token from admin."
        )

    if not token or token != saved_token:
        raise HTTPException(status_code=403, detail="Invalid contractor token")

    return saved_token


def contractor_public_card(c: dict) -> str:
    contractor_id = safe(c.get("id", ""))
    business_name = safe(c.get("business_name", "Unnamed Business"))
    service = safe(c.get("service", ""))
    city = safe(c.get("city", ""))
    state = safe(c.get("state", ""))
    description = safe(c.get("description", "") or "No description yet.")

    return f"""
    <div class="card">
        <h3>{business_name}</h3>
        <p><span class="pill">{service}</span></p>
        <p class="muted">{city}, {state}</p>
        <p>{description}</p>
        <a class="btn" href="/request/{contractor_id}">Request This Contractor</a>
    </div>
    """


def admin_login_page(error: str = "") -> HTMLResponse:
    error_html = f'<p style="color:#b91c1c;font-weight:700;">{safe(error)}</p>' if error else ""
    return html_page(
        "Admin Login",
        f"""
        <div class="topbar">
            <div>
                <h1>LeadForge Admin Login</h1>
                <p class="muted">Enter your admin password to continue.</p>
            </div>
            <a class="btn btn-secondary" href="/">Back Home</a>
        </div>

        <div class="card" style="max-width:520px;">
            {error_html}
            <form method="post" action="/admin-login">
                <label>Password</label>
                <input type="password" name="password" required />
                <button class="btn" type="submit">Login</button>
            </form>
        </div>
        """,
    )


def render_forbidden_page(title: str, message: str) -> HTMLResponse:
    return html_page(
        title,
        f"""
        <div class="card">
            <h1>{safe(title)}</h1>
            <p>{safe(message)}</p>
            <a class="btn btn-secondary" href="/">Back Home</a>
        </div>
        """,
    )


def render_admin_page(contractors: list, leads: list) -> HTMLResponse:
    contractor_rows = []
    for c in contractors:
        contractor_id = safe(c.get("id", ""))
        approved = bool(c.get("approved"))
        token = safe(c.get("access_token", "") or "")
        dashboard_link = contractor_dashboard_link(c)

        if approved and token and dashboard_link:
            dashboard_html = f"""
            <div style="margin-bottom:8px;">
                <a class="btn btn-secondary small" href="/contractor/{contractor_id}?token={token}">Open Dashboard</a>
            </div>
            <a class="linkbox" href="/contractor/{contractor_id}?token={token}">
                {safe(dashboard_link)}
            </a>
            """
        elif approved:
            dashboard_html = f"""
            <div class="muted">Approved, but no token yet.</div>
            <div style="margin-top:8px;">
                <a class="btn btn-warning small" href="/approve/{contractor_id}">Generate Token</a>
            </div>
            """
        else:
            dashboard_html = '<span class="muted">Not approved yet</span>'

        contractor_rows.append(
            f"""
            <tr>
                <td>{safe(c.get("business_name", ""))}</td>
                <td>{safe(c.get("owner_name", ""))}</td>
                <td>{safe(c.get("email", ""))}</td>
                <td>{safe(c.get("phone", ""))}</td>
                <td>{safe(c.get("service", ""))}</td>
                <td>{safe(c.get("city", ""))}, {safe(c.get("state", ""))}</td>
                <td>{"Approved" if approved else "Pending"}</td>
                <td>
                    <div style="display:flex;gap:8px;flex-wrap:wrap;">
                        <a class="btn btn-success small" href="/approve/{contractor_id}">Approve</a>
                        <a class="btn btn-danger small" href="/reject/{contractor_id}">Reject</a>
                    </div>
                </td>
                <td>{dashboard_html}</td>
            </tr>
            """
        )

    lead_rows = []
    for lead in leads:
        unlocked = bool(lead.get("unlocked"))
        lead_rows.append(
            f"""
            <tr>
                <td>{safe(lead.get("owner_name", ""))}</td>
                <td>{safe(lead.get("service", ""))}</td>
                <td>{safe(lead.get("city", ""))}, {safe(lead.get("state", ""))}</td>
                <td>{safe(lead.get("contractor_id", ""))}</td>
                <td>{"Unlocked" if unlocked else "Locked"}</td>
                <td>{safe(lead.get("phone", ""))}</td>
                <td>{safe(lead.get("email", ""))}</td>
            </tr>
            """
        )

    return html_page(
        "Admin Dashboard",
        f"""
        <div class="topbar">
            <div>
                <h1>LeadForge Admin</h1>
                <p class="muted">Protected admin dashboard</p>
            </div>
            <div>
                <a class="btn btn-secondary" href="/">Home</a>
                <a class="btn btn-danger" href="/admin-logout">Logout</a>
            </div>
        </div>

        <div class="grid">
            <div class="card">
                <h3>Total Contractors</h3>
                <p style="font-size:32px;font-weight:800;">{len(contractors)}</p>
            </div>
            <div class="card">
                <h3>Total Leads</h3>
                <p style="font-size:32px;font-weight:800;">{len(leads)}</p>
            </div>
            <div class="card">
                <h3>Stripe</h3>
                <p style="font-size:20px;font-weight:800;">{"Configured" if stripe_configured() else "Not Configured"}</p>
            </div>
        </div>

        <div class="card">
            <h2>Contractors</h2>
            <p class="muted">When you approve a contractor, a private token link is generated for their dashboard.</p>
            <div class="table-wrap">
                <table>
                    <thead>
                        <tr>
                            <th>Business</th>
                            <th>Owner</th>
                            <th>Email</th>
                            <th>Phone</th>
                            <th>Service</th>
                            <th>Location</th>
                            <th>Status</th>
                            <th>Actions</th>
                            <th>Private Dashboard Link</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(contractor_rows) if contractor_rows else '<tr><td colspan="9">No contractors found.</td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="card">
            <h2>Leads</h2>
            <div class="table-wrap">
                <table>
                    <thead>
                        <tr>
                            <th>Homeowner</th>
                            <th>Service</th>
                            <th>Location</th>
                            <th>Contractor ID</th>
                            <th>Status</th>
                            <th>Phone</th>
                            <th>Email</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(lead_rows) if lead_rows else '<tr><td colspan="7">No leads found.</td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>
        """,
    )


# =========================================================
# PUBLIC ROUTES
# =========================================================

@app.get("/")
def home():
    return FileResponse("templates/index.html")


@app.get("/health")
def health():
    return JSONResponse(
        {
            "ok": True,
            "supabase_configured": bool(SUPABASE_URL and SUPABASE_KEY),
            "stripe_configured": stripe_configured(),
            "admin_password_set": bool(ADMIN_PASSWORD),
            "timestamp": now_iso(),
        }
    )


@app.get("/contractors", response_class=HTMLResponse)
def contractors_page():
    contractors = get_contractors(all_rows=False)
    cards = "".join(contractor_public_card(c) for c in contractors)

    return html_page(
        "Approved Contractors",
        f"""
        <div class="topbar">
            <div>
                <h1>Approved Contractors</h1>
                <p class="muted">Only approved contractors are shown here.</p>
            </div>
            <a class="btn btn-secondary" href="/">Home</a>
        </div>

        <div class="grid">
            {cards if cards else '<div class="card"><p>No approved contractors available yet.</p></div>'}
        </div>
        """,
    )


@app.get("/join-contractor", response_class=HTMLResponse)
def join_contractor_form():
    return html_page(
        "Join as a Contractor",
        """
        <div class="topbar">
            <div>
                <h1>Join LeadForge</h1>
                <p class="muted">Apply to be listed and receive exclusive homeowner opportunities.</p>
            </div>
            <a class="btn btn-secondary" href="/">Home</a>
        </div>

        <div class="card">
            <form method="post" action="/join-contractor">
                <label>Business Name</label>
                <input type="text" name="business_name" required />

                <label>Owner Name</label>
                <input type="text" name="owner_name" required />

                <div class="row">
                    <div>
                        <label>Email</label>
                        <input type="email" name="email" required />
                    </div>
                    <div>
                        <label>Phone</label>
                        <input type="text" name="phone" required />
                    </div>
                </div>

                <label>Service</label>
                <input type="text" name="service" placeholder="Roofing, HVAC, Plumbing, etc." required />

                <div class="row">
                    <div>
                        <label>City</label>
                        <input type="text" name="city" required />
                    </div>
                    <div>
                        <label>State</label>
                        <input type="text" name="state" required />
                    </div>
                </div>

                <label>ZIP</label>
                <input type="text" name="zip" required />

                <label>Business Description</label>
                <textarea name="description" rows="5" placeholder="Tell homeowners about your business, experience, and service area."></textarea>

                <label>Website</label>
                <input type="text" name="website" placeholder="https://yourwebsite.com" />

                <button class="btn" type="submit">Submit Application</button>
            </form>
        </div>
        """,
    )


@app.post("/join-contractor")
def join_contractor_submit(
    business_name: str = Form(...),
    owner_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    service: str = Form(...),
    city: str = Form(...),
    state: str = Form(...),
    zip: str = Form(...),
    description: str = Form(""),
    website: str = Form(""),
):
    db = db_required()

    payload = {
        "id": str(uuid4()),
        "business_name": business_name,
        "owner_name": owner_name,
        "email": email,
        "phone": phone,
        "service": service,
        "city": city,
        "state": state,
        "zip": zip,
        "description": description or "",
        "website": website or "",
        "approved": False,
        "access_token": None,
        "created_at": now_iso(),
    }

    db.table("contractors").insert(payload).execute()

    return RedirectResponse(url="/join-contractor-success", status_code=303)


@app.get("/join-contractor-success", response_class=HTMLResponse)
def join_contractor_success():
    return html_page(
        "Application Submitted",
        """
        <div class="card">
            <h1>Application Submitted</h1>
            <p>Your contractor application was sent successfully. Once reviewed and approved, your business can be listed on LeadForge.</p>
            <a class="btn" href="/">Back Home</a>
        </div>
        """,
    )


@app.get("/request/{contractor_id}", response_class=HTMLResponse)
def request_form(contractor_id: str):
    contractor = get_contractor_by_id(contractor_id)
    if not contractor or not contractor.get("approved"):
        raise HTTPException(status_code=404, detail="Contractor not found")

    business_name = safe(contractor.get("business_name", "Contractor"))
    service = safe(contractor.get("service", ""))

    return html_page(
        "Request Contractor",
        f"""
        <div class="topbar">
            <div>
                <h1>Request {business_name}</h1>
                <p class="muted">Your request goes directly to this contractor.</p>
            </div>
            <a class="btn btn-secondary" href="/contractors">Back</a>
        </div>

        <div class="card">
            <p><strong>Service:</strong> {service}</p>
            <form method="post" action="/request/{safe(contractor_id)}">
                <label>Your Name</label>
                <input type="text" name="owner_name" required />

                <div class="row">
                    <div>
                        <label>Phone</label>
                        <input type="text" name="phone" required />
                    </div>
                    <div>
                        <label>Email</label>
                        <input type="email" name="email" />
                    </div>
                </div>

                <label>Service Needed</label>
                <input type="text" name="service" value="{service}" required />

                <label>Project Details</label>
                <textarea name="project_details" rows="5" required></textarea>

                <div class="row">
                    <div>
                        <label>City</label>
                        <input type="text" name="city" required />
                    </div>
                    <div>
                        <label>State</label>
                        <input type="text" name="state" required />
                    </div>
                </div>

                <label>ZIP</label>
                <input type="text" name="zip" required />

                <button class="btn" type="submit">Submit Request</button>
            </form>
        </div>
        """,
    )


@app.post("/request/{contractor_id}")
def submit_request(
    contractor_id: str,
    owner_name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(""),
    service: str = Form(...),
    project_details: str = Form(...),
    city: str = Form(...),
    state: str = Form(...),
    zip: str = Form(...),
):
    contractor = get_contractor_by_id(contractor_id)
    if not contractor or not contractor.get("approved"):
        raise HTTPException(status_code=404, detail="Contractor not found")

    existing = existing_active_lead(contractor_id, phone)
    if existing:
        return html_page(
            "Request Already Sent",
            """
            <div class="card">
                <h1>Request Already Sent</h1>
                <p>You already submitted a request to this contractor using this phone number.</p>
                <a class="btn" href="/contractors">Back to Contractors</a>
            </div>
            """
        )

    db = db_required()
    payload = {
        "contractor_id": contractor_id,
        "owner_name": owner_name,
        "phone": phone,
        "email": email,
        "service": service,
        "project_details": project_details,
        "city": city,
        "state": state,
        "zip": zip,
        "unlocked": False,
        "stripe_paid": False,
        "created_at": now_iso(),
    }
    db.table("leads").insert(payload).execute()

    return RedirectResponse(url="/request-success", status_code=303)


@app.get("/request-success", response_class=HTMLResponse)
def request_success():
    return html_page(
        "Request Sent",
        """
        <div class="card">
            <h1>Request Sent</h1>
            <p>Your request was submitted successfully.</p>
            <a class="btn" href="/contractors">Back to Contractors</a>
        </div>
        """,
    )


# =========================================================
# ADMIN AUTH
# =========================================================

@app.get("/admin-login", response_class=HTMLResponse)
def admin_login_get():
    return admin_login_page()


@app.post("/admin-login")
def admin_login_post(request: Request, password: str = Form(...)):
    if not ADMIN_PASSWORD:
        raise HTTPException(status_code=500, detail="ADMIN_PASSWORD is not set")

    if password != ADMIN_PASSWORD:
        return admin_login_page("Wrong password.")

    request.session["is_admin"] = True
    return RedirectResponse(url="/admin", status_code=303)


@app.get("/admin-logout")
def admin_logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/admin-login", status_code=303)


# =========================================================
# ADMIN ROUTES
# =========================================================

@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request):
    redirect = admin_redirect_if_not_logged_in(request)
    if redirect:
        return redirect

    contractors = get_contractors(all_rows=True)
    leads = get_all_leads()
    return render_admin_page(contractors, leads)


@app.get("/approve/{contractor_id}")
def approve_contractor(contractor_id: str, request: Request):
    redirect = admin_redirect_if_not_logged_in(request)
    if redirect:
        return redirect

    token = ensure_contractor_token(contractor_id)

    db = db_required()
    db.table("contractors").update(
        {
            "approved": True,
            "access_token": token,
        }
    ).eq("id", contractor_id).execute()

    return RedirectResponse(url="/admin", status_code=303)


@app.get("/reject/{contractor_id}")
def reject_contractor(contractor_id: str, request: Request):
    redirect = admin_redirect_if_not_logged_in(request)
    if redirect:
        return redirect

    db = db_required()
    db.table("contractors").update({"approved": False}).eq("id", contractor_id).execute()
    return RedirectResponse(url="/admin", status_code=303)


# =========================================================
# CONTRACTOR DASHBOARD
# =========================================================

@app.get("/contractor/{contractor_id}", response_class=HTMLResponse)
def contractor_dashboard(contractor_id: str, token: Optional[str] = None):
    contractor = get_contractor_by_id(contractor_id)
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")

    if not contractor.get("approved"):
        return render_forbidden_page(
            "Access Restricted",
            "This contractor is not approved yet."
        )

    if not token:
        return render_forbidden_page(
            "Private Access Required",
            "This page requires a valid private contractor link."
        )

    try:
        valid_token = require_contractor_token(contractor, token)
    except HTTPException:
        return render_forbidden_page(
            "Invalid Access",
            "This link is invalid or expired."
        )

    leads = get_leads_by_contractor(contractor_id)
    business_name = safe(contractor.get("business_name", "Contractor"))

    lead_cards = []
    for lead in leads:
        unlocked = bool(lead.get("unlocked"))
        lead_id = safe(lead.get("id", ""))
        status_html = '<span class="unlocked">Unlocked</span>' if unlocked else '<span class="locked">Locked</span>'

        if unlocked:
            details = f"""
            <p><strong>Homeowner:</strong> {safe(lead.get("owner_name", ""))}</p>
            <p><strong>Phone:</strong> {safe(lead.get("phone", ""))}</p>
            <p><strong>Email:</strong> {safe(lead.get("email", ""))}</p>
            <p><strong>Service:</strong> {safe(lead.get("service", ""))}</p>
            <p><strong>Project:</strong> {safe(lead.get("project_details", ""))}</p>
            <p><strong>Location:</strong> {safe(lead.get("city", ""))}, {safe(lead.get("state", ""))} {safe(lead.get("zip", ""))}</p>
            """
            action = ""
        else:
            details = f"""
            <p><strong>Homeowner:</strong> Hidden until unlock</p>
            <p><strong>Phone:</strong> Hidden until unlock</p>
            <p><strong>Email:</strong> Hidden until unlock</p>
            <p><strong>Service:</strong> {safe(lead.get("service", ""))}</p>
            <p><strong>Project:</strong> {safe(lead.get("project_details", ""))}</p>
            <p><strong>Location:</strong> {safe(lead.get("city", ""))}, {safe(lead.get("state", ""))} {safe(lead.get("zip", ""))}</p>
            """
            action = f'<a class="btn" href="/unlock/{lead_id}?token={safe(valid_token)}">Unlock for $10</a>'

        lead_cards.append(
            f"""
            <div class="card">
                <h3>{status_html}</h3>
                {details}
                {action}
            </div>
            """
        )

    return html_page(
        f"{business_name} Dashboard",
        f"""
        <div class="topbar">
            <div>
                <h1>{business_name} Lead Dashboard</h1>
                <p class="muted">Assigned homeowner opportunities</p>
            </div>
            <a class="btn btn-secondary" href="/">Home</a>
        </div>

        <div class="card">
            <p><strong>Private access active.</strong> Keep this dashboard link private.</p>
        </div>

        <div class="grid">
            {''.join(lead_cards) if lead_cards else '<div class="card"><p>No leads yet.</p></div>'}
        </div>
        """,
    )


# =========================================================
# STRIPE UNLOCK FLOW
# =========================================================

@app.get("/unlock/{lead_id}")
def unlock_lead(lead_id: str, token: Optional[str] = None):
    lead = get_lead_by_id(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    contractor_id = lead.get("contractor_id")
    if not contractor_id:
        raise HTTPException(status_code=400, detail="Lead missing contractor_id")

    contractor = get_contractor_by_id(contractor_id)
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")

    valid_token = require_contractor_token(contractor, token)

    if lead.get("unlocked"):
        return RedirectResponse(url=f"/contractor/{contractor_id}?token={valid_token}", status_code=303)

    if not stripe_configured():
        raise HTTPException(status_code=500, detail="Stripe not configured")

    success_url = f"{BASE_URL}/stripe-success?session_id={{CHECKOUT_SESSION_ID}}&token={valid_token}"
    cancel_url = f"{BASE_URL}/contractor/{contractor_id}?token={valid_token}"

    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[{"price": STRIPE_PRICE_ID, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "lead_id": str(lead_id),
            "contractor_id": str(contractor_id),
        },
    )

    return RedirectResponse(url=session.url, status_code=303)


@app.get("/stripe-success")
def stripe_success(session_id: str, token: Optional[str] = None):
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")

    session = stripe.checkout.Session.retrieve(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Stripe session not found")

    metadata = getattr(session, "metadata", {}) or {}
    lead_id = metadata.get("lead_id")
    contractor_id = metadata.get("contractor_id")

    if not lead_id or not contractor_id:
        raise HTTPException(status_code=400, detail="Missing lead metadata")

    contractor = get_contractor_by_id(contractor_id)
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")

    valid_token = require_contractor_token(contractor, token)

    payment_status = getattr(session, "payment_status", "")
    if payment_status != "paid":
        raise HTTPException(status_code=400, detail="Payment not completed")

    db = db_required()
    db.table("leads").update(
        {
            "unlocked": True,
            "stripe_paid": True,
            "stripe_session_id": session_id,
        }
    ).eq("id", lead_id).execute()

    return RedirectResponse(url=f"/contractor/{contractor_id}?token={valid_token}", status_code=303)


# =========================================================
# OPTIONAL API ROUTES
# =========================================================

@app.post("/contractors")
def create_contractor(contractor: ContractorCreate):
    db = db_required()
    payload = {
        "id": str(uuid4()),
        "business_name": contractor.business_name,
        "owner_name": contractor.owner_name,
        "email": contractor.email,
        "phone": contractor.phone,
        "service": contractor.service,
        "city": contractor.city,
        "state": contractor.state,
        "zip": contractor.zip,
        "description": contractor.description or "",
        "website": contractor.website or "",
        "approved": False,
        "access_token": None,
        "created_at": now_iso(),
    }
    result = db.table("contractors").insert(payload).execute()
    return {"ok": True, "data": result.data}


@app.post("/leads")
def create_lead_api(lead: LeadCreate):
    contractor = get_contractor_by_id(lead.contractor_id)
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")

    db = db_required()
    payload = {
        "id": str(uuid4()),
        "contractor_id": lead.contractor_id,
        "owner_name": lead.owner_name,
        "phone": lead.phone,
        "email": lead.email or "",
        "service": lead.service,
        "project_details": lead.project_details,
        "city": lead.city,
        "state": lead.state,
        "zip": lead.zip,
        "unlocked": False,
        "stripe_paid": False,
        "created_at": now_iso(),
    }
    result = db.table("leads").insert(payload).execute()
    return {"ok": True, "data": result.data}
