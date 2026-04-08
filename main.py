from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uuid

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# =====================
# DATA
# =====================

PENDING_CONTRACTORS = []
APPROVED_CONTRACTORS = []
LEADS = []

# =====================
# HELPERS
# =====================

def get_contractor(contractor_id):
    for c in APPROVED_CONTRACTORS:
        if c["id"] == contractor_id:
            return c
    return None

# =====================
# BASIC ROUTES
# =====================

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/services", response_class=HTMLResponse)
def services_page(request: Request):
    return templates.TemplateResponse("services.html", {"request": request})

# =====================
# CONTRACTOR SIGNUP
# =====================

@app.get("/join-contractor", response_class=HTMLResponse)
def join_contractor(request: Request):
    return templates.TemplateResponse("join-contractor.html", {"request": request})

@app.post("/join-contractor")
async def submit_contractor(request: Request):
    form = await request.form()

    try:
        contractor = {
            "id": str(uuid.uuid4()),
            "name": form.get("full_name"),
            "company_name": form.get("company_name"),
            "service": form.get("service"),
            "city": form.get("city"),
            "state": form.get("state"),
            "zip_code": form.get("zip_code"),
            "phone": form.get("phone"),
            "email": form.get("email"),
            "bio": form.get("bio"),
            "approved": False,
        }

        # VALIDATION CHECK
        if not contractor["name"] or not contractor["email"]:
            return PlainTextResponse("Missing required fields", status_code=400)

        PENDING_CONTRACTORS.append(contractor)

        print("NEW CONTRACTOR:", contractor)

        return RedirectResponse("/join-contractor-success", status_code=303)

    except Exception as e:
        print("ERROR IN SUBMIT:", e)
        return PlainTextResponse("Server error on submit", status_code=500)

@app.get("/join-contractor-success", response_class=HTMLResponse)
def join_success(request: Request):
    return templates.TemplateResponse("join-contractor-success.html", {"request": request})

# =====================
# CONTRACTORS PAGE
# =====================

@app.get("/contractors", response_class=HTMLResponse)
def contractors(request: Request, service: str = None):
    data = APPROVED_CONTRACTORS

    if service:
        data = [c for c in data if c["service"].lower() == service.lower()]

    return templates.TemplateResponse(
        "contractors.html",
        {"request": request, "contractors": data, "service": service}
    )

# =====================
# HOMEOWNER REQUEST
# =====================

@app.get("/request/{contractor_id}", response_class=HTMLResponse)
def request_page(request: Request, contractor_id: str):
    contractor = get_contractor(contractor_id)

    return templates.TemplateResponse(
        "request.html",
        {
            "request": request,
            "contractor": contractor,
            "contractor_id": contractor_id
        }
    )

@app.post("/request/{contractor_id}")
async def submit_request(contractor_id: str, request: Request):
    form = await request.form()

    lead = {
        "id": str(uuid.uuid4()),
        "contractor_id": contractor_id,
        "owner_name": form.get("owner_name"),
        "phone": form.get("phone"),
        "email": form.get("email"),
        "service": form.get("service"),
        "project_details": form.get("project_details"),
        "city": form.get("city"),
        "state": form.get("state"),
        "zip": form.get("zip"),
    }

    LEADS.append(lead)

    print("NEW LEAD:", lead)

    return RedirectResponse("/request-success", status_code=303)

@app.get("/request-success", response_class=HTMLResponse)
def request_success(request: Request):
    return templates.TemplateResponse("request-success.html", {"request": request})

# =====================
# ADMIN
# =====================

@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "pending_contractors": PENDING_CONTRACTORS,
            "approved_contractors": APPROVED_CONTRACTORS,
            "contractors": APPROVED_CONTRACTORS,
            "leads": LEADS
        }
    )

@app.post("/approve/{contractor_id}")
def approve_contractor(contractor_id: str):
    global PENDING_CONTRACTORS, APPROVED_CONTRACTORS

    found = False

    for c in PENDING_CONTRACTORS:
        if c["id"] == contractor_id:
            c["approved"] = True
            APPROVED_CONTRACTORS.append(c)
            found = True
            break

    PENDING_CONTRACTORS = [c for c in PENDING_CONTRACTORS if c["id"] != contractor_id]

    print("APPROVE:", contractor_id, "FOUND:", found)

    return RedirectResponse("/admin", status_code=303)

@app.post("/reject/{contractor_id}")
def reject_contractor(contractor_id: str):
    global PENDING_CONTRACTORS

    before = len(PENDING_CONTRACTORS)

    PENDING_CONTRACTORS = [c for c in PENDING_CONTRACTORS if c["id"] != contractor_id]

    after = len(PENDING_CONTRACTORS)

    print("REJECT:", contractor_id, "REMOVED:", before != after)

    return RedirectResponse("/admin", status_code=303)

# =====================
# CONTRACTOR DASHBOARD
# =====================

@app.get("/contractor/{contractor_id}", response_class=HTMLResponse)
def contractor_dashboard(request: Request, contractor_id: str):
    contractor = get_contractor(contractor_id)

    contractor_leads = [l for l in LEADS if l.get("contractor_id") == contractor_id]

    return templates.TemplateResponse(
        "contractor-dashboard.html",
        {
            "request": request,
            "contractor": contractor,
            "leads": contractor_leads
        }
    )
