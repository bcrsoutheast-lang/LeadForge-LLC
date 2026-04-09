import os
import uuid
from typing import List, Optional

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from supabase import create_client

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_KEY in environment variables.")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def normalize_service(value: str) -> str:
    if not value:
        return ""

    value = value.strip().lower()

    aliases = {
        "roofing": "roofing",
        "roof": "roofing",
        "roof repair": "roofing",
        "roof replacement": "roofing",
        "hvac": "hvac",
        "heating": "hvac",
        "air conditioning": "hvac",
        "ac": "hvac",
        "plumbing": "plumbing",
        "plumber": "plumbing",
        "electrical": "electrical",
        "electrician": "electrical",
        "remodeling": "remodeling",
        "remodel": "remodeling",
        "renovation": "remodeling",
        "fencing": "fencing",
        "fence": "fencing",
        "fence installation": "fencing",
        "soft-washing": "soft-washing",
        "soft washing": "soft-washing",
        "pressure washing": "soft-washing",
        "exterior cleaning": "soft-washing",
        "landscaping": "landscaping",
        "landscape": "landscaping",
        "handyman": "handyman",
        "junk-removal": "junk-removal",
        "junk removal": "junk-removal",
        "pest-control": "pest-control",
        "pest control": "pest-control",
        "cleaning": "cleaning",
        "house cleaning": "cleaning",
    }

    return aliases.get(value, value)


def pretty_service_name(value: str) -> str:
    names = {
        "roofing": "Roofing",
        "hvac": "HVAC",
        "plumbing": "Plumbing",
        "electrical": "Electrical",
        "remodeling": "Remodeling",
        "fencing": "Fencing",
        "soft-washing": "Exterior Cleaning",
        "landscaping": "Landscaping",
        "handyman": "Handyman",
        "junk-removal": "Junk Removal",
        "pest-control": "Pest Control",
        "cleaning": "Cleaning",
    }
    return names.get(value, value.title())


def normalize_services(values: Optional[List[str]]) -> List[str]:
    if not values:
        return []

    cleaned = []
    seen = set()

    for value in values:
        normalized = normalize_service(value)
        if normalized and normalized not in seen:
            cleaned.append(normalized)
            seen.add(normalized)

    return cleaned


def service_matches(contractor_service: str, selected_service: str) -> bool:
    contractor_value = (contractor_service or "").strip().lower()
    selected_value = normalize_service(selected_service)

    if not contractor_value or not selected_value:
        return False

    parts = [normalize_service(part.strip()) for part in contractor_value.split(",") if part.strip()]

    if selected_value in parts:
        return True

    for part in parts:
        if selected_value in part or part in selected_value:
            return True

    return False


def get_contractor_by_id(contractor_id: str):
    result = (
        supabase
        .table("contractors")
        .select("*")
        .eq("id", contractor_id)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {}
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/services", response_class=HTMLResponse)
def services_page(request: Request):
    return templates.TemplateResponse(
        request,
        "services.html",
        {}
    )


@app.get("/join-contractor", response_class=HTMLResponse)
def join_contractor(request: Request):
    return templates.TemplateResponse(
        request,
        "join-contractor.html",
        {}
    )


@app.post("/join-contractor")
def submit_contractor(
    full_name: str = Form(...),
    company_name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    service: List[str] = Form(...),
    city: str = Form(...),
    state: str = Form(...),
    zip_code: str = Form(...),
    bio: str = Form(...)
):
    normalized_services = normalize_services(service)
    service_display = ", ".join(pretty_service_name(item) for item in normalized_services)

    supabase.table("contractors").insert({
        "id": str(uuid.uuid4()),
        "contact_name": full_name,
        "company_name": company_name,
        "service": service_display,
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
        request,
        "join-contractor-success.html",
        {}
    )


@app.get("/contractors", response_class=HTMLResponse)
def contractors(request: Request, service: str = None):
    result = (
        supabase
        .table("contractors")
        .select("*")
        .eq("approved", True)
        .execute()
    )

    data = result.data if result.data else []

    if service:
        data = [
            contractor for contractor in data
            if service_matches(contractor.get("service", ""), service)
        ]

    return templates.TemplateResponse(
        request,
        "contractors.html",
        {
            "contractors": data,
            "service": service
        }
    )


@app.get("/request/{contractor_id}", response_class=HTMLResponse)
def request_page(request: Request, contractor_id: str):
    contractor = get_contractor_by_id(contractor_id)

    return templates.TemplateResponse(
        request,
        "request.html",
        {
            "contractor": contractor,
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
    contractor = get_contractor_by_id(contractor_id)
    contractor_name = "LeadForge Contractor"

    if contractor:
        contractor_name = (
            contractor.get("company_name")
            or contractor.get("contact_name")
            or contractor_name
        )

    supabase.table("leads").insert({
        "contractor_id": contractor_id,
        "contractor_name": contractor_name,
        "homeowner_name": owner_name,
        "phone": phone,
        "email": email,
        "service": normalize_service(service),
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
        request,
        "request-success.html",
        {}
    )


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
        .order("created_at", desc=True)
        .execute()
    )

    pending = pending_result.data if pending_result.data else []
    approved = approved_result.data if approved_result.data else []
    leads = leads_result.data if leads_result.data else []

    return templates.TemplateResponse(
        request,
        "admin.html",
        {
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


@app.get("/contractor/{contractor_id}", response_class=HTMLResponse)
def contractor_dashboard(request: Request, contractor_id: str):
    contractor = get_contractor_by_id(contractor_id)

    leads_result = (
        supabase
        .table("leads")
        .select("*")
        .eq("contractor_id", contractor_id)
        .order("created_at", desc=True)
        .execute()
    )

    contractor_leads = leads_result.data if leads_result.data else []

    return templates.TemplateResponse(
        request,
        "contractor-dashboard.html",
        {
            "contractor": contractor,
            "leads": contractor_leads
        }
    )
