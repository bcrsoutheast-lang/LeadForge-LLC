from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from supabase import create_client
from datetime import datetime
from uuid import uuid4
from urllib.parse import quote_plus
import os
import html
import stripe
import hmac
import hashlib


app = FastAPI()

# -----------------------------
# ENV
# -----------------------------
SUPABASE_URL = (os.getenv("SUPABASE_URL") or "").strip()
SUPABASE_KEY = (os.getenv("SUPABASE_KEY") or "").strip()
ADMIN_PASSWORD = (os.getenv("ADMIN_PASSWORD") or "changeme").strip()
SESSION_SECRET = (os.getenv("SESSION_SECRET") or "leadforge-session-secret").strip()
BASE_URL = (os.getenv("BASE_URL") or "https://leadforge-llc.onrender.com").strip().rstrip("/")
STRIPE_SECRET_KEY = (os.getenv("STRIPE_SECRET_KEY") or "").strip()
STRIPE_PRICE_ID = (os.getenv("STRIPE_PRICE_ID") or "").strip()
ADMIN_ENTRY_ROUTE = "/VaultForge-kkc0212"
ADMIN_DASHBOARD_ROUTE = "/VaultForge-kkc0212/dashboard"

supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        supabase = None

if STRIPE_SECRET_KEY:
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
    if value is None:
        return ""
    return html.escape(str(value))


def now_iso():
    return datetime.utcnow().isoformat()


def is_admin(request: Request) -> bool:
    return request.session.get("is_admin") is True


def admin_required(request: Request):
    if not is_admin(request):
        return RedirectResponse(url=ADMIN_ENTRY_ROUTE, status_code=303)
    return None


def brand_html():
    return """
    <a class="brand-wrap" href="/">
      <div class="brand-copy">
        <span class="brand-text">VaultForge</span>
        <span class="brand-tagline">Homeowners Choose. Contractors Unlock Opportunity.</span>
      </div>
    </a>
    """


def topbar(extra_nav: str = ""):
    return f"""
    <div class="topbar">
      {brand_html()}
      <div class="nav">
        <a class="btn secondary" href="/">Home</a>
        <a class="btn secondary" href="/services">Services</a>
        <a class="btn secondary" href="/contractors">Contractors</a>
        <a class="btn secondary" href="/contact">Contact</a>
        <a class="btn secondary" href="/join-contractor">Join as a Contractor</a>
        {extra_nav}
      </div>
    </div>
    """


def layout(title: str, body: str):
    return HTMLResponse(
        f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
          <meta charset="UTF-8" />
          <meta name="viewport" content="width=device-width, initial-scale=1.0" />
          <title>{esc(title)}</title>
          <style>
            * {{
              box-sizing: border-box;
            }}
            body {{
              margin: 0;
              font-family: Arial, sans-serif;
              background:
                radial-gradient(circle at top, rgba(179, 0, 0, 0.16), transparent 30%),
                linear-gradient(180deg, #080808 0%, #040404 100%);
              color: #f5f5f5;
            }}
            .wrap {{
              max-width: 1180px;
              margin: 0 auto;
              padding: 24px;
            }}
            .topbar {{
              display: flex;
              justify-content: space-between;
              align-items: center;
              gap: 16px;
              flex-wrap: wrap;
              margin-bottom: 18px;
              padding: 10px 0 18px;
              border-bottom: 1px solid #242424;
            }}
            .brand-wrap {{
              display: inline-flex;
              align-items: center;
              gap: 14px;
              text-decoration: none;
            }}
            .brand-copy {{
              display: flex;
              flex-direction: column;
              gap: 4px;
            }}
            .brand-text {{
              font-size: 34px;
              font-weight: 900;
              letter-spacing: 0.5px;
              text-decoration: none;
              background: linear-gradient(90deg, #cc0000 0%, #ff3b2f 24%, #d4af37 62%, #f0d37a 100%);
              -webkit-background-clip: text;
              -webkit-text-fill-color: transparent;
            }}
            .brand-tagline {{
              font-size: 13px;
              color: #d4af37;
              font-weight: 700;
            }}
            .nav {{
              display: flex;
              gap: 10px;
              flex-wrap: wrap;
            }}
            .hero {{
              background: linear-gradient(135deg, #0d0d0d 0%, #141414 100%);
              border: 1px solid #242424;
              border-radius: 18px;
              padding: 34px 28px;
              margin-bottom: 24px;
              box-shadow: 0 0 0 1px rgba(255,255,255,0.02) inset, 0 0 40px rgba(204,0,0,0.08);
            }}
            h1, h2, h3 {{
              margin-top: 0;
            }}
            h1 {{
              font-size: 42px;
              line-height: 1.05;
              margin-bottom: 14px;
            }}
            h2 {{
              font-size: 28px;
            }}
            h3 {{
              font-size: 20px;
            }}
            .gold {{
              color: #d4af37;
            }}
            .red {{
              color: #cc0000;
            }}
            .muted {{
              color: #bdbdbd;
            }}
            .grid {{
              display: grid;
              gap: 18px;
            }}
            .grid-2 {{
              grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            }}
            .grid-3 {{
              grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            }}
            .card {{
              background: #0d0d0d;
              border: 1px solid #242424;
              border-radius: 16px;
              padding: 20px;
            }}
            .contractor-card {{
              display: flex;
              flex-direction: column;
              justify-content: space-between;
            }}
            .btn {{
              display: inline-block;
              background: #cc0000;
              color: white;
              text-decoration: none;
              padding: 12px 16px;
              border-radius: 10px;
              font-weight: bold;
              border: none;
              cursor: pointer;
            }}
            .btn.secondary {{
              background: #1f1f1f;
              border: 1px solid #353535;
            }}
            .btn.gold {{
              background: #d4af37;
              color: #111;
            }}
            .btn.green {{
              background: #166534;
              color: white;
            }}
            input, textarea, select {{
              width: 100%;
              box-sizing: border-box;
              padding: 12px;
              margin-top: 6px;
              margin-bottom: 14px;
              border-radius: 10px;
              border: 1px solid #333;
              background: #0a0a0a;
              color: #fff;
            }}
            label {{
              font-weight: bold;
            }}
            .topnav {{
              display: flex;
              gap: 12px;
              flex-wrap: wrap;
              margin-top: 18px;
            }}
            .pill {{
              display: inline-block;
              padding: 5px 10px;
              border-radius: 999px;
              font-size: 12px;
              font-weight: bold;
            }}
            .pill.ok {{
              background: #143d1f;
              color: #8ef0a4;
            }}
            .pill.no {{
              background: #3d1414;
              color: #ff9c9c;
            }}
            .notice {{
              background: #1a1203;
              border: 1px solid #5a4208;
              color: #f0d48a;
              border-radius: 12px;
              padding: 14px;
              margin-bottom: 16px;
            }}
            .success {{
              background: #0f2417;
              border: 1px solid #235c38;
              color: #a7f3c1;
              border-radius: 12px;
              padding: 14px;
              margin-bottom: 16px;
            }}
            .mini {{
              font-size: 14px;
              color: #c8c8c8;
              line-height: 1.5;
            }}
            .hero-kicker {{
              font-size: 18px;
              margin-bottom: 8px;
            }}
            .hero-copy {{
              max-width: 820px;
              font-size: 22px;
              line-height: 1.45;
              color: #d2d2d2;
              margin-bottom: 0;
            }}
            .section-title {{
              margin: 10px 0 16px;
            }}
            ul.clean-list {{
              padding-left: 20px;
              margin: 0;
            }}
            ul.clean-list li {{
              margin-bottom: 8px;
            }}
            .admin-stack {{
              display: grid;
              gap: 18px;
            }}
            .contractor-admin-card {{
              background: linear-gradient(135deg, #101010 0%, #151515 100%);
              border: 1px solid #2a2a2a;
              border-radius: 18px;
              padding: 22px;
            }}
            .contractor-admin-head {{
              display: flex;
              justify-content: space-between;
              align-items: flex-start;
              gap: 16px;
              flex-wrap: wrap;
              margin-bottom: 14px;
            }}
            .contractor-admin-meta {{
              display: grid;
              gap: 6px;
            }}
            .contractor-admin-actions {{
              display: flex;
              gap: 8px;
              flex-wrap: wrap;
            }}
            .leads-wrap {{
              margin-top: 18px;
              border-top: 1px solid #242424;
              padding-top: 18px;
            }}
            .lead-admin-card {{
              background: #0b0b0b;
              border: 1px solid #242424;
              border-radius: 14px;
              padding: 16px;
              margin-bottom: 12px;
            }}
            .lead-admin-grid {{
              display: grid;
              grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
              gap: 10px 16px;
              margin-bottom: 12px;
            }}
            .copy-box {{
              background: #060606;
              border: 1px solid #2e2e2e;
              border-radius: 12px;
              padding: 12px;
              font-family: monospace;
              font-size: 13px;
              color: #f3e0a0;
              white-space: pre-wrap;
              word-break: break-word;
            }}
            .premium-panel {{
              background: linear-gradient(135deg, rgba(212,175,55,0.08) 0%, rgba(204,0,0,0.08) 100%);
              border: 1px solid rgba(212,175,55,0.22);
              border-radius: 18px;
              padding: 22px;
              box-shadow: 0 0 30px rgba(212,175,55,0.06);
            }}
            .premium-title {{
              font-size: 18px;
              font-weight: 800;
              letter-spacing: 0.3px;
              margin-bottom: 10px;
            }}
            .premium-sub {{
              color: #ddd0a0;
              font-size: 14px;
              line-height: 1.5;
            }}
            .urgency-row {{
              display: flex;
              gap: 10px;
              flex-wrap: wrap;
              margin: 12px 0 16px;
            }}
            .urgency-chip {{
              display: inline-block;
              padding: 8px 12px;
              border-radius: 999px;
              font-size: 12px;
              font-weight: 800;
              letter-spacing: 0.2px;
            }}
            .urgency-chip.red {{
              background: rgba(204,0,0,0.18);
              color: #ffb2aa;
              border: 1px solid rgba(204,0,0,0.35);
            }}
            .urgency-chip.gold {{
              background: rgba(212,175,55,0.15);
              color: #f0d37a;
              border: 1px solid rgba(212,175,55,0.32);
            }}
            .lead-premium-card {{
              background: linear-gradient(135deg, #0d0d0d 0%, #151515 100%);
              border: 1px solid #272727;
              border-radius: 18px;
              padding: 22px;
              margin-bottom: 18px;
              box-shadow: 0 0 24px rgba(0,0,0,0.22);
            }}
            .lead-premium-head {{
              display: flex;
              justify-content: space-between;
              align-items: flex-start;
              gap: 14px;
              flex-wrap: wrap;
              margin-bottom: 12px;
            }}
            .lead-eyebrow {{
              color: #d4af37;
              text-transform: uppercase;
              font-size: 11px;
              font-weight: 800;
              letter-spacing: 0.6px;
              margin-bottom: 8px;
            }}
            .lead-highlight {{
              background: rgba(212,175,55,0.08);
              border: 1px solid rgba(212,175,55,0.18);
              border-radius: 14px;
              padding: 14px;
              margin: 14px 0;
            }}
            .lead-meta-grid {{
              display: grid;
              gap: 12px;
              grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
              margin-top: 14px;
            }}
            .metric-card {{
              background: #0a0a0a;
              border: 1px solid #232323;
              border-radius: 12px;
              padding: 12px;
            }}
            .cta-note {{
              color: #f0d37a;
              font-size: 13px;
              font-weight: 700;
              margin-top: 10px;
            }}
            .hero-premium-bar {{
              display: grid;
              grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
              gap: 14px;
              margin-top: 18px;
            }}
            .hero-premium-item {{
              background: rgba(255,255,255,0.03);
              border: 1px solid #242424;
              border-radius: 14px;
              padding: 14px;
            }}
            @media (max-width: 700px) {{
              h1 {{
                font-size: 32px;
              }}
              .hero-copy {{
                font-size: 18px;
              }}
              .wrap {{
                padding: 20px;
              }}
              .hero {{
                padding: 26px 20px;
              }}
              .brand-text {{
                font-size: 26px;
              }}
              .brand-tagline {{
                font-size: 12px;
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


def error_page(title: str, message: str, details: str = ""):
    detail_html = ""
    if details:
        detail_html = f'<div class="notice" style="margin-top:16px;"><strong>Details:</strong><br>{esc(details)}</div>'

    body = f"""
    {topbar()}
    <div class="hero">
      <h1>{esc(title)}</h1>
      <p class="muted">{esc(message)}</p>
      <div class="topnav">
        <a class="btn secondary" href="javascript:history.back()">Go Back</a>
        <a class="btn" href="/">Back Home</a>
      </div>
    </div>
    {detail_html}
    """
    return layout(title, body)


def normalize_service(value: str) -> str:
    return (value or "").strip().lower()


def split_services(raw_value: str):
    if not raw_value:
        return []
    return [p.strip() for p in raw_value.split(",") if p.strip()]


def contractor_matches_service(contractor: dict, service: str) -> bool:
    target = normalize_service(service)
    if not target:
        return True
    raw = contractor.get("service") or contractor.get("services") or ""
    services = [normalize_service(s) for s in split_services(raw)]
    return target in services


def fetch_contractors(include_unapproved: bool = True):
    if not supabase:
        return []
    try:
        response = supabase.table("contractors").select("*").order("created_at", desc=True).execute()
        rows = response.data or []
        if include_unapproved:
            return rows
        return [row for row in rows if row.get("approved") is True]
    except Exception:
        return []


def fetch_leads():
    if not supabase:
        return []
    try:
        response = supabase.table("leads").select("*").order("created_at", desc=True).execute()
        return response.data or []
    except Exception:
        return []

def fetch_contacts():
    if not supabase:
        return []
    try:
        response = supabase.table("contacts").select("*").order("created_at", desc=True).execute()
        return response.data or []
    except Exception:
        return []


def fetch_contractor_by_id(contractor_id: str):
    if not supabase:
        return None
    try:
        response = supabase.table("contractors").select("*").eq("id", contractor_id).limit(1).execute()
        rows = response.data or []
        return rows[0] if rows else None
    except Exception:
        return None


def fetch_leads_for_contractor(contractor_id: str):
    if not supabase:
        return []
    try:
        response = (
            supabase.table("leads")
            .select("*")
            .eq("contractor_id", contractor_id)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data or []
    except Exception:
        return []


def fetch_lead_by_id(lead_id: str):
    if not supabase:
        return None
    try:
        response = supabase.table("leads").select("*").eq("id", lead_id).limit(1).execute()
        rows = response.data or []
        return rows[0] if rows else None
    except Exception:
        return None


def unlock_lead(lead_id: str):
    if not supabase:
        return
    try:
        supabase.table("leads").update({"unlocked": True}).eq("id", lead_id).execute()
    except Exception:
        pass


def safe_insert_contractor(payload: dict):
    if not supabase:
        return False, "Supabase is not configured."

    attempts = [
        payload,
        {k: v for k, v in payload.items() if k not in {"business_description"}},
        {k: v for k, v in payload.items() if k in {"id", "full_name", "company_name", "phone", "email", "service", "city", "state", "zip", "approved", "created_at"}},
        {k: v for k, v in payload.items() if k in {"full_name", "company_name", "phone", "email", "service", "city", "state", "zip", "approved", "created_at"}},
    ]

    last_error = "Unknown contractor insert error."
    for attempt in attempts:
        try:
            supabase.table("contractors").insert(attempt).execute()
            return True, ""
        except Exception as e:
            last_error = str(e)

    return False, last_error


def safe_insert_lead(payload: dict):
    if not supabase:
        return False, "Supabase is not configured."

    attempts = [
        payload,
        {k: v for k, v in payload.items() if k not in {"chosen_contractor"}},
        {k: v for k, v in payload.items() if k not in {"chosen_contractor", "unlocked"}},
        {k: v for k, v in payload.items() if k in {"id", "contractor_id", "owner_name", "phone", "email", "service", "project_details", "city", "state", "zip", "created_at"}},
        {k: v for k, v in payload.items() if k in {"contractor_id", "owner_name", "phone", "email", "service", "project_details", "city", "state", "zip", "created_at"}},
        {k: v for k, v in payload.items() if k in {"contractor_id", "owner_name", "phone", "service", "project_details", "city", "state"}},
    ]

    last_error = "Unknown lead insert error."
    for attempt in attempts:
        try:
            supabase.table("leads").insert(attempt).execute()
            return True, ""
        except Exception as e:
            last_error = str(e)

    return False, last_error


def safe_insert_contact(payload: dict):
    if not supabase:
        return False, "Supabase is not configured."

    attempts = [
        payload,
        {k: v for k, v in payload.items() if k in {"id", "name", "email", "phone", "message", "created_at"}},
        {k: v for k, v in payload.items() if k in {"name", "email", "phone", "message", "created_at"}},
        {k: v for k, v in payload.items() if k in {"name", "email", "phone", "message"}},
    ]

    last_error = "Unknown contact insert error."
    for attempt in attempts:
        try:
            supabase.table("contacts").insert(attempt).execute()
            return True, ""
        except Exception as e:
            last_error = str(e)

    return False, last_error


def format_contractor_card(contractor: dict):
    contractor_id = esc(contractor.get("id"))
    full_name = esc(contractor.get("full_name"))
    company_name = esc(contractor.get("company_name"))
    phone = esc(contractor.get("phone"))
    email = esc(contractor.get("email"))
    service = esc(contractor.get("service") or contractor.get("services"))
    city = esc(contractor.get("city"))
    state = esc(contractor.get("state"))
    zip_code = esc(contractor.get("zip"))
    approved = "Yes" if contractor.get("approved") else "No"

    return f"""
    <div class="card contractor-card">
      <h3>{company_name or full_name or "Contractor"}</h3>
      <p><strong>Name:</strong> {full_name}</p>
      <p><strong>Phone:</strong> {phone}</p>
      <p><strong>Email:</strong> {email}</p>
      <p><strong>Service:</strong> {service}</p>
      <p><strong>Area:</strong> {city}, {state} {zip_code}</p>
      <p><strong>Approved:</strong> {approved}</p>
      <a class="btn" href="/request/{contractor_id}">Request This Contractor</a>
    </div>
    """


def format_copy_line(lead: dict):
    location = f"{lead.get('city') or ''}, {lead.get('state') or ''} {lead.get('zip') or ''}".strip()
    location = " ".join(location.split())
    parts = [
        str(lead.get("owner_name") or "").strip(),
        str(lead.get("phone") or "").strip(),
        str(lead.get("email") or "").strip(),
        str(lead.get("service") or "").strip(),
        location,
    ]
    return " | ".join([p for p in parts if p])


def stripe_ready() -> bool:
    return bool(STRIPE_SECRET_KEY and STRIPE_PRICE_ID)




def generate_dashboard_token(contractor_id: str) -> str:
    contractor_id = str(contractor_id or "").strip()
    secret = SESSION_SECRET or "vaultforge-dashboard-secret"
    if not contractor_id:
        return ""
    return hmac.new(secret.encode("utf-8"), contractor_id.encode("utf-8"), hashlib.sha256).hexdigest()


def contractor_dashboard_url(contractor_id: str) -> str:
    contractor_id = str(contractor_id or "").strip()
    token = generate_dashboard_token(contractor_id)
    if not contractor_id or not token:
        return "/contractors"
    return f"/contractor/{quote_plus(contractor_id)}?token={quote_plus(token)}"


def contractor_token_valid(contractor_id: str, token: str) -> bool:
    expected = generate_dashboard_token(contractor_id)
    provided = str(token or "").strip()
    if not expected or not provided:
        return False
    return hmac.compare_digest(expected, provided)


def stripe_metadata_to_dict(metadata):
    if metadata is None:
        return {}
    if isinstance(metadata, dict):
        return metadata
    try:
        return dict(metadata)
    except Exception:
        try:
            return {k: metadata[k] for k in metadata.keys()}
        except Exception:
            return {}


def stripe_attr(obj, name, default=None):
    if obj is None:
        return default
    try:
        value = getattr(obj, name)
        if value is not None:
            return value
    except Exception:
        pass
    try:
        value = obj.get(name)
        if value is not None:
            return value
    except Exception:
        pass
    try:
        value = obj[name]
        if value is not None:
            return value
    except Exception:
        pass
    return default


# -----------------------------
# ROUTES
# -----------------------------
@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/contact", response_class=HTMLResponse)
def contact_form():
    body = f"""
    {topbar()}
    <div class="hero">
      <h1>Contact VaultForge</h1>
      <p class="muted">Questions, support, partnership inquiries, or general business contact.</p>
      <p class="mini">
        Send us a message and we will review it as soon as possible.
      </p>
    </div>

    <div class="card">
      <form method="post" action="/contact">
        <label>Name</label>
        <input name="name" required>

        <label>Email</label>
        <input type="email" name="email" required>

        <label>Phone</label>
        <input name="phone">

        <label>Message</label>
        <textarea name="message" rows="6" required></textarea>

        <button class="btn gold" type="submit">Send Message</button>
      </form>
    </div>
    """
    return layout("Contact VaultForge", body)


@app.post("/contact")
def contact_submit(
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(""),
    message: str = Form(...),
):
    payload = {
        "id": str(uuid4()),
        "name": name.strip(),
        "email": email.strip(),
        "phone": phone.strip(),
        "message": message.strip(),
        "created_at": now_iso(),
    }

    ok, error = safe_insert_contact(payload)
    if not ok:
        return error_page(
            "Contact Form Error",
            "We could not save your message right now.",
            error,
        )

    return RedirectResponse(url="/contact-success", status_code=303)


@app.get("/contact-success", response_class=HTMLResponse)
def contact_success():
    body = f"""
    {topbar()}
    <div class="hero">
      <h1>Message Received</h1>
      <p class="muted">Your message has been sent to VaultForge.</p>
      <p class="mini">We will review it and follow up using the information you submitted.</p>
      <div class="topnav">
        <a class="btn" href="/">Back Home</a>
        <a class="btn secondary" href="/contact">Send Another Message</a>
      </div>
    </div>
    """
    return layout("Contact Submitted", body)


@app.get("/", response_class=HTMLResponse)
def homepage():
    body = f"""
    {topbar()}

    <div class="hero">
      <div class="hero-kicker gold"><strong>Exclusive Opportunities. Real Homeowners. No Competition.</strong></div>
      <h1><span class="red">Homeowners Choose.</span><br><span class="gold">Contractors Unlock Opportunity.</span></h1>
      <p class="hero-copy">
        VaultForge connects homeowners with vetted contractors through a cleaner, more controlled system.
        Homeowners choose one contractor. Contractors unlock real opportunities without getting buried in bidding wars.
      </p>
      <div class="topnav">
        <a class="btn" href="/services">Find a Contractor</a>
        <a class="btn gold" href="/join-contractor">Join as a Contractor</a>
      </div>
    </div>

    <div class="grid grid-2">
      <div class="card">
        <h2>For Homeowners</h2>
        <p class="mini">
          Browse by service, review approved contractors, and send one direct request to the company
          you actually want to talk to.
        </p>
        <a class="btn" href="/services">Browse Services</a>
      </div>

      <div class="card">
        <h2>For Contractors</h2>
        <p class="mini">
          VaultForge is built for legitimate contractors who want real homeowner opportunities.
          Approved contractors can unlock exclusive request details for a flat $10 access fee.
        </p>
        <a class="btn gold" href="/join-contractor">Apply Now</a>
      </div>
    </div>

    <div class="card" style="margin-top:22px;">
      <h2 class="section-title">How VaultForge Works</h2>
      <div class="grid grid-3">
        <div class="card">
          <h3>1. Homeowner Chooses a Service</h3>
          <p class="mini">
            Roofing, siding, gutters, painting, flooring, plumbing, electrical, HVAC,
            landscaping, remodeling, and more.
          </p>
        </div>
        <div class="card">
          <h3>2. Homeowner Picks One Contractor</h3>
          <p class="mini">
            Homeowners choose a specific contractor instead of sending the same lead to a pile of companies.
          </p>
        </div>
        <div class="card">
          <h3>3. Contractor Unlocks the Homeowner Request</h3>
          <p class="mini">
            The contractor sees the request, knows it was sent to one chosen contractor, and can unlock full homeowner details for $10.
          </p>
        </div>
      </div>
    </div>

    <div class="grid grid-2" style="margin-top:22px;">
      <div class="card">
        <h2>Our contractor vetting process</h2>
        <p class="mini">
          We want homeowners to feel confident using VaultForge, and we want legitimate contractors
          to know exactly what approval means.
        </p>
        <ul class="clean-list mini">
          <li>Business information is reviewed before approval.</li>
          <li>We look for contractors that present themselves professionally and clearly.</li>
          <li>Registered business status matters.</li>
          <li>Licensing matters where required for the trade and area served.</li>
          <li>Insurance matters.</li>
          <li>Only approved contractors are shown in the homeowner directory.</li>
        </ul>
      </div>

      <div class="card">
        <h2>Transparency for contractors</h2>
        <p class="mini">
          VaultForge is not trying to create a hard time for good contractors. The approval process is here
          to keep the platform cleaner, protect homeowner trust, and give legitimate businesses a better-quality
          marketplace.
        </p>
        <p class="mini">
          If a contractor is registered, properly licensed where needed, insured, and operating professionally,
          the vetting process should feel straightforward, not unfair.
        </p>
      </div>
    </div>
    """
    return layout("VaultForge", body)


@app.get("/services", response_class=HTMLResponse)
def services():
    items = [
        "roofing",
        "siding",
        "gutters",
        "painting",
        "flooring",
        "plumbing",
        "electrical",
        "hvac",
        "landscaping",
        "remodeling",
    ]

    cards = "".join(
        f"""
        <div class="card">
          <h3>{esc(item.title())}</h3>
          <p class="mini">Find approved {esc(item)} contractors in your area.</p>
          <a class="btn" href="/contractors?service={esc(item)}">View {esc(item.title())}</a>
        </div>
        """
        for item in items
    )

    body = f"""
    {topbar()}
    <div class="hero">
      <h1>Choose a Service</h1>
      <p class="muted">Start by selecting the type of contractor you need.</p>
    </div>
    <div class="grid grid-2">
      {cards}
    </div>
    """
    return layout("Services", body)


@app.get("/contractors", response_class=HTMLResponse)
def contractors(service: str = ""):
    rows = fetch_contractors(include_unapproved=False)
    if service:
        rows = [row for row in rows if contractor_matches_service(row, service)]

    cards = "".join(format_contractor_card(row) for row in rows)

    if not cards:
        cards = """
        <div class="card">
          <h3>No contractors found</h3>
          <p class="mini">Try another service category or check back soon.</p>
          <a class="btn secondary" href="/services">Back to Services</a>
        </div>
        """

    heading = f"Approved Contractors{' - ' + service.title() if service else ''}"

    body = f"""
    {topbar()}
    <div class="hero">
      <h1>{esc(heading)}</h1>
      <p class="muted">Browse approved contractors and choose one to request.</p>
    </div>
    <div class="grid grid-2">
      {cards}
    </div>
    """
    return layout("Contractors", body)


@app.get("/join-contractor", response_class=HTMLResponse)
def join_contractor_form():
    body = f"""
    {topbar()}
    <div class="hero">
      <h1>Apply to Join VaultForge</h1>
      <p class="muted">Join free and get access to exclusive homeowner opportunities.</p>
      <p class="mini">
        Contractors that present themselves professionally, operate legitimately, and meet approval
        standards have a better shot at being accepted into the directory.
      </p>
    </div>

    <div class="card">
      <form method="post" action="/join-contractor">
        <label>Full Name</label>
        <input name="full_name" required>

        <label>Company Name</label>
        <input name="company_name" required>

        <label>Phone</label>
        <input name="phone" required>

        <label>Email</label>
        <input type="email" name="email" required>

        <label>Services Offered (comma separated)</label>
        <input name="service" placeholder="Roofing, Gutters, Siding" required>

        <label>City</label>
        <input name="city" required>

        <label>State</label>
        <input name="state" required>

        <label>ZIP Code</label>
        <input name="zip" required>

        <label>Business Description</label>
        <textarea name="business_description" rows="5"></textarea>

        <button class="btn gold" type="submit">Submit Contractor Application</button>
      </form>
    </div>
    """
    return layout("Join Contractor", body)


@app.post("/join-contractor")
def join_contractor_submit(
    full_name: str = Form(...),
    company_name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    service: str = Form(...),
    city: str = Form(...),
    state: str = Form(...),
    zip: str = Form(...),
    business_description: str = Form(""),
):
    contractor_id = str(uuid4())
    payload = {
        "id": contractor_id,
        "full_name": full_name.strip(),
        "company_name": company_name.strip(),
        "phone": phone.strip(),
        "email": email.strip(),
        "service": service.strip(),
        "city": city.strip(),
        "state": state.strip(),
        "zip": zip.strip(),
        "business_description": business_description.strip(),
        "approved": False,
        "created_at": now_iso(),
    }

    ok, error = safe_insert_contractor(payload)
    if not ok:
        return error_page(
            "Contractor Application Error",
            "We could not save the contractor application right now.",
            error,
        )

    return RedirectResponse(url="/join-contractor-success", status_code=303)


@app.get("/join-contractor-success", response_class=HTMLResponse)
def join_contractor_success():
    body = f"""
    {topbar()}
    <div class="hero">
      <h1>Application Submitted</h1>
      <p class="muted">Your contractor application has been received and is waiting for admin approval.</p>
      <a class="btn" href="/">Back Home</a>
    </div>
    """
    return layout("Application Submitted", body)


@app.get("/request/{contractor_id}", response_class=HTMLResponse)
def request_form(contractor_id: str):
    contractor = fetch_contractor_by_id(contractor_id)

    if not contractor:
        return HTMLResponse("Contractor not found.", status_code=404)

    if contractor.get("approved") is not True:
        return HTMLResponse("Contractor not found.", status_code=404)

    company_name = contractor.get("company_name") or contractor.get("full_name") or "Contractor"
    city = contractor.get("city") or ""
    state = contractor.get("state") or ""
    service = contractor.get("service") or contractor.get("services") or ""

    body = f"""
    {topbar()}
    <div class="hero">
      <h1>Request Contractor</h1>
      <p class="muted">You are sending one exclusive request to <strong>{esc(company_name)}</strong>.</p>
      <p class="muted">Service area: {esc(city)}, {esc(state)}</p>
      <p class="muted">Services: {esc(service)}</p>
    </div>

    <div class="card">
      <form method="post" action="/request/{esc(contractor_id)}">
        <label>Your Name</label>
        <input name="owner_name" required>

        <label>Phone</label>
        <input name="phone" required>

        <label>Email</label>
        <input type="email" name="email" required>

        <label>City</label>
        <input name="city" required>

        <label>State</label>
        <input name="state" required>

        <label>ZIP Code</label>
        <input name="zip" required>

        <label>Service Needed</label>
        <input name="service" value="{esc(service)}" required>

        <label>Project Details</label>
        <textarea name="project_details" rows="5" required></textarea>

        <button class="btn" type="submit">Submit Request</button>
      </form>
    </div>
    """
    return layout("Request Contractor", body)


@app.post("/request/{contractor_id}")
def request_submit(
    contractor_id: str,
    owner_name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    city: str = Form(...),
    state: str = Form(...),
    zip: str = Form(...),
    service: str = Form(...),
    project_details: str = Form(...),
):
    contractor = fetch_contractor_by_id(contractor_id)
    if not contractor or contractor.get("approved") is not True:
        return HTMLResponse("Contractor not found.", status_code=404)

    lead_id = str(uuid4())
    payload = {
        "id": lead_id,
        "contractor_id": contractor_id,
        "owner_name": owner_name.strip(),
        "phone": phone.strip(),
        "email": email.strip(),
        "city": city.strip(),
        "state": state.strip(),
        "zip": zip.strip(),
        "service": service.strip(),
        "project_details": project_details.strip(),
        "chosen_contractor": contractor.get("company_name") or contractor.get("full_name") or "",
        "unlocked": False,
        "created_at": now_iso(),
    }

    ok, error = safe_insert_lead(payload)
    if not ok:
        return error_page("Request Error", error)

    return RedirectResponse(url="/request-success", status_code=303)


@app.get("/request-success", response_class=HTMLResponse)
def request_success():
    return layout("Success", f"""
    {topbar()}
    <h1>Request Sent</h1>
    <a href="/">Back Home</a>
    """)


# -----------------------------
# STRIPE
# -----------------------------
@app.get("/unlock/{lead_id}")
def unlock_checkout(lead_id: str, token: str = ""):
    lead = fetch_lead_by_id(lead_id)
    if not lead:
        return HTMLResponse("Lead not found.", status_code=404)

    if not stripe_ready():
        return error_page(
            "Stripe Not Configured",
            "Stripe is missing a secret key or price ID in Render environment variables.",
            "Check STRIPE_SECRET_KEY and STRIPE_PRICE_ID.",
        )

    contractor_id = str(lead.get("contractor_id") or "").strip()

    if not contractor_token_valid(contractor_id, token):
        return error_page(
            "Access Denied",
            "This contractor dashboard link is missing a valid access token.",
            "Use the protected dashboard link from admin.",
        )

    success_url = (
        f"{BASE_URL}/stripe-success"
        f"?session_id={{CHECKOUT_SESSION_ID}}"
        f"&lead_id={quote_plus(str(lead_id))}"
        f"&contractor_id={quote_plus(contractor_id)}"
        f"&token={quote_plus(token)}"
    )

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[{"price": STRIPE_PRICE_ID, "quantity": 1}],
            success_url=success_url,
            cancel_url=f"{BASE_URL}{contractor_dashboard_url(contractor_id)}",
            metadata={
                "lead_id": str(lead_id),
                "contractor_id": contractor_id,
            },
        )
        return RedirectResponse(url=session.url, status_code=303)
    except Exception as e:
        return error_page(
            "Stripe Checkout Error",
            "We could not create the Stripe checkout session.",
            str(e),
        )


@app.get("/stripe-success", response_class=HTMLResponse)
def stripe_success(session_id: str = "", lead_id: str = "", contractor_id: str = "", token: str = ""):
    if not session_id:
        return error_page(
            "Stripe Success Error",
            "Stripe returned to the site without a checkout session ID.",
            "Missing session_id in the success URL.",
        )

    if not STRIPE_SECRET_KEY:
        return error_page(
            "Stripe Not Configured",
            "Stripe secret key is missing on the server.",
            "Add STRIPE_SECRET_KEY in Render environment variables.",
        )

    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except Exception as e:
        return error_page(
            "Stripe Session Error",
            "We could not retrieve the Stripe checkout session.",
            str(e),
        )

    payment_status = str(stripe_attr(session, "payment_status", "") or "").strip().lower()
    session_status = str(stripe_attr(session, "status", "") or "").strip().lower()

    if payment_status == "paid" or session_status == "complete":
        if lead_id:
            unlock_lead(lead_id)

        lead = fetch_lead_by_id(lead_id) if lead_id else None

        if not contractor_id and lead:
            contractor_id = str(lead.get("contractor_id") or "").strip()

        homeowner_name = esc(lead.get("owner_name") if lead else "")
        homeowner_phone = esc(lead.get("phone") if lead else "")
        homeowner_email = esc(lead.get("email") if lead else "")
        homeowner_service = esc(lead.get("service") if lead else "")
        homeowner_project = esc(lead.get("project_details") if lead else "")

        if lead:
            detail_box = f"""
            <div class="success">
              <strong>Name:</strong> {homeowner_name or "Saved"}<br>
              <strong>Phone:</strong> {homeowner_phone or "-"}<br>
              <strong>Email:</strong> {homeowner_email or "-"}<br>
              <strong>Service:</strong> {homeowner_service or "-"}<br>
              <strong>Project:</strong> {homeowner_project or "-"}
            </div>
            """
        else:
            detail_box = """
            <div class="success">
              Payment completed successfully. The lead unlock has been processed.
            </div>
            """

        dashboard_button = (
            f'<a class="btn gold" href="{esc(contractor_dashboard_url(contractor_id))}">Back to Dashboard</a>'
            if contractor_id
            else '<a class="btn gold" href="/">Back Home</a>'
        )

        body = f"""
        {topbar()}
        <div class="hero">
          <h1>Lead Unlocked</h1>
          <p class="muted">Payment completed and the homeowner request is now unlocked for your business.</p>
          {detail_box}
          <div class="topnav">
            {dashboard_button}
            <a class="btn secondary" href="/">Back Home</a>
          </div>
        </div>
        """
        return layout("Unlocked", body)

    return error_page(
        "Payment Error",
        "Stripe did not confirm a completed payment for this session.",
        f"payment_status={payment_status or 'unknown'} | status={session_status or 'unknown'}",
    )


@app.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    try:
        data = await request.json()
        event = stripe.Event.construct_from(data, stripe.api_key)

        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            metadata = stripe_metadata_to_dict(session.get("metadata") or {})
            lead_id = metadata.get("lead_id")
            if lead_id:
                unlock_lead(str(lead_id))

        return {"status": "ok"}
    except Exception:
        return {"status": "ignored"}


@app.get(ADMIN_ENTRY_ROUTE, response_class=HTMLResponse)
def admin_login_form(error: str = ""):
    error_html = f'<div class="notice">{esc(error)}</div>' if error else ""
    body = f"""
    {topbar()}
    <div class="hero">
      <h1>Admin Login</h1>
      <p class="muted">This area is now protected.</p>
    </div>

    {error_html}

    <div class="card" style="max-width:520px;">
      <form method="post" action="{ADMIN_ENTRY_ROUTE}">
        <label>Admin Password</label>
        <input type="password" name="password" required>
        <button class="btn" type="submit">Login</button>
      </form>
    </div>
    """
    return layout("Admin Login", body)


@app.post(ADMIN_ENTRY_ROUTE)
def admin_login(request: Request, password: str = Form(...)):
    if password == ADMIN_PASSWORD:
        request.session["is_admin"] = True
        return RedirectResponse(url=ADMIN_DASHBOARD_ROUTE, status_code=303)

    return RedirectResponse(url=f"{ADMIN_ENTRY_ROUTE}?error=Wrong+password", status_code=303)



@app.get("/admin")
def admin_decoy():
    return RedirectResponse(url="/", status_code=303)


@app.get("/admin-login")
def admin_login_decoy():
    return RedirectResponse(url="/", status_code=303)


@app.get("/admin-logout")
def admin_logout(request: Request):
    request.session.clear()
    return RedirectResponse(url=ADMIN_ENTRY_ROUTE, status_code=303)


# -----------------------------
# ADMIN
# -----------------------------
@app.get(ADMIN_DASHBOARD_ROUTE, response_class=HTMLResponse)
def admin_dashboard(request: Request):
    guard = admin_required(request)
    if guard:
        return guard

    contractors = fetch_contractors(include_unapproved=True)
    leads = fetch_leads()
    contacts = fetch_contacts()

    leads_by_contractor = {}
    orphan_leads = []

    for lead in leads:
        contractor_id = str(lead.get("contractor_id") or "").strip()
        if contractor_id:
            leads_by_contractor.setdefault(contractor_id, []).append(lead)
        else:
            orphan_leads.append(lead)

    contractor_cards = []

    for contractor in contractors:
        contractor_id_raw = str(contractor.get("id") or "").strip()
        cid = esc(contractor_id_raw)
        approved = contractor.get("approved") is True
        approved_badge = '<span class="pill ok">Approved</span>' if approved else '<span class="pill no">Pending</span>'

        contractor_name = contractor.get("company_name") or contractor.get("full_name") or "Contractor"
        contractor_leads = leads_by_contractor.get(contractor_id_raw, [])

        if contractor_leads:
            blocks = []
            for lead in contractor_leads:
                unlocked = lead.get("unlocked") is True
                unlocked_badge = '<span class="pill ok">Unlocked</span>' if unlocked else '<span class="pill no">Locked</span>'
                copy_line = esc(format_copy_line(lead))

                blocks.append(
                    f"""
                    <div class="lead-admin-card">
                      <div style="display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; margin-bottom:10px;">
                        <div>
                          <strong>{esc(lead.get("owner_name") or "Homeowner Lead")}</strong>
                        </div>
                        <div>
                          {unlocked_badge}
                        </div>
                      </div>

                      <div class="lead-admin-grid">
                        <div><strong>Created:</strong><br>{esc(lead.get("created_at"))}</div>
                        <div><strong>Lead ID:</strong><br>{esc(lead.get("id"))}</div>
                        <div><strong>Phone:</strong><br>{esc(lead.get("phone"))}</div>
                        <div><strong>Email:</strong><br>{esc(lead.get("email"))}</div>
                        <div><strong>Service:</strong><br>{esc(lead.get("service"))}</div>
                        <div><strong>City:</strong><br>{esc(lead.get("city"))}</div>
                        <div><strong>State:</strong><br>{esc(lead.get("state"))}</div>
                        <div><strong>ZIP:</strong><br>{esc(lead.get("zip"))}</div>
                      </div>

                      <div style="margin-bottom:10px;">
                        <strong>Project Details:</strong><br>
                        <span class="mini">{esc(lead.get("project_details"))}</span>
                      </div>

                      <div>
                        <strong>Copy / Text Line:</strong>
                        <div class="copy-box">{copy_line}</div>
                      </div>
                    </div>
                    """
                )
            lead_html = "".join(blocks)
        else:
            lead_html = """
            <div class="lead-admin-card">
              <p class="mini" style="margin:0;">No leads yet.</p>
            </div>
            """

        contractor_cards.append(
            f"""
            <div class="contractor-admin-card">
              <div class="contractor-admin-head">
                <div class="contractor-admin-meta">
                  <h2 style="margin-bottom:6px;">{esc(contractor_name)}</h2>
                  <div>{approved_badge}</div>
                  <div class="mini"><strong>Name:</strong> {esc(contractor.get("full_name"))}</div>
                  <div class="mini"><strong>Phone:</strong> {esc(contractor.get("phone"))}</div>
                  <div class="mini"><strong>Email:</strong> {esc(contractor.get("email"))}</div>
                  <div class="mini"><strong>Service:</strong> {esc(contractor.get("service") or contractor.get("services"))}</div>
                  <div class="mini"><strong>Area:</strong> {esc(contractor.get("city"))}, {esc(contractor.get("state"))} {esc(contractor.get("zip"))}</div>
                  <div class="mini"><strong>Contractor ID:</strong> {cid}</div>
                  <div class="mini"><strong>Created:</strong> {esc(contractor.get("created_at"))}</div>
                  <div class="mini"><strong>Protected Dashboard Link:</strong></div>
                  <div class="copy-box">{esc(BASE_URL + contractor_dashboard_url(contractor_id_raw))}</div>
                </div>

                <div class="contractor-admin-actions">
                  <a class="btn" href="/approve/{cid}">Approve</a>
                  <a class="btn secondary" href="/reject/{cid}">Reject</a>
                  <a class="btn gold" href="{esc(contractor_dashboard_url(contractor_id_raw))}" target="_blank">Dashboard</a>
                </div>
              </div>

              <div class="leads-wrap">
                <h3 style="margin-bottom:12px;">Assigned Homeowner Leads ({len(contractor_leads)})</h3>
                {lead_html}
              </div>
            </div>
            """
        )

    contact_html = ""
    if contacts:
        contact_blocks = []
        for contact in contacts:
            contact_blocks.append(
                f"""
                <div class="lead-admin-card">
                  <div style="display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; margin-bottom:10px;">
                    <div><strong>{esc(contact.get("name") or "Contact Message")}</strong></div>
                    <div><span class="pill ok">Contact</span></div>
                  </div>
                  <div class="lead-admin-grid">
                    <div><strong>Created:</strong><br>{esc(contact.get("created_at"))}</div>
                    <div><strong>Contact ID:</strong><br>{esc(contact.get("id"))}</div>
                    <div><strong>Email:</strong><br>{esc(contact.get("email"))}</div>
                    <div><strong>Phone:</strong><br>{esc(contact.get("phone"))}</div>
                  </div>
                  <div>
                    <strong>Message:</strong><br>
                    <span class="mini">{esc(contact.get("message"))}</span>
                  </div>
                </div>
                """
            )

        contact_html = f"""
        <div class="card" style="margin-bottom:20px;">
          <h2>Contact Messages</h2>
          <p class="mini">Messages submitted through the Contact page.</p>
          {''.join(contact_blocks)}
        </div>
        """
    else:
        contact_html = """
        <div class="card" style="margin-bottom:20px;">
          <h2>Contact Messages</h2>
          <p class="mini" style="margin:0;">No contact messages yet.</p>
        </div>
        """

    orphan_html = ""
    if orphan_leads:
        blocks = []
        for lead in orphan_leads:
            copy_line = esc(format_copy_line(lead))
            unlocked = lead.get("unlocked") is True
            unlocked_badge = '<span class="pill ok">Unlocked</span>' if unlocked else '<span class="pill no">Locked</span>'

            blocks.append(
                f"""
                <div class="lead-admin-card">
                  <div style="display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; margin-bottom:10px;">
                    <div><strong>{esc(lead.get("owner_name") or "Homeowner Lead")}</strong></div>
                    <div>{unlocked_badge}</div>
                  </div>
                  <div class="lead-admin-grid">
                    <div><strong>Lead ID:</strong><br>{esc(lead.get("id"))}</div>
                    <div><strong>Contractor ID:</strong><br>{esc(lead.get("contractor_id"))}</div>
                    <div><strong>Chosen Contractor:</strong><br>{esc(lead.get("chosen_contractor"))}</div>
                    <div><strong>Phone:</strong><br>{esc(lead.get("phone"))}</div>
                    <div><strong>Email:</strong><br>{esc(lead.get("email"))}</div>
                    <div><strong>Service:</strong><br>{esc(lead.get("service"))}</div>
                  </div>
                  <div>
                    <strong>Copy / Text Line:</strong>
                    <div class="copy-box">{copy_line}</div>
                  </div>
                </div>
                """
            )

        orphan_html = f"""
        <div class="card" style="margin-top:20px;">
          <h2>Unmatched / Orphan Leads</h2>
          <p class="mini">These leads did not match a loaded contractor card by contractor_id.</p>
          {''.join(blocks)}
        </div>
        """

    body = f"""
    {topbar(f'<a class="btn secondary" href="/admin-logout">Logout</a>')}

    <div class="hero">
      <h1>VaultForge Admin</h1>
      <p class="muted">
        Contractors are now grouped with their assigned homeowner leads directly underneath.
      </p>
      <div class="topnav">
        <span class="pill ok">Contractors: {len(contractors)}</span>
        <span class="pill no">Leads: {len(leads)}</span>
        <span class="pill ok">Contacts: {len(contacts)}</span>
      </div>
    </div>

    {contact_html}

    <div class="admin-stack">
      {''.join(contractor_cards) if contractor_cards else '<div class="card"><p>No contractors found.</p></div>'}
    </div>

    {orphan_html}
    """
    return layout("VaultForge Admin", body)


@app.get("/approve/{contractor_id}")
def approve_contractor(contractor_id: str, request: Request):
    guard = admin_required(request)
    if guard:
        return guard

    if not supabase:
        return HTMLResponse("Supabase is not configured.", status_code=500)

    try:
        supabase.table("contractors").update({"approved": True}).eq("id", contractor_id).execute()
    except Exception as e:
        return error_page("Approve Error", "Could not approve contractor.", str(e))

    return RedirectResponse(url=ADMIN_DASHBOARD_ROUTE, status_code=303)


@app.get("/reject/{contractor_id}")
def reject_contractor(contractor_id: str, request: Request):
    guard = admin_required(request)
    if guard:
        return guard

    if not supabase:
        return HTMLResponse("Supabase is not configured.", status_code=500)

    try:
        supabase.table("contractors").delete().eq("id", contractor_id).execute()
    except Exception as e:
        return error_page("Reject Error", "Could not reject contractor.", str(e))

    return RedirectResponse(url=ADMIN_DASHBOARD_ROUTE, status_code=303)


# -----------------------------
# CONTRACTOR DASHBOARD
# -----------------------------
@app.get("/contractor/{contractor_id}", response_class=HTMLResponse)
def contractor_dashboard(contractor_id: str, token: str = ""):
    contractor = fetch_contractor_by_id(contractor_id)
    if not contractor:
        return HTMLResponse("Contractor not found.", status_code=404)

    if not contractor_token_valid(contractor_id, token):
        return error_page(
            "Access Denied",
            "This contractor dashboard is protected.",
            "Use the private contractor dashboard link from admin.",
        )

    leads = fetch_leads_for_contractor(contractor_id)
    locked_count = sum(1 for lead in leads if lead.get("unlocked") is not True)
    unlocked_count = sum(1 for lead in leads if lead.get("unlocked") is True)

    lead_cards = []
    for lead in leads:
        unlocked = lead.get("unlocked") is True
        lead_id = esc(lead.get("id"))
        service_name = esc(lead.get("service") or "Requested Service")
        project_text = esc(lead.get("project_details") or "")
        created_at = esc(lead.get("created_at") or "")
        location_line = f"{esc(lead.get('city') or '')}, {esc(lead.get('state') or '')} {esc(lead.get('zip') or '')}".strip()
        location_line = " ".join(location_line.split())

        if unlocked:
            details = f"""
            <div class="lead-highlight">
              <strong>Homeowner unlocked successfully.</strong><br>
              You now have full contact details for this exclusive request.
            </div>

            <div class="lead-meta-grid">
              <div class="metric-card"><strong>Name</strong><br>{esc(lead.get("owner_name"))}</div>
              <div class="metric-card"><strong>Phone</strong><br>{esc(lead.get("phone"))}</div>
              <div class="metric-card"><strong>Email</strong><br>{esc(lead.get("email"))}</div>
              <div class="metric-card"><strong>Location</strong><br>{location_line}</div>
            </div>

            <div style="margin-top:14px;">
              <strong>Service:</strong> {service_name}<br>
              <strong>Project:</strong> {project_text}
            </div>
            """
            action_button = ""
            status_badge = '<span class="pill ok">Unlocked</span>'
        else:
            details = f"""
            <div class="urgency-row">
              <span class="urgency-chip red">Exclusive homeowner request</span>
              <span class="urgency-chip gold">Recommended to unlock soon</span>
            </div>

            <div class="lead-highlight">
              <strong>{service_name}</strong><br>
              {project_text}
            </div>

            <p class="mini">
              Unlock this homeowner request for <strong>$10</strong> to view the homeowner's name, phone, email,
              and full contact details. This is built to help you move fast without getting buried in a bidding war.
            </p>
            <p class="cta-note">Suggested action: unlock promptly so you can reach the homeowner while the request is fresh.</p>
            """
            action_button = f'<a class="btn gold" href="/unlock/{lead_id}?token={quote_plus(token)}">Unlock Homeowner Request - $10</a>'
            status_badge = '<span class="pill no">Locked</span>'

        lead_cards.append(
            f"""
            <div class="lead-premium-card">
              <div class="lead-premium-head">
                <div>
                  <div class="lead-eyebrow">Exclusive opportunity</div>
                  <h3 style="margin-bottom:6px;">{service_name}</h3>
                  <div class="mini">Lead ID: {lead_id}</div>
                  <div class="mini">Received: {created_at}</div>
                </div>
                <div>{status_badge}</div>
              </div>

              {details}

              <div class="topnav">
                {action_button}
              </div>
            </div>
            """
        )

    company_display = esc(contractor.get("company_name") or contractor.get("full_name"))
    body = f"""
    {topbar()}
    <div class="hero premium-panel">
      <h1>{company_display}</h1>
      <p class="muted">Private contractor dashboard</p>
      <p class="muted">This dashboard is protected by a private access token link.</p>

      <div class="hero-premium-bar">
        <div class="hero-premium-item">
          <div class="premium-title">Locked Requests</div>
          <div class="premium-sub">{locked_count} request(s) waiting to be unlocked.</div>
        </div>
        <div class="hero-premium-item">
          <div class="premium-title">Unlocked Requests</div>
          <div class="premium-sub">{unlocked_count} request(s) already opened.</div>
        </div>
        <div class="hero-premium-item">
          <div class="premium-title">How to Win Faster</div>
          <div class="premium-sub">Unlock quickly, call fast, and be the first contractor to reach the homeowner.</div>
        </div>
      </div>
    </div>

    <div class="card" style="margin-bottom:18px;">
      <h2>Private Dashboard Link</h2>
      <div class="copy-box">{esc(BASE_URL + contractor_dashboard_url(contractor_id))}</div>
    </div>

    <div class="card">
      <h2>Your Homeowner Requests</h2>
      <p class="mini">These are exclusive homeowner requests assigned to your business. Locked requests are shown with urgency so you can act quickly.</p>
      {"".join(lead_cards) if lead_cards else "<p>No leads yet.</p>"}
    </div>
    """
    return layout("Contractor Dashboard", body)


# -----------------------------
# JSON HELPERS
# -----------------------------
@app.get("/api/contractors")
def api_contractors():
    return JSONResponse(fetch_contractors(include_unapproved=False))


@app.get("/api/leads")
def api_leads():
    return JSONResponse(fetch_leads())
