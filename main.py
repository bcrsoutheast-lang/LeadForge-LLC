import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from supabase import create_client, Client


# =========================
# ENV
# =========================
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_KEY environment variables.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# =========================
# APP
# =========================
app = FastAPI(title="LeadForge API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later if you want
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# MODELS
# =========================
class LeadCreate(BaseModel):
    name: str = Field(..., min_length=1)
    email: EmailStr
    phone: str = Field(..., min_length=7)
    zip_code: Optional[str] = None
    project_type: str = Field(..., min_length=1)
    message: Optional[str] = None


class ContractorCreate(BaseModel):
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    business_name: str = Field(..., min_length=1)
    email: EmailStr
    phone: str = Field(..., min_length=7)
    trade: str = Field(..., min_length=1)
    service_area: str = Field(..., min_length=1)
    experience_years: Optional[str] = None
    license_number: Optional[str] = None
    insured: Optional[bool] = False

    agreed_to_terms: bool
    agreement_version: str = "v1.0"


# =========================
# HELPERS
# =========================
def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return ""


# =========================
# ROUTES
# =========================
@app.get("/")
def root():
    return {"message": "LeadForge API is live"}


@app.get("/debug-env")
def debug_env():
    return {
        "supabase_url_present": bool(SUPABASE_URL),
        "supabase_key_present": bool(SUPABASE_KEY),
    }


@app.post("/leads")
def create_lead(lead: LeadCreate):
    payload = {
        "name": lead.name,
        "email": lead.email,
        "phone": lead.phone,
        "zip_code": lead.zip_code,
        "project_type": lead.project_type,
        "message": lead.message,
        "created_at": utc_now_iso(),
    }

    try:
        result = supabase.table("leads").insert(payload).execute()
        return {
            "success": True,
            "message": "Lead submitted successfully.",
            "data": result.data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save lead: {str(e)}")


@app.post("/contractors")
def create_contractor(contractor: ContractorCreate, request: Request):
    if contractor.agreed_to_terms is not True:
        raise HTTPException(
            status_code=400,
            detail="You must agree to the LeadForge Contractor Agreement before submitting."
        )

    payload = {
        "first_name": contractor.first_name,
        "last_name": contractor.last_name,
        "business_name": contractor.business_name,
        "email": contractor.email,
        "phone": contractor.phone,
        "trade": contractor.trade,
        "service_area": contractor.service_area,
        "experience_years": contractor.experience_years,
        "license_number": contractor.license_number,
        "insured": contractor.insured,
        "agreed_to_terms": contractor.agreed_to_terms,
        "agreement_version": contractor.agreement_version,
        "agreement_timestamp": utc_now_iso(),
        "ip_address": get_client_ip(request),
        "status": "pending",
        "created_at": utc_now_iso(),
    }

    try:
        result = supabase.table("contractors").insert(payload).execute()
        return {
            "success": True,
            "message": "Contractor application submitted successfully.",
            "data": result.data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save contractor: {str(e)}")


@app.get("/contractors")
def get_approved_contractors():
    try:
        result = (
            supabase
            .table("contractors")
            .select("*")
            .eq("status", "approved")
            .order("created_at", desc=True)
            .execute()
        )
        return {
            "success": True,
            "data": result.data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch contractors: {str(e)}")


@app.get("/admin")
def get_all_contractors():
    try:
        result = (
            supabase
            .table("contractors")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        return {
            "success": True,
            "data": result.data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch admin data: {str(e)}")


@app.post("/contractors/approve/{contractor_id}")
def approve_contractor(contractor_id: int):
    try:
        result = (
            supabase
            .table("contractors")
            .update({"status": "approved"})
            .eq("id", contractor_id)
            .execute()
        )
        return {
            "success": True,
            "message": f"Contractor {contractor_id} approved.",
            "data": result.data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to approve contractor: {str(e)}")


@app.post("/contractors/reject/{contractor_id}")
def reject_contractor(contractor_id: int):
    try:
        result = (
            supabase
            .table("contractors")
            .update({"status": "rejected"})
            .eq("id", contractor_id)
            .execute()
        )
        return {
            "success": True,
            "message": f"Contractor {contractor_id} rejected.",
            "data": result.data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reject contractor: {str(e)}")
