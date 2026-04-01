from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client
from datetime import datetime
from typing import Optional, Any
import os
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Missing SUPABASE_URL or SUPABASE_KEY environment variables")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


class ContractorCreate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    business_name: Optional[str] = None
    trade: Optional[str] = None
    experience_years: Optional[str] = None
    service_area: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    license_number: Optional[str] = None
    insured: Optional[bool] = None
    agreed_to_terms: Optional[bool] = None
    agreement_version: Optional[str] = None
    agreement_timestamp: Optional[str] = None
    ip_address: Optional[str] = None

    company_name: Optional[str] = None
    owner_name: Optional[str] = None
    business_type: Optional[str] = None
    crew_size: Optional[str] = None
    years_in_business: Optional[str] = None
    bio: Optional[str] = None
    insurance_type: Optional[str] = None
    insurance_coverage: Optional[str] = None
    notes: Optional[str] = None

    category: Optional[str] = None
    services: Optional[str] = None
    website: Optional[str] = None


class LeadCreate(BaseModel):
    contractor_id: str
    name: Optional[str] = None
    homeowner_name: Optional[str] = None
    email: str
    phone: str
    details: Optional[str] = None
    project_type: Optional[str] = None
    message: Optional[str] = None
    address: Optional[str] = None


def normalize_email(email: Optional[str]) -> str:
    return (email or "").strip().lower()


def normalize_phone(phone: Optional[str]) -> str:
    return re.sub(r"\D", "", phone or "")


def safe_single(response: Any):
    data = getattr(response, "data", None)
    if isinstance(data, list):
        return data[0] if data else None
    return data


@app.get("/")
def root():
    return {"message": "API WORKING"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/admin")
def get_admin_contractors():
    response = (
        supabase.table("contractors")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


@app.get("/contractors")
def get_public_contractors():
    response = (
        supabase.table("contractors")
        .select("*")
        .eq("status", "approved")
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


@app.get("/contractors/{contractor_id}")
def get_contractor(contractor_id: str):
    response = (
        supabase.table("contractors")
        .select("*")
        .eq("id", contractor_id)
        .execute()
    )

    contractor = safe_single(response)

    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")

    if contractor.get("status") != "approved":
        raise HTTPException(status_code=404, detail="Contractor not approved")

    return contractor


@app.post("/contractors")
def create_contractor(contractor: ContractorCreate):
    payload = contractor.dict()

    payload["created_at"] = datetime.utcnow().isoformat()
    payload["status"] = "pending"
    payload["approved"] = False

    response = supabase.table("contractors").insert(payload).execute()
    created = safe_single(response)

    return {
        "message": "Contractor submitted",
        "contractor": created,
    }


# 🔥 POST APPROVE (normal)
@app.post("/contractors/approve/{contractor_id}")
def approve_contractor(contractor_id: str):
    response = (
        supabase.table("contractors")
        .update({"status": "approved", "approved": True})
        .eq("id", contractor_id)
        .execute()
    )

    updated = safe_single(response)

    return {
        "message": "approved",
        "contractor": updated,
    }


# 🔥 GET APPROVE (TEMP FOR PHONE USE)
@app.get("/contractors/approve/{contractor_id}")
def approve_contractor_get(contractor_id: str):
    response = (
        supabase.table("contractors")
        .update({"status": "approved", "approved": True})
        .eq("id", contractor_id)
        .execute()
    )

    updated = safe_single(response)

    return {
        "message": "approved via GET",
        "contractor": updated,
    }


@app.post("/contractors/reject/{contractor_id}")
def reject_contractor(contractor_id: str):
    response = (
        supabase.table("contractors")
        .update({"status": "rejected", "approved": False})
        .eq("id", contractor_id)
        .execute()
    )

    updated = safe_single(response)

    return {
        "message": "rejected",
        "contractor": updated,
    }


@app.post("/leads")
def create_lead(lead: LeadCreate):
    contractor_check = (
        supabase.table("contractors")
        .select("*")
        .eq("id", lead.contractor_id)
        .execute()
    )
    contractor = safe_single(contractor_check)

    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")

    if contractor.get("status") != "approved":
        raise HTTPException(status_code=400, detail="Contractor not approved")

    normalized_email = normalize_email(lead.email)
    normalized_phone = normalize_phone(lead.phone)

    duplicate_check = (
        supabase.table("leads")
        .select("*")
        .or_(
            f"normalized_email.eq.{normalized_email},normalized_phone.eq.{normalized_phone}"
        )
        .eq("locked", True)
        .execute()
    )

    if duplicate_check.data:
        raise HTTPException(
            status_code=400,
            detail="You already have an active request",
        )

    payload = {
        "contractor_id": lead.contractor_id,
        "name": lead.homeowner_name or lead.name,
        "email": lead.email,
        "phone": lead.phone,
        "details": lead.details or lead.message,
        "normalized_email": normalized_email,
        "normalized_phone": normalized_phone,
        "locked": True,
        "unlocked": False,
        "created_at": datetime.utcnow().isoformat(),
    }

    response = supabase.table("leads").insert(payload).execute()
    created = safe_single(response)

    return {
        "message": "Request submitted",
        "lead": created,
    }
