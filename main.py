from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from supabase import create_client
import uuid

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# =========================================================
# SUPABASE
# REPLACE THESE TWO VALUES WITH YOUR REAL SUPABASE VALUES
# =========================================================
SUPABASE_URL = "https://YOUR_PROJECT_ID.supabase.co"
SUPABASE_KEY = "YOUR_ANON_KEY"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# =========================================================
# HOME
# =========================================================
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/services", response_class=HTMLResponse)
def services_page(request: Request):
    return templates.TemplateResponse(
        "services.html",
        {"request": request}
    )


# =========================================================
# CONTRACTOR JOIN
# =========================================================
@app.get("/join-contractor", response_class=HTMLResponse)
def join_contractor(request: Request):
    return templates.TemplateResponse(
        "join-contractor.html",
        {"request": request}
    )


@app.post("/join-contractor")
def submit_contractor(
    full_name: str = Form(...),
    company_name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    service: str = Form(...),
    city: str = Form(...),
    state: str = Form(...),
    zip_code: str = Form(...),
    bio: str = Form(...)
):
    supabase.table("contractors").insert({
        "id": str(uuid.uuid4()),
        "contact_name": full_name,
        "company_name": company_name,
        "service": service,
        "city": city,
        "state": state,
        "zip_code": zip_code,
        "phone": phone,
        "email": email,
        "bio": bio,
        "approved": False
    }).execute()

    return RedirectResponse("/join-contractor-success", status_code=303)


@app.get("/join-contractor-success", response_class=HTMLResponse)
def join_success(request: Request):
    return templates.TemplateResponse(
        "join-contractor-success.html",
        {"request": request}
    )


# =========================================================
# CONTRACTORS
# =========================================================
@app.get("/contractors", response_class=HTMLResponse)
def contractors(request: Request, service: str = None):
    query = supabase.table("contractors").select("*").eq("approved", True)

    if service:
        query = query.ilike("service", f"%{service}%")

    result = query.execute()
    data = result.data if result.data else []

    return templates.TemplateResponse(
        "contractors.html",
        {
            "request": request,
            "contractors": data,
            "service": service
        }
    )


# =========================================================
# HOMEOWNER REQUEST
# =========================================================
@app.get("/request/{contractor_id}", response_class=HTMLResponse)
def request_page(request: Request, contractor_id: str):
    contractor_result = (
        supabase
        .table("contractors")
        .select("*")
        .eq("id", contractor_id)
        .execute()
    )

    contractor_data = contractor_result.data[0] if contractor_result.data else None

    return templates.TemplateResponse(
        "request.html",
        {
            "request": request,
            "contractor": contractor_data,
            "contractor_id": contractor_id
        }
    )


@app.post("/request/{contractor_id}")
def submit_request(
    contractor_id: str,
    owner_name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    service: str = Form(...),
    city: str = Form(...),
    state: str = Form(...),
    zip: str = Form(...),
    project_details: str = Form(...)
):
    contractor_result = (
        supabase
        .table("contractors")
        .select("contact_name, company_name")
        .eq("id", contractor_id)
        .execute()
    )

    contractor_data = contractor_result.data[0] if contractor_result.data else {}

    contractor_name = (
        contractor_data.get("company_name")
        or contractor_data.get("contact_name")
        or "LeadForge Contractor"
    )

    supabase.table("leads").insert({
        "id": str(uuid.uuid4()),
        "contractor_id": contractor_id,
        "contractor_name": contractor_name,
        "homeowner_name": owner_name,
        "phone": phone,
        "email": email,
        "service": service,
        "city": city,
        "state": state,
        "zip_code": zip,
        "project_details": project_details,
        "unlocked": False,
        "stripe_paid": False
    }).execute()

    return RedirectResponse("/request-success", status_code=303)


@app.get("/request-success", response_class=HTMLResponse)
def request_success(request: Request):
    return templates.TemplateResponse(
        "request-success.html",
        {"request": request}
    )


# =========================================================
# ADMIN
# =========================================================
@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    pending_result = (
        supabase
        .table("contractors")
        .select("*")
        .eq("approved", False)
        .execute()
    )

    approved_result = (
        supabase
        .table("contractors")
        .select("*")
        .eq("approved", True)
        .execute()
    )

    leads_result = (
        supabase
        .table("leads")
        .select("*")
        .execute()
    )

    pending = pending_result.data if pending_result.data else []
    approved = approved_result.data if approved_result.data else []
    leads = leads_result.data if leads_result.data else []

    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "pending_contractors": pending,
            "approved_contractors": approved,
            "contractors": approved,
            "leads": leads
        }
    )


@app.post("/approve/{contractor_id}")
def approve_contractor(contractor_id: str):
    supabase.table("contractors").update({
        "approved": True
    }).eq("id", contractor_id).execute()

    return RedirectResponse("/admin", status_code=303)


@app.post("/reject/{contractor_id}")
def reject_contractor(contractor_id: str):
    supabase.table("contractors").delete().eq("id", contractor_id).execute()

    return RedirectResponse("/admin", status_code=303)
