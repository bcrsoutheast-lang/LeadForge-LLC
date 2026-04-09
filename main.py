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
def esc(value) -> str:
    if value is None:
        return ""
    return html.escape(str(value))


def now_iso() -> str:
    return datetime.utcnow().isoformat()


def brand_html() -> str:
    return """
    <a class="brand-wrap" href="/">
      <img src="/static/IMG_2026.png" alt="LeadForge Logo" class="brand-logo" onerror="this.style.display='none'">
      <span class="brand-text">LeadForge</span>
    </a>
    """


def topbar(extra_nav: str = "") -> str:
    return f"""
    <div class="topbar">
      {brand_html()}
      <div class="nav">
        <a class="btn secondary" href="/">Home</a>
        <a class="btn secondary" href="/services">Services</a>
        <a class="btn secondary" href="/contractors">Contractors</a>
        <a class="btn secondary" href="/join-contractor">Join as a Contractor</a>
        {extra_nav}
      </div>
    </div>
    """


def is_admin(request: Request) -> bool:
    return request.session.get("is_admin") is True


def admin_required(request: Request):
    if not is_admin(request):
        return RedirectResponse(url="/admin-login", status_code=303)
    return None


def normalize_service(value: str) -> str:
    return (value or "").strip().lower()


def split_services(raw_value: str) -> list[str]:
    if not raw_value:
        return []
    parts = [p.strip() for p in raw_value.split(",")]
    return [p for p in parts if p]


def contractor_matches_service(contractor: dict, service: str) -> bool:
    target = normalize_service(service)
    if not target:
        return True

    services_raw = contractor.get("service") or contractor.get("services") or ""
    services = [normalize_service(s) for s in split_services(services_raw)]
    return target in services


def fetch_contractors(include_unapproved: bool = True) -> list[dict]:
    if not supabase:
        return []

    response = supabase.table("contractors").select("*").order("created_at", desc=True).execute()
    rows = response.data or []

    if include_unapproved:
        return rows

    return [row for row in rows if row.get("approved") is True]


def fetch_leads() -> list[dict]:
    if not supabase:
        return []

    response = supabase.table("leads").select("*").order("created_at", desc=True).execute()
    return response.data or []


def fetch_contractor_by_id(contractor_id: str) -> dict | None:
    if not supabase:
        return None

    response = supabase.table("contractors").select("*").eq("id", contractor_id).limit(1).execute()
    rows = response.data or []
    return rows[0] if rows else None


def fetch_leads_for_contractor(contractor_id: str) -> list[dict]:
    if not supabase:
        return []

    response = (
        supabase.table("leads")
        .select("*")
        .eq("contractor_id", contractor_id)
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


def fetch_lead_by_id(lead_id: str) -> dict | None:
    if not supabase:
        return None

    response = supabase.table("leads").select("*").eq("id", lead_id).limit(1).execute()
    rows = response.data or []
    return rows[0] if rows else None


def unlock_lead(lead_id: str):
    if not supabase:
        return
    try:
        supabase.table("leads").update({"unlocked": True}).eq("id", lead_id).execute()
    except Exception:
        pass


def safe_insert_contractor(payload: dict) -> tuple[bool, str]:
    if not supabase:
        return False, "Supabase is not configured."

    attempts = [
        payload,
        {k: v for k, v in payload.items() if k not in {"business_description"}},
        {k: v for k, v in payload.items() if k in {"id", "full_name", "company_name", "phone", "email", "service", "city", "state", "zip", "approved"}},
        {k: v for k, v in payload.items() if k in {"full_name", "company_name", "phone", "email", "service", "city", "state", "zip", "approved"}},
    ]

    last_error = "Unknown contractor insert error."
    for attempt in attempts:
        try:
            supabase.table("contractors").insert(attempt).execute()
            return True, ""
        except Exception as e:
            last_error = str(e)

    return False, last_error


def safe_insert_lead(payload: dict) -> tuple[bool, str]:
    if not supabase:
        return False, "Supabase is not configured."

    attempts = [
        payload,
        {k: v for k, v in payload.items() if k not in {"chosen_contractor"}},
        {k: v for k, v in payload.items() if k not in {"chosen_contractor", "unlocked"}},
        {k: v for k, v in payload.items() if k in {"id", "contractor_id", "owner_name", "phone", "email", "service", "project_details", "city", "state", "zip", "created_at"}},
        {k: v for k, v in payload.items() if k in {"contractor_id", "owner_name", "phone", "email", "service", "project_details", "city", "state", "zip"}},
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


def format_contractor_card(contractor: dict) -> str:
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


def layout(title: str, body: str) -> HTMLResponse:
    return HTMLResponse(f"""
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
          background: #050505;
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
        }}
        .brand-wrap {{
          display: inline-flex;
          align-items: center;
          gap: 14px;
          text-decoration: none;
        }}
        .brand-logo {{
          height: 72px;
          width: auto;
          display: block;
        }}
        .brand-text {{
          font-size: 30px;
          font-weight: 800;
          color: #cc0000;
          text-decoration: none;
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
          box-shadow: 0 0 0 1px rgba(255,255,255,0.02) inset;
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
        table {{
          width: 100%;
          border-collapse: collapse;
          overflow-x: auto;
          display: block;
        }}
        th, td {{
          border-bottom: 1px solid #2c2c2c;
          padding: 10px 8px;
          text-align: left;
          vertical-align: top;
          font-size: 14px;
        }}
        th {{
          color: #d4af37;
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
          .brand-logo {{
            height: 60px;
          }}
          .brand-text {{
            font-size: 24px;
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
    """)


def error_page(title: str, message: str, details: str = "") -> HTMLResponse:
    detail_html = f'<div class="notice" style="margin-top:16px;"><strong>Details:</strong><br>{esc(details)}</div>' if details else ""
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

# -----------------------------
# ROUTES
# -----------------------------
@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def homepage():
    body = f"""
    {topbar()}

    <div class="hero">
      <div class="hero-kicker gold"><strong>Cleaner matching. More trust. One homeowner request at a time.</strong></div>
      <h1><span class="red">Choose Your Contractor.</span><br><span class="gold">Send One Request.</span></h1>
      <p class="hero-copy">
        LeadForge gives homeowners a more legitimate way to connect with contractors.
        Instead of blasting a project out to everyone, homeowners choose one approved contractor
        and send one direct request.
      </p>
      <div class="topnav">
        <a class="btn" href="/services">Find a Contractor</a>
        <a class="btn secondary" href="/join-contractor">Join as a Contractor</a>
      </div>
    </div>

    <div class="grid grid-2">
      <div class="card">
        <h2>For Homeowners</h2>
        <p class="mini">
          Browse by service, review approved contractors, and send a direct request to the company
          you actually want to talk to.
        </p>
        <a class="btn" href="/services">Browse Services</a>
      </div>

      <div class="card">
        <h2>For Contractors</h2>
        <p class="mini">
          LeadForge is built for legitimate contractors who want real homeowner opportunities.
          Approved contractors can unlock exclusive request details for a flat $10 access fee.
        </p>
        <a class="btn gold" href="/join-contractor">Apply Now</a>
      </div>
    </div>

    <div class="card" style="margin-top:22px;">
      <h2 class="section-title">How LeadForge Works</h2>
      <div class="grid grid-3">
        <div class="card">
          <h3>1. Homeowner Picks a Service</h3>
          <p class="mini">
            Roofing, siding, gutters, painting, flooring, plumbing, electrical, HVAC,
            landscaping, remodeling, and more.
          </p>
        </div>
        <div class="card">
          <h3>2. Homeowner Chooses One Contractor</h3>
          <p class="mini">
            Homeowners choose a specific contractor instead of sending the same lead to a pile of companies.
          </p>
        </div>
        <div class="card">
          <h3>3. Contractor Unlocks the Opportunity</h3>
          <p class="mini">
            The contractor sees the request and can unlock full homeowner details for $10.
          </p>
        </div>
      </div>
    </div>

    <div class="grid grid-2" style="margin-top:22px;">
      <div class="card">
        <h2>Our contractor vetting process</h2>
        <p class="mini">
          We want homeowners to feel confident using LeadForge, and we want legitimate contractors
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
          LeadForge is not trying to create a hard time for good contractors. The approval process is here
          to keep the platform cleaner, protect homeowner trust, and give legitimate businesses a better-quality
          marketplace.
        </p>
        <p class="mini">
          If a contractor is registered, properly licensed where needed, insured, and operating professionally,
          the vetting process should feel straightforward, not unfair.
        </p>
      </div>
    </div>

    <div class="grid grid-2" style="margin-top:22px;">
      <div class="card">
        <h2>Popular homeowner services</h2>
        <div class="topnav">
          <a class="btn secondary" href="/contractors?service=roofing">Roofing</a>
          <a class="btn secondary" href="/contractors?service=siding">Siding</a>
          <a class="btn secondary" href="/contractors?service=gutters">Gutters</a>
          <a class="btn secondary" href="/contractors?service=painting">Painting</a>
          <a class="btn secondary" href="/contractors?service=flooring">Flooring</a>
          <a class="btn secondary" href="/contractors?service=plumbing">Plumbing</a>
        </div>
      </div>

      <div class="card">
        <h2>Why homeowners use LeadForge</h2>
        <ul class="clean-list mini">
          <li>Cleaner experience</li>
          <li>Approved contractor directory</li>
          <li>Less spam and fewer bidding wars</li>
          <li>One direct request instead of getting flooded</li>
          <li>Better transparency around who is being shown</li>
        </ul>
      </div>
    </div>

    <div class="card" style="margin-top:22px;">
      <h2>Built for trust on both sides</h2>
      <p class="mini">
        LeadForge is meant to feel legitimate. Homeowners should feel like they are choosing from contractors
        who were actually reviewed. Contractors should feel like the process is transparent and meant to reward
        serious businesses, not punish them.
      </p>
      <div class="topnav">
        <a class="btn" href="/services">Find a Contractor</a>
        <a class="btn gold" href="/join-contractor">Become a Contractor</a>
      </div>
    </div>
    """
    return layout("LeadForge", body)


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

    heading = f"Approved Contractors{f' - {service.title()}' if service else ''}"

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
      <h1>Apply to Join LeadForge</h1>
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
      <p class="mini">
        Your request goes directly to the contractor you selected. This is designed to feel cleaner,
        more direct, and more legitimate for homeowners.
      </p>
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
        return error_page(
            "Request Submission Error",
            "We could not save the homeowner request right now.",
            error,
        )

    return RedirectResponse(url="/request-success", status_code=303)


@app.get("/request-success", response_class=HTMLResponse)
def request_success():
    body = f"""
    {topbar()}
    <div class="hero">
      <h1>Request Sent</h1>
      <p class="muted">Your project request has been sent to the contractor you selected.</p>
      <a class="btn" href="/">Back Home</a>
    </div>
    """
    return layout("Request Sent", body)

# -----------------------------
# ADMIN LOGIN / LOGOUT
# -----------------------------
@app.get("/admin-login", response_class=HTMLResponse)
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
      <form method="post" action="/admin-login">
        <label>Admin Password</label>
        <input type="password" name="password" required>
        <button class="btn" type="submit">Login</button>
      </form>
    </div>
    """
    return layout("Admin Login", body)


@app.post("/admin-login")
def admin_login(request: Request, password: str = Form(...)):
    if password == ADMIN_PASSWORD:
        request.session["is_admin"] = True
        return RedirectResponse(url="/admin", status_code=303)

    return RedirectResponse(url="/admin-login?error=Wrong+password", status_code=303)


@app.get("/admin-logout")
def admin_logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/admin-login", status_code=303)

# -----------------------------
# ADMIN
# -----------------------------
@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    guard = admin_required(request)
    if guard:
        return guard

    contractors = fetch_contractors(include_unapproved=True)
    leads = fetch_leads()

    contractor_rows = []
    for contractor in contractors:
        cid = esc(contractor.get("id"))
        approved = contractor.get("approved") is True
        approved_badge = '<span class="pill ok">Approved</span>' if approved else '<span class="pill no">Pending</span>'

        contractor_rows.append(f"""
        <tr>
          <td>{esc(contractor.get("created_at"))}</td>
          <td>{cid}</td>
          <td>{esc(contractor.get("company_name"))}</td>
          <td>{esc(contractor.get("full_name"))}</td>
          <td>{esc(contractor.get("phone"))}</td>
          <td>{esc(contractor.get("email"))}</td>
          <td>{esc(contractor.get("service"))}</td>
          <td>{esc(contractor.get("city"))}</td>
          <td>{esc(contractor.get("state"))}</td>
          <td>{esc(contractor.get("zip"))}</td>
          <td>{approved_badge}</td>
          <td>
            <div style="display:flex; gap:8px; flex-wrap:wrap;">
              <a class="btn" href="/approve/{cid}">Approve</a>
              <a class="btn secondary" href="/reject/{cid}">Reject</a>
              <a class="btn gold" href="/contractor/{cid}" target="_blank">Dashboard</a>
            </div>
          </td>
        </tr>
        """)

    lead_rows = []
    for lead in leads:
        unlocked = lead.get("unlocked") is True
        unlocked_badge = '<span class="pill ok">Yes</span>' if unlocked else '<span class="pill no">No</span>'
        lead_rows.append(f"""
        <tr>
          <td>{esc(lead.get("created_at"))}</td>
          <td>{esc(lead.get("id"))}</td>
          <td>{esc(lead.get("owner_name"))}</td>
          <td>{esc(lead.get("phone"))}</td>
          <td>{esc(lead.get("email"))}</td>
          <td>{esc(lead.get("city"))}</td>
          <td>{esc(lead.get("state"))}</td>
          <td>{esc(lead.get("zip"))}</td>
          <td>{esc(lead.get("service"))}</td>
          <td>{esc(lead.get("project_details"))}</td>
          <td>{esc(lead.get("chosen_contractor"))}</td>
          <td>{esc(lead.get("contractor_id"))}</td>
          <td>{unlocked_badge}</td>
        </tr>
        """)

    body = f"""
    {topbar('<a class="btn secondary" href="/admin-logout">Logout</a>')}
    <div class="hero">
      <h1>LeadForge Admin</h1>
      <p class="muted">Protected admin dashboard</p>
    </div>

    <div class="grid grid-2">
      <div class="card">
        <h3>Total Contractors</h3>
        <p style="font-size:32px; font-weight:bold;">{len(contractors)}</p>
      </div>
      <div class="card">
        <h3>Total Leads</h3>
        <p style="font-size:32px; font-weight:bold;">{len(leads)}</p>
      </div>
    </div>

    <div class="card" style="margin-top:20px;">
      <h2>Contractor Applications</h2>
      <table>
        <thead>
          <tr>
            <th>Created</th>
            <th>ID</th>
            <th>Company</th>
            <th>Contact</th>
            <th>Phone</th>
            <th>Email</th>
            <th>Service</th>
            <th>City</th>
            <th>State</th>
            <th>Zip</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {''.join(contractor_rows) if contractor_rows else '<tr><td colspan="12">No contractors found.</td></tr>'}
        </tbody>
      </table>
    </div>

    <div class="card" style="margin-top:20px;">
      <h2>Homeowner Leads</h2>
      <table>
        <thead>
          <tr>
            <th>Created</th>
            <th>Lead ID</th>
            <th>Name</th>
            <th>Phone</th>
            <th>Email</th>
            <th>City</th>
            <th>State</th>
            <th>Zip</th>
            <th>Service</th>
            <th>Project Details</th>
            <th>Chosen Contractor</th>
            <th>Contractor ID</th>
            <th>Unlocked</th>
          </tr>
        </thead>
        <tbody>
          {''.join(lead_rows) if lead_rows else '<tr><td colspan="13">No leads found.</td></tr>'}
        </tbody>
      </table>
    </div>
    """
    return layout("LeadForge Admin", body)


@app.get("/approve/{contractor_id}")
def approve_contractor(contractor_id: str, request: Request):
    guard = admin_required(request)
    if guard:
        return guard

    if not supabase:
        return HTMLResponse("Supabase is not configured.", status_code=500)

    supabase.table("contractors").update({"approved": True}).eq("id", contractor_id).execute()
    return RedirectResponse(url="/admin", status_code=303)


@app.get("/reject/{contractor_id}")
def reject_contractor(contractor_id: str, request: Request):
    guard = admin_required(request)
    if guard:
        return guard

    if not supabase:
        return HTMLResponse("Supabase is not configured.", status_code=500)

    supabase.table("contractors").delete().eq("id", contractor_id).execute()
    return RedirectResponse(url="/admin", status_code=303)

# -----------------------------
# STRIPE UNLOCK FLOW
# -----------------------------
@app.get("/unlock/{lead_id}")
def unlock_checkout(lead_id: str):
    if not STRIPE_SECRET_KEY or not STRIPE_PRICE_ID:
        return HTMLResponse("Stripe is not configured.", status_code=500)

    lead = fetch_lead_by_id(lead_id)
    if not lead:
        return HTMLResponse("Lead not found.", status_code=404)

    if lead.get("unlocked") is True:
        contractor_id = lead.get("contractor_id")
        return RedirectResponse(url=f"/contractor/{contractor_id}", status_code=303)

    contractor_id = str(lead.get("contractor_id") or "")
    if not contractor_id:
        return HTMLResponse("Missing contractor for this lead.", status_code=400)

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[
                {
                    "price": STRIPE_PRICE_ID,
                    "quantity": 1,
                }
            ],
            success_url=f"{BASE_URL}/stripe-success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{BASE_URL}/contractor/{contractor_id}",
            metadata={
                "lead_id": lead_id,
                "contractor_id": contractor_id,
            },
        )
        return RedirectResponse(url=session.url, status_code=303)
    except Exception as e:
        return error_page(
            "Stripe Checkout Error",
            "We could not launch checkout right now.",
            str(e),
        )


@app.get("/stripe-success", response_class=HTMLResponse)
def stripe_success(session_id: str = ""):
    if not session_id:
        return HTMLResponse("Missing Stripe session ID.", status_code=400)

    if not STRIPE_SECRET_KEY:
        return HTMLResponse("Stripe is not configured.", status_code=500)

    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except Exception as e:
        return error_page(
            "Stripe Verification Error",
            "We could not verify the payment session.",
            str(e),
        )

    payment_status = session.get("payment_status")
    metadata = session.get("metadata") or {}
    lead_id = metadata.get("lead_id", "")
    contractor_id = metadata.get("contractor_id", "")

    if payment_status == "paid" and lead_id:
        unlock_lead(lead_id)

        body = f"""
        {topbar()}
        <div class="hero">
          <h1>Lead Unlocked</h1>
          <p class="muted">Your $10 access payment was successful.</p>
        </div>

        <div class="success">
          Payment confirmed. The homeowner details for this lead are now unlocked.
        </div>

        <div class="topnav">
          <a class="btn green" href="/contractor/{esc(contractor_id)}">Go To Contractor Dashboard</a>
          <a class="btn secondary" href="/">Back Home</a>
        </div>
        """
        return layout("Lead Unlocked", body)

    return HTMLResponse("Payment not completed.", status_code=400)

# -----------------------------
# CONTRACTOR DASHBOARD
# -----------------------------
@app.get("/contractor/{contractor_id}", response_class=HTMLResponse)
def contractor_dashboard(contractor_id: str):
    contractor = fetch_contractor_by_id(contractor_id)
    if not contractor:
        return HTMLResponse("Contractor not found.", status_code=404)

    leads = fetch_leads_for_contractor(contractor_id)

    lead_cards = []
    for lead in leads:
        unlocked = lead.get("unlocked") is True
        lead_id = esc(lead.get("id"))

        if unlocked:
            details = f"""
            <p><strong>Status:</strong> <span class="pill ok">Unlocked</span></p>
            <p><strong>Name:</strong> {esc(lead.get("owner_name"))}</p>
            <p><strong>Phone:</strong> {esc(lead.get("phone"))}</p>
            <p><strong>Email:</strong> {esc(lead.get("email"))}</p>
            <p><strong>City:</strong> {esc(lead.get("city"))}</p>
            <p><strong>State:</strong> {esc(lead.get("state"))}</p>
            <p><strong>ZIP:</strong> {esc(lead.get("zip"))}</p>
            <p><strong>Service:</strong> {esc(lead.get("service"))}</p>
            <p><strong>Project:</strong> {esc(lead.get("project_details"))}</p>
            """
            action_button = ""
        else:
            details = f"""
            <p><strong>Status:</strong> <span class="pill no">Locked</span></p>
            <p><strong>Service:</strong> {esc(lead.get("service"))}</p>
            <p><strong>Project:</strong> {esc(lead.get("project_details"))}</p>
            <p class="muted">To view homeowner name, phone, email, and full details, unlock this request for $10.</p>
            """
            action_button = f'<a class="btn gold" href="/unlock/{lead_id}">Unlock For $10</a>'

        lead_cards.append(f"""
        <div class="card">
          <h3>Lead {lead_id}</h3>
          {details}
          {action_button}
        </div>
        """)

    body = f"""
    {topbar()}
    <div class="hero">
      <h1>{esc(contractor.get("company_name") or contractor.get("full_name"))}</h1>
      <p class="muted">Contractor dashboard</p>
      <p class="muted">This page is still public if someone has the exact URL. We will lock it next.</p>
    </div>

    <div class="card">
      <h2>Your Leads</h2>
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
