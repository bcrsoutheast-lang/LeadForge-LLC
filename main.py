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


def safe_data(response: Any):
    return getattr(response, "data", None)


def safe_single(response: Any):
    data = safe_data(response)
    if isinstance(data, list):
        return data[0] if data else None
    return data


def is_approved(contractor: dict) -> bool:
    return contractor.get("status") == "approved" or contractor.get("approved") is True


@app.get("/")
def root():
    return {"message": "API WORKING"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/admin")
def get_admin_contractors():
    try:
        response = (
            supabase.table("contractors")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        return safe_data(response) or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Admin fetch failed: {str(e)}")


@app.get("/contractors/approve/{contractor_id}")
def approve_contractor_get(contractor_id: str):
    return approve_contractor_logic(contractor_id, "GET")


@app.post("/contractors/approve/{contractor_id}")
def approve_contractor_post(contractor_id: str):
    return approve_contractor_logic(contractor_id, "POST")


def approve_contractor_logic(contractor_id: str, method_used: str):
    try:
        existing = (
            supabase.table("contractors")
            .select("*")
            .eq("id", contractor_id)
            .execute()
        )

        contractor = safe_single(existing)

        if not contractor:
            raise HTTPException(status_code=404, detail="Contractor not found")

        update_payload = {
            "status": "approved",
            "approved": True,
        }

        response = (
            supabase.table("contractors")
            .update(update_payload)
            .eq("id", contractor_id)
            .execute()
        )

        updated = safe_single(response)

        if not updated:
            reread = (
                supabase.table("contractors")
                .select("*")
                .eq("id", contractor_id)
                .execute()
            )
            updated = safe_single(reread)

        return {
            "message": f"approved via {method_used}",
            "contractor": updated,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Approve failed: {str(e)}")


@app.get("/contractors/reject/{contractor_id}")
def reject_contractor_get(contractor_id: str):
    return reject_contractor_logic(contractor_id, "GET")


@app.post("/contractors/reject/{contractor_id}")
def reject_contractor_post(contractor_id: str):
    return reject_contractor_logic(contractor_id, "POST")


def reject_contractor_logic(contractor_id: str, method_used: str):
    try:
        existing = (
            supabase.table("contractors")
            .select("*")
            .eq("id", contractor_id)
            .execute()
        )

        contractor = safe_single(existing)

        if not contractor:
            raise HTTPException(status_code=404, detail="Contractor not found")

        update_payload = {
            "status": "rejected",
            "approved": False,
        }

        response = (
            supabase.table("contractors")
            .update(update_payload)
            .eq("id", contractor_id)
            .execute()
        )

        updated = safe_single(response)

        if not updated:
            reread = (
                supabase.table("contractors")
                .select("*")
                .eq("id", contractor_id)
                .execute()
            )
            updated = safe_single(reread)

        return {
            "message": f"rejected via {method_used}",
            "contractor": updated,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reject failed: {str(e)}")


@app.get("/contractors")
def get_public_contractors():
    try:
        response = (
            supabase.table("contractors")
            .select("*")
            .eq("status", "approved")
            .order("created_at", desc=True)
            .execute()
        )

        data = safe_data(response) or []

        if data:
            return data

        fallback = (
            supabase.table("contractors")
            .select("*")
            .eq("approved", True)
            .order("created_at", desc=True)
            .execute()
        )

        return safe_data(fallback) or []

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Public contractors fetch failed: {str(e)}")


@app.get("/contractors/{contractor_id}")
def get_contractor(contractor_id: str):
    try:
        response = (
            supabase.table("contractors")
            .select("*")
            .eq("id", contractor_id)
            .execute()
        )

        contractor = safe_single(response)

        if not contractor:
            raise HTTPException(status_code=404, detail="Contractor not found")

        if not is_approved(contractor):
            raise HTTPException(status_code=404, detail="Contractor not found")

        return contractor

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Single contractor fetch failed: {str(e)}")


@app.post("/contractors")
def create_contractor(contractor: ContractorCreate):
    try:
        payload = contractor.dict()

        payload["created_at"] = datetime.utcnow().isoformat()

        if "status" not in payload or payload.get("status") is None:
            payload["status"] = "pending"

        if "approved" not in payload or payload.get("approved") is None:
            payload["approved"] = False

        response = supabase.table("contractors").insert(payload).execute()
        created = safe_single(response)

        return {
            "message": "Contractor submitted",
            "contractor": created,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Create contractor failed: {str(e)}")


@app.post("/leads")
def create_lead(lead: LeadCreate):
    try:
        contractor_check = (
            supabase.table("contractors")
            .select("*")
            .eq("id", lead.contractor_id)
            .execute()
        )
        contractor = safe_single(contractor_check)

        if not contractor:
            raise HTTPException(status_code=404, detail="Contractor not found")

        if not is_approved(contractor):
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

        existing_active = safe_data(duplicate_check) or []

        if existing_active:
            raise HTTPException(
                status_code=400,
                detail="You already have an active request",
            )

        payload = {
            "contractor_id": lead.contractor_id,
            "name": lead.homeowner_name or lead.name,
            "homeowner_name": lead.homeowner_name or lead.name,
            "email": lead.email,
            "phone": lead.phone,
            "details": lead.details or lead.message,
            "project_type": lead.project_type,
            "address": lead.address,
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

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Create lead failed: {str(e)}")
