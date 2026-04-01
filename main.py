from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import os

app = FastAPI(title="LeadForge API")

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

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ----------------------------
# Helpers
# ----------------------------

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def normalize_email(value: Any) -> str:
    return safe_str(value).lower()


def normalize_phone(value: Any) -> str:
    raw = safe_str(value)
    return "".join(ch for ch in raw if ch.isdigit())


def normalize_text(value: Any) -> str:
    return " ".join(safe_str(value).lower().split())


def get_single_row(rows: Any) -> Optional[Dict[str, Any]]:
    if isinstance(rows, list):
        return rows[0] if rows else None
    return rows


def contractor_exists_and_approved(contractor_id: int) -> Optional[Dict[str, Any]]:
    result = (
        supabase.table("contractors")
        .select("*")
        .eq("id", contractor_id)
        .limit(1)
        .execute()
    )
    contractor = get_single_row(result.data)
    if not contractor:
        return None

    status = safe_str(contractor.get("status")).lower()
    approved_flag = contractor.get("approved")

    is_approved = status == "approved" or approved_flag is True
    if not is_approved:
        return None

    return contractor


def find_duplicate_active_lead(
    homeowner_email: str,
    homeowner_phone: str,
    property_address: str,
) -> Optional[Dict[str, Any]]:
    """
    A homeowner can only have ONE active request in the system at a time.
    We treat these statuses as active/open.
    """
    active_statuses = ["new", "notified", "locked", "claimed", "released", "contacted"]

    # Check by email
    if homeowner_email:
        result = (
            supabase.table("leads")
            .select("*")
            .eq("homeowner_email_normalized", homeowner_email)
            .in_("status", active_statuses)
            .order("id", desc=True)
            .limit(1)
            .execute()
        )
        row = get_single_row(result.data)
        if row:
            return row

    # Check by phone
    if homeowner_phone:
        result = (
            supabase.table("leads")
            .select("*")
            .eq("homeowner_phone_normalized", homeowner_phone)
            .in_("status", active_statuses)
            .order("id", desc=True)
            .limit(1)
            .execute()
        )
        row = get_single_row(result.data)
        if row:
            return row

    # Check by address
    if property_address:
        result = (
            supabase.table("leads")
            .select("*")
            .eq("property_address_normalized", property_address)
            .in_("status", active_statuses)
            .order("id", desc=True)
            .limit(1)
            .execute()
        )
        row = get_single_row(result.data)
        if row:
            return row

    return None


def build_public_contractor(contractor: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": contractor.get("id"),
        "business_name": contractor.get("business_name"),
        "contact_name": contractor.get("contact_name"),
        "phone": contractor.get("phone"),
        "email": contractor.get("email"),
        "city": contractor.get("city"),
        "state": contractor.get("state"),
        "zip_code": contractor.get("zip_code"),
        "category": contractor.get("category"),
        "services": contractor.get("services"),
        "bio": contractor.get("bio"),
        "website": contractor.get("website"),
        "status": contractor.get("status"),
        "approved": contractor.get("approved"),
        "created_at": contractor.get("created_at"),
    }


def build_locked_lead_preview(lead: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": lead.get("id"),
        "contractor_id": lead.get("contractor_id"),
        "project_type": lead.get("project_type"),
        "city": lead.get("city"),
        "state": lead.get("state"),
        "zip_code": lead.get("zip_code"),
        "message": lead.get("message"),
        "status": lead.get("status"),
        "locked": lead.get("locked"),
        "unlocked": lead.get("unlocked"),
        "exclusive": lead.get("exclusive"),
        "created_at": lead.get("created_at"),
        "badge": "EXCLUSIVE REQUEST",
        "unlock_fee": 10,
        "unlock_label": "Unlock Request",
    }


def build_unlocked_lead(lead: Dict[str, Any]) -> Dict[str, Any]:
    return {
        **build_locked_lead_preview(lead),
        "homeowner_name": lead.get("homeowner_name"),
        "homeowner_email": lead.get("homeowner_email"),
        "homeowner_phone": lead.get("homeowner_phone"),
        "property_address": lead.get("property_address"),
    }


# ----------------------------
# Health / Root
# ----------------------------

@app.get("/")
def root():
    return {"message": "API WORKING"}


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "LeadForge API",
        "timestamp": now_iso(),
    }


# ----------------------------
# Contractors
# ----------------------------

@app.get("/admin")
def admin():
    result = (
        supabase.table("contractors")
        .select("*")
        .order("id", desc=True)
        .execute()
    )
    return result.data


@app.get("/contractors")
def get_public_contractors(category: Optional[str] = None):
    """
    Public contractor list.
    Only approved contractors should be visible.
    Supports optional category filter for future frontend use.
    """
    result = (
        supabase.table("contractors")
        .select("*")
        .eq("status", "approved")
        .order("id", desc=True)
        .execute()
    )

    contractors = result.data or []

    if category:
        normalized_category = normalize_text(category)
        contractors = [
            c for c in contractors
            if normalize_text(c.get("category")) == normalized_category
        ]

    return [build_public_contractor(c) for c in contractors]


@app.get("/contractors/{contractor_id}")
def get_contractor_profile(contractor_id: int):
    """
    Public contractor profile.
    Only approved contractors should be visible publicly.
    """
    contractor = contractor_exists_and_approved(contractor_id)
    if not contractor:
        raise HTTPException(status_code=404, detail="Approved contractor not found")

    return build_public_contractor(contractor)


@app.post("/contractors")
async def create_contractor(request: Request):
    data = await request.json()

    payload = {
        "business_name": safe_str(data.get("business_name")),
        "contact_name": safe_str(data.get("contact_name")),
        "phone": safe_str(data.get("phone")),
        "email": normalize_email(data.get("email")),
        "city": safe_str(data.get("city")),
        "state": safe_str(data.get("state")),
        "zip_code": safe_str(data.get("zip_code")),
        "category": safe_str(data.get("category")),
        "services": safe_str(data.get("services")),
        "bio": safe_str(data.get("bio")),
        "website": safe_str(data.get("website")),
        "status": "pending",
        "approved": False,
        "created_at": now_iso(),
    }

    result = supabase.table("contractors").insert(payload).execute()
    return {
        "success": True,
        "message": "Contractor submitted successfully",
        "data": result.data,
    }


@app.post("/contractors/approve/{contractor_id}")
def approve_contractor(contractor_id: int):
    existing = (
        supabase.table("contractors")
        .select("*")
        .eq("id", contractor_id)
        .limit(1)
        .execute()
    )
    contractor = get_single_row(existing.data)
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")

    result = (
        supabase.table("contractors")
        .update(
            {
                "status": "approved",
                "approved": True,
            }
        )
        .eq("id", contractor_id)
        .execute()
    )

    return {
        "success": True,
        "message": f"Contractor {contractor_id} approved",
        "data": result.data,
    }


@app.post("/contractors/reject/{contractor_id}")
def reject_contractor(contractor_id: int):
    existing = (
        supabase.table("contractors")
        .select("*")
        .eq("id", contractor_id)
        .limit(1)
        .execute()
    )
    contractor = get_single_row(existing.data)
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")

    result = (
        supabase.table("contractors")
        .update(
            {
                "status": "rejected",
                "approved": False,
            }
        )
        .eq("id", contractor_id)
        .execute()
    )

    return {
        "success": True,
        "message": f"Contractor {contractor_id} rejected",
        "data": result.data,
    }


# ----------------------------
# Leads
# ----------------------------

@app.post("/leads")
async def create_lead(request: Request):
    """
    Exclusive homeowner request flow:
    - homeowner picks ONE contractor
    - one active homeowner request only
    - duplicate attempts blocked
    - lead is locked until contractor pays/unlocks later
    """
    data = await request.json()

    contractor_id_raw = data.get("contractor_id")
    if contractor_id_raw is None:
        raise HTTPException(status_code=400, detail="contractor_id is required")

    try:
        contractor_id = int(contractor_id_raw)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="contractor_id must be a number")

    contractor = contractor_exists_and_approved(contractor_id)
    if not contractor:
        raise HTTPException(status_code=404, detail="Selected contractor is not available")

    homeowner_name = safe_str(data.get("homeowner_name"))
    homeowner_email = normalize_email(data.get("homeowner_email"))
    homeowner_phone = normalize_phone(data.get("homeowner_phone"))
    property_address = safe_str(data.get("property_address"))
    city = safe_str(data.get("city"))
    state = safe_str(data.get("state"))
    zip_code = safe_str(data.get("zip_code"))
    project_type = safe_str(data.get("project_type"))
    message = safe_str(data.get("message"))

    if not homeowner_name:
        raise HTTPException(status_code=400, detail="homeowner_name is required")
    if not homeowner_email and not homeowner_phone:
        raise HTTPException(
            status_code=400,
            detail="At least one contact method is required (email or phone)",
        )
    if not project_type:
        raise HTTPException(status_code=400, detail="project_type is required")

    duplicate = find_duplicate_active_lead(
        homeowner_email=homeowner_email,
        homeowner_phone=homeowner_phone,
        property_address=normalize_text(property_address),
    )

    if duplicate:
        # Save a blocked attempt for tracking if possible
        blocked_payload = {
            "contractor_id": contractor_id,
            "homeowner_name": homeowner_name,
            "homeowner_email": homeowner_email,
            "homeowner_email_normalized": homeowner_email,
            "homeowner_phone": safe_str(data.get("homeowner_phone")),
            "homeowner_phone_normalized": homeowner_phone,
            "property_address": property_address,
            "property_address_normalized": normalize_text(property_address),
            "city": city,
            "state": state,
            "zip_code": zip_code,
            "project_type": project_type,
            "message": message,
            "status": "blocked_duplicate",
            "exclusive": True,
            "locked": True,
            "unlocked": False,
            "unlock_fee_paid": False,
            "created_at": now_iso(),
        }

        try:
            supabase.table("leads").insert(blocked_payload).execute()
        except Exception:
            pass

        raise HTTPException(
            status_code=409,
            detail="You already have an active request in the system. Only one active request is allowed at a time.",
        )

    payload = {
        "contractor_id": contractor_id,
        "contractor_business_name": contractor.get("business_name"),
        "contractor_category": contractor.get("category"),
        "homeowner_name": homeowner_name,
        "homeowner_email": homeowner_email,
        "homeowner_email_normalized": homeowner_email,
        "homeowner_phone": safe_str(data.get("homeowner_phone")),
        "homeowner_phone_normalized": homeowner_phone,
        "property_address": property_address,
        "property_address_normalized": normalize_text(property_address),
        "city": city,
        "state": state,
        "zip_code": zip_code,
        "project_type": project_type,
        "message": message,
        "status": "new",
        "exclusive": True,
        "locked": True,
        "unlocked": False,
        "unlock_fee_paid": False,
        "unlock_fee_amount": 10,
        "created_at": now_iso(),
    }

    result = supabase.table("leads").insert(payload).execute()
    new_lead = get_single_row(result.data)

    return {
        "success": True,
        "message": "Your request was sent. Only one contractor request is allowed at a time.",
        "lead": build_locked_lead_preview(new_lead) if new_lead else None,
        "admin_alert": True,
        "contractor_alert": True,
    }


@app.get("/leads")
def get_all_leads():
    """
    Admin use.
    Returns all leads.
    """
    result = (
        supabase.table("leads")
        .select("*")
        .order("id", desc=True)
        .execute()
    )
    return result.data


@app.get("/leads/{lead_id}/preview")
def get_lead_preview(lead_id: int):
    """
    Contractor-safe preview before unlock/payment.
    """
    result = (
        supabase.table("leads")
        .select("*")
        .eq("id", lead_id)
        .limit(1)
        .execute()
    )
    lead = get_single_row(result.data)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    return build_locked_lead_preview(lead)


@app.get("/leads/{lead_id}")
def get_lead_details(lead_id: int):
    """
    Full lead details only after unlock.
    For now this supports your future unlock flow.
    """
    result = (
        supabase.table("leads")
        .select("*")
        .eq("id", lead_id)
        .limit(1)
        .execute()
    )
    lead = get_single_row(result.data)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if not lead.get("unlocked"):
        return build_locked_lead_preview(lead)

    return build_unlocked_lead(lead)


@app.post("/leads/{lead_id}/unlock")
async def unlock_lead(lead_id: int, request: Request):
    """
    Placeholder unlock endpoint.
    Right now this marks the lead unlocked after a successful admin/payment action.
    Stripe/payment wiring comes next.
    """
    _ = await request.json()

    existing = (
        supabase.table("leads")
        .select("*")
        .eq("id", lead_id)
        .limit(1)
        .execute()
    )
    lead = get_single_row(existing.data)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if lead.get("unlocked") is True:
        return {
            "success": True,
            "message": "Lead already unlocked",
            "lead": build_unlocked_lead(lead),
        }

    result = (
        supabase.table("leads")
        .update(
            {
                "status": "released",
                "locked": False,
                "unlocked": True,
                "unlock_fee_paid": True,
                "unlocked_at": now_iso(),
            }
        )
        .eq("id", lead_id)
        .execute()
    )

    updated = get_single_row(result.data)

    return {
        "success": True,
        "message": "Lead unlocked successfully",
        "lead": build_unlocked_lead(updated) if updated else None,
    }
