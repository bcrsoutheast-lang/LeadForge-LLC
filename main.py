from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


PENDING_CONTRACTORS = [
    {
        "id": "pending-roofing-1",
        "name": "James Porter",
        "company_name": "Porter Roofing",
        "service": "Roofing",
        "city": "Birmingham",
        "state": "AL",
        "zip_code": "35203",
        "phone": "(205) 555-3011",
        "email": "james@porterroofing.com",
        "bio": "Residential roofing, repair work, and storm damage jobs.",
        "approved": False,
    },
    {
        "id": "pending-plumbing-1",
        "name": "Chris Lane",
        "company_name": "Lane Plumbing Co.",
        "service": "Plumbing",
        "city": "Hoover",
        "state": "AL",
        "zip_code": "35226",
        "phone": "(205) 555-3022",
        "email": "chris@laneplumbing.com",
        "bio": "Drain repair, water heaters, fixture replacement, and plumbing service calls.",
        "approved": False,
    },
]

APPROVED_CONTRACTORS = [
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
]

LEADS = [
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
    }
]


def get_contractor(contractor_id):
    for contractor in APPROVED_CONTRACTORS:
        if contractor["id"] == contractor_id:
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


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request, "index.html", {})


@app.get("/health")
def health():
    return {"status": "ok", "app": "leadforge"}


@app.get("/services", response_class=HTMLResponse)
def services_page(request: Request):
    return templates.TemplateResponse(request, "services.html", {})


@app.get("/join-contractor", response_class=HTMLResponse)
def join_contractor(request: Request):
    return templates.TemplateResponse(request, "join-contractor.html", {})


@app.post("/join-contractor")
def submit_contractor():
    return RedirectResponse("/join-contractor-success", status_code=303)


@app.get("/join-contractor-success", response_class=HTMLResponse)
def join_success(request: Request):
    return templates.TemplateResponse(request, "join-contractor-success.html", {})


@app.get("/contractors", response_class=HTMLResponse)
def contractors(request: Request, service: str = None):
    contractors_to_show = APPROVED_CONTRACTORS

    if service:
        filtered = []
        for contractor in APPROVED_CONTRACTORS:
            if contractor.get("service", "").lower() == service.lower():
                filtered.append(contractor)
        if filtered:
            contractors_to_show = filtered

    return templates.TemplateResponse(
        request,
        "contractors.html",
        {
            "service": service,
            "contractors": contractors_to_show
        }
    )


@app.get("/request/{contractor_id}", response_class=HTMLResponse)
def request_page(request: Request, contractor_id: str):
    contractor = get_contractor(contractor_id)
    return templates.TemplateResponse(
        request,
        "request.html",
        {
            "contractor_id": contractor_id,
            "contractor": contractor
        }
    )


@app.post("/request/{contractor_id}")
def submit_request(contractor_id: str):
    return RedirectResponse("/request-success", status_code=303)


@app.get("/request-success", response_class=HTMLResponse)
def request_success(request: Request):
    return templates.TemplateResponse(request, "request-success.html", {})


@app.get("/admin-login", response_class=HTMLResponse)
def admin_login(request: Request):
    return templates.TemplateResponse(request, "admin-login.html", {})


@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    return templates.TemplateResponse(
        request,
        "admin.html",
        {
            "contractors": APPROVED_CONTRACTORS,
            "leads": LEADS,
            "pending_contractors": PENDING_CONTRACTORS,
            "approved_contractors": APPROVED_CONTRACTORS
        }
    )


@app.post("/approve/{contractor_id}")
def approve_contractor(contractor_id: str):
    return RedirectResponse("/admin", status_code=303)


@app.post("/reject/{contractor_id}")
def reject_contractor(contractor_id: str):
    return RedirectResponse("/admin", status_code=303)


@app.get("/contractor/{contractor_id}", response_class=HTMLResponse)
def contractor_dashboard(request: Request, contractor_id: str, token: str = None):
    contractor = get_contractor(contractor_id)

    contractor_leads = []
    for lead in LEADS:
        if lead.get("contractor_id") == contractor_id:
            contractor_leads.append(lead)

    return templates.TemplateResponse(
        request,
        "contractor-dashboard.html",
        {
            "contractor_id": contractor_id,
            "token": token,
            "contractor": contractor,
            "leads": contractor_leads
        }
    )


@app.get("/unlock/{lead_id}")
def unlock_lead(lead_id: str, token: str = None):
    if token is None:
        token = ""
    return RedirectResponse(f"/stripe-success?session_id=test&token={token}", status_code=303)


@app.get("/stripe-success", response_class=HTMLResponse)
def stripe_success(request: Request, session_id: str = None, token: str = None):
    return templates.TemplateResponse(
        request,
        "stripe-success.html",
        {
            "session_id": session_id,
            "token": token
        }
    )
