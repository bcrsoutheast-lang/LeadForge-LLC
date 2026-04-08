from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

templates = Jinja2Templates(directory="templates")

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")


# =====================
# DEMO DATA
# =====================

DEMO_CONTRACTORS: List[Dict[str, Any]] = [
    {
        "id": "demo-electrical-1",
        "name": "Marcus Hill",
        "company_name": "Hill Electrical Co.",
        "service": "Electrical",
        "city": "Birmingham",
        "state": "AL",
        "zip_code": "35203",
        "years_experience": "12 years",
        "phone": "(205) 555-0112",
        "email": "marcus@hillelectrical.com",
        "bio": "Residential electrical upgrades, lighting, panel work, troubleshooting, and service calls.",
        "approved": True,
    },
    {
        "id": "demo-roofing-1",
        "name": "Derrick Cole",
        "company_name": "Cole Roofing & Repair",
        "service": "Roofing",
        "city": "Hoover",
        "state": "AL",
        "zip_code": "35226",
        "years_experience": "15 years",
        "phone": "(205) 555-0144",
        "email": "derrick@coleroofing.com",
        "bio": "Roof repair, shingle replacement, leak inspections, and storm damage estimates.",
        "approved": True,
    },
    {
        "id": "demo-plumbing-1",
        "name": "Tasha Reed",
        "company_name": "Reed Plumbing Pros",
        "service": "Plumbing",
        "city": "Vestavia Hills",
        "state": "AL",
        "zip_code": "35216",
        "years_experience": "10 years",
        "phone": "(205) 555-0178",
        "email": "tasha@reedplumbingpros.com",
        "bio": "Drain issues, fixture installs, water heater service, and general plumbing repairs.",
        "approved": True,
    },
    {
        "id": "demo-hvac-1",
        "name": "Brandon Price",
        "company_name": "Price Heating & Air",
        "service": "HVAC",
        "city": "Mountain Brook",
        "state": "AL",
        "zip_code": "35213",
        "years_experience": "9 years",
        "phone": "(205) 555-0199",
        "email": "brandon@pricehvac.com",
        "bio": "AC repair, heating service, tune-ups, thermostat installs, and seasonal maintenance.",
        "approved": True,
    },
    {
        "id": "demo-painting-1",
        "name": "Elijah Brooks",
        "company_name": "Brooks Painting",
        "service": "Painting",
        "city": "Trussville",
        "state": "AL",
        "zip_code": "35173",
        "years_experience": "8 years",
        "phone": "(205) 555-0133",
        "email": "elijah@brookspainting.com",
        "bio": "Interior and exterior painting, trim work, touch-ups, and residential repaint projects.",
        "approved": True,
    },
    {
        "id": "demo-flooring-1",
        "name": "Andre Lawson",
        "company_name": "Lawson Flooring Group",
        "service": "Flooring",
        "city": "Bessemer",
        "state": "AL",
        "zip_code": "35022",
        "years_experience": "11 years",
        "phone": "(205) 555-0181",
        "email": "andre@lawsonflooring.com",
        "bio": "LVP, hardwood, laminate, repairs, and full-room flooring replacement.",
        "approved": True,
    },
]

DEMO_LEADS: List[Dict[str, Any]] = [
    {
        "id": "lead-demo-001",
        "contractor_id": "demo-electrical-1",
        "owner_name": "John Smith",
        "phone": "(205) 555-2222",
        "email": "johnsmith@example.com",
        "service": "Electrical",
        "project_details": "Need a dining room light fixture replaced and two outlets checked.",
        "city": "Birmingham",
        "state": "AL",
        "zip": "35203",
        "unlocked": False,
    },
    {
        "id": "lead-demo-002",
        "contractor_id": "demo-roofing-1",
        "owner_name": "Lisa Carter",
        "phone": "(205) 555-2323",
        "email": "lisacarter@example.com",
        "service": "Roofing",
        "project_details": "Small leak over garage after recent storm.",
        "city": "Hoover",
        "state": "AL",
        "zip": "35226",
        "unlocked": False,
    },
]


# =====================
# HELPERS
# =====================

def render_template(request: Request, template_name: str, extra_context: Optional[Dict[str, Any]] = None):
    context = {"request": request}
    if extra_context:
        context.update(extra_context)
    return templates.TemplateResponse(template_name, context)


def filter_contractors_by_service(service: Optional[str]) -> List[Dict[str, Any]]:
    if not service:
        return DEMO_CONTRACTORS

    wanted = service.strip().lower()
    filtered = [
        contractor
        for contractor in DEMO_CONTRACTORS
        if str(contractor.get("service", "")).strip().lower() == wanted
    ]

    return filtered if filtered else DEMO_CONTRACTORS


def get_contractor(contractor_id: str) -> Dict[str, Any]:
    for contractor in DEMO_CONTRACTORS:
        if contractor.get("id") == contractor_id:
            return contractor

    return {
        "id": contractor_id,
        "name": "LeadForge Contractor",
        "company_name": "LeadForge Network Pro",
        "service": "Contractor Services",
        "city": "Birmingham",
        "state": "AL",
        "zip_code": "35203",
        "years_experience": "Not listed",
        "phone": "Not listed",
        "email": "Not listed",
        "bio": "This contractor is available through LeadForge.",
        "approved": True,
    }


# =====================
# BASIC ROUTES
# =====================

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return render_template(request, "index.html")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "app": "leadforge",
        "contractors_loaded": len(DEMO_CONTRACTORS),
        "leads_loaded": len(DEMO_LEADS),
    }


# =====================
# SERVICES PAGE
# =====================

@app.get("/services", response_class=HTMLResponse)
def services_page(request: Request):
    return render_template(request, "services.html")


# =====================
# CONTRACTOR SIGNUP
# =====================

@app.get("/join-contractor", response_class=HTMLResponse)
def join_contractor(request: Request):
    return render_template(request, "join-contractor.html")


@app.post("/join-contractor")
def submit_contractor(
    full_name: Optional[str] = Form(default=None),
    company_name: Optional[str] = Form(default=None),
    phone: Optional[str] = Form(default=None),
    email: Optional[str] = Form(default=None),
    service: Optional[str] = Form(default=None),
    city: Optional[str] = Form(default=None),
    state: Optional[str] = Form(default=None),
    zip_code: Optional[str] = Form(default=None),
    bio: Optional[str] = Form(default=None),
):
    return RedirectResponse("/join-contractor-success", status_code=303)


@app.get("/join-contractor-success", response_class=HTMLResponse)
def join_success(request: Request):
    return render_template(request, "join-contractor-success.html")


# =====================
# CONTRACTOR BROWSE
# =====================

@app.get("/contractors", response_class=HTMLResponse)
def contractors(request: Request, service: Optional[str] = None):
    contractors_to_show = filter_contractors_by_service(service)

    return render_template(
        request,
        "contractors.html",
        {
            "service": service,
            "contractors": contractors_to_show,
        },
    )


# =====================
# HOMEOWNER REQUEST
# =====================

@app.get("/request/{contractor_id}", response_class=HTMLResponse)
def request_page(request: Request, contractor_id: str):
    contractor = get_contractor(contractor_id)

    return render_template(
        request,
        "request.html",
        {
            "contractor_id": contractor_id,
            "contractor": contractor,
        },
    )


@app.post("/request/{contractor_id}")
def submit_request(
    contractor_id: str,
    full_name: Optional[str] = Form(default=None),
    phone: Optional[str] = Form(default=None),
    email: Optional[str] = Form(default=None),
    service: Optional[str] = Form(default=None),
    city: Optional[str] = Form(default=None),
    state: Optional[str] = Form(default=None),
    zip_code: Optional[str] = Form(default=None),
    project_details: Optional[str] = Form(default=None),
):
    return RedirectResponse("/request-success", status_code=303)


@app.get("/request-success", response_class=HTMLResponse)
def request_success(request: Request):
    return render_template(request, "request-success.html")


# =====================
# ADMIN
# =====================

@app.get("/admin-login", response_class=HTMLResponse)
def admin_login(request: Request):
    return render_template(request, "admin-login.html")


@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    return render_template(
        request,
        "admin.html",
        {
            "contractors": DEMO_CONTRACTORS,
            "leads": DEMO_LEADS,
            "pending_contractors": [],
            "approved_contractors": DEMO_CONTRACTORS,
        },
    )


# =====================
# CONTRACTOR DASHBOARD
# =====================

@app.get("/contractor/{contractor_id}", response_class=HTMLResponse)
def contractor_dashboard(request: Request, contractor_id: str, token: Optional[str] = None):
    contractor = get_contractor(contractor_id)
    contractor_leads = [lead for lead in DEMO_LEADS if lead.get("contractor_id") == contractor_id]

    return render_template(
        request,
        "contractor-dashboard.html",
        {
            "contractor_id": contractor_id,
            "token": token,
            "contractor": contractor,
            "leads": contractor_leads,
        },
    )


# =====================
# STRIPE UNLOCK FLOW
# =====================

@app.get("/unlock/{lead_id}")
def unlock_lead(lead_id: str, token: Optional[str] = None):
    safe_token = token or ""
    return RedirectResponse(f"/stripe-success?session_id=test&token={safe_token}", status_code=303)


@app.get("/stripe-success", response_class=HTMLResponse)
def stripe_success(request: Request, session_id: Optional[str] = None, token: Optional[str] = None):
    return render_template(
        request,
        "stripe-success.html",
        {
            "session_id": session_id,
            "token": token,
        },
    )
