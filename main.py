from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr
from supabase import create_client, Client
from datetime import datetime, timezone
from typing import Optional, Any, Dict, List
import os


app = FastAPI(title="LeadForge API", version="1.0.0")


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
# Models
# ----------------------------

class LeadCreate(BaseModel):
    name: str
    phone: str
    email: EmailStr
    city: str
    state: str
    zip_code: str
    service: str
    project_details: str


class ContractorCreate(BaseModel):
    company_name: str
    contact_name: str
    phone: str
    email: EmailStr
    services_offered: str
    service_area: str
    licensed_insured: str
    notes: Optional[str] = ""


class UnlockTestRequest(BaseModel):
    contractor_id: Optional[str] = None
    payment_reference: Optional[str] = None


# ----------------------------
# Helpers
# ----------------------------

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def table_insert(table_name: str, payload: Dict[str, Any]):
    try:
        return supabase.table(table_name).insert(payload).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Insert failed for table '{table_name}': {str(e)}")


def table_select(table_name: str, select_str: str = "*"):
    try:
        return supabase.table(table_name).select(select_str)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Select setup failed for table '{table_name}': {str(e)}")


def get_lead_by_id(lead_id: str) -> Dict[str, Any]:
    try:
        response = (
            supabase.table("leads")
            .select("*")
            .eq("id", lead_id)
            .limit(1)
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query lead: {str(e)}")

    data = response.data or []
    if not data:
        raise HTTPException(status_code=404, detail="Lead not found")

    return data[0]


def get_unlock_record(lead_id: str) -> Optional[Dict[str, Any]]:
    try:
        response = (
            supabase.table("lead_unlocks")
            .select("*")
            .eq("lead_id", lead_id)
            .eq("status", "paid")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
    except Exception as e:
        message = str(e)
        if "lead_unlocks" in message.lower() or "relation" in message.lower():
            raise HTTPException(
                status_code=500,
                detail=(
                    "lead_unlocks table is missing. Create it first, then redeploy. "
                    "Scroll down for the SQL in the setup section."
                ),
            )
        raise HTTPException(status_code=500, detail=f"Failed to query lead unlocks: {message}")

    data = response.data or []
    return data[0] if data else None


def build_lead_preview(lead: Dict[str, Any]) -> Dict[str, Any]:
    submitted_at = lead.get("created_at") or lead.get("submitted_at") or ""
    area = lead.get("zip_code") or ""
    details = (lead.get("project_details") or "").strip()
    preview = details[:120] + ("..." if len(details) > 120 else "")

    return {
        "id": lead.get("id"),
        "service": lead.get("service"),
        "city": lead.get("city"),
        "state": lead.get("state"),
        "zip_code": lead.get("zip_code"),
        "preview": preview,
        "submitted_at": submitted_at,
        "status": "locked",
        "area": area,
    }


def build_lead_full(lead: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": lead.get("id"),
        "name": lead.get("name"),
        "phone": lead.get("phone"),
        "email": lead.get("email"),
        "city": lead.get("city"),
        "state": lead.get("state"),
        "zip_code": lead.get("zip_code"),
        "service": lead.get("service"),
        "project_details": lead.get("project_details"),
        "created_at": lead.get("created_at"),
        "status": "unlocked",
    }


# ----------------------------
# Basic routes
# ----------------------------

@app.get("/")
def root():
    return {"message": "API WORKING"}


@app.get("/health")
def health():
    return {
        "ok": True,
        "service": "leadforge-api",
        "timestamp": now_iso(),
    }


# ----------------------------
# Leads
# ----------------------------

@app.post("/leads")
def create_lead(lead: LeadCreate):
    payload = {
        "name": lead.name.strip(),
        "phone": lead.phone.strip(),
        "email": lead.email.strip(),
        "city": lead.city.strip(),
        "state": lead.state.strip(),
        "zip_code": lead.zip_code.strip(),
        "service": lead.service.strip(),
        "project_details": lead.project_details.strip(),
    }

    try:
        response = supabase.table("leads").insert(payload).execute()
        inserted = response.data[0] if response.data else None
        return {
            "success": True,
            "message": "Lead received",
            "lead": inserted,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save lead: {str(e)}")


@app.get("/leads")
def get_leads():
    try:
        response = (
            supabase.table("leads")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        return response.data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch leads: {str(e)}")


@app.get("/leads/{lead_id}/preview")
def get_lead_preview(lead_id: str):
    lead = get_lead_by_id(lead_id)
    return build_lead_preview(lead)


@app.get("/leads/{lead_id}/unlock-status")
def get_lead_unlock_status(lead_id: str):
    lead = get_lead_by_id(lead_id)
    unlock = get_unlock_record(lead_id)

    return {
        "lead_id": lead.get("id"),
        "unlocked": unlock is not None,
        "status": "paid" if unlock else "locked",
        "preview": build_lead_preview(lead),
        "unlocked_at": unlock.get("created_at") if unlock else None,
        "contractor_id": unlock.get("contractor_id") if unlock else None,
    }


@app.get("/leads/{lead_id}/full")
def get_lead_full(lead_id: str):
    lead = get_lead_by_id(lead_id)
    unlock = get_unlock_record(lead_id)

    if not unlock:
        raise HTTPException(status_code=403, detail="Lead is still locked")

    return build_lead_full(lead)


@app.post("/leads/{lead_id}/test-unlock")
def test_unlock_lead(lead_id: str, payload: UnlockTestRequest):
    # Temporary route to prove real backend unlock flow
    # We will replace this later with Stripe webhook confirmation
    lead = get_lead_by_id(lead_id)

    existing_unlock = get_unlock_record(lead_id)
    if existing_unlock:
        return {
            "success": True,
            "message": "Lead already unlocked",
            "lead_id": lead.get("id"),
            "unlock": existing_unlock,
        }

    insert_payload = {
        "lead_id": lead_id,
        "contractor_id": payload.contractor_id,
        "status": "paid",
        "payment_reference": payload.payment_reference or f"manual-test-{lead_id}",
    }

    try:
        response = supabase.table("lead_unlocks").insert(insert_payload).execute()
        unlock_row = response.data[0] if response.data else None
        return {
            "success": True,
            "message": "Lead unlocked for testing",
            "lead_id": lead.get("id"),
            "unlock": unlock_row,
        }
    except Exception as e:
        message = str(e)
        if "lead_unlocks" in message.lower() or "relation" in message.lower():
            raise HTTPException(
                status_code=500,
                detail=(
                    "lead_unlocks table is missing. Create it first, then redeploy. "
                    "Scroll down for the SQL in the setup section."
                ),
            )
        raise HTTPException(status_code=500, detail=f"Failed to create unlock record: {message}")


# ----------------------------
# Contractors
# ----------------------------

@app.post("/contractors")
def create_contractor(contractor: ContractorCreate):
    payload = {
        "company_name": contractor.company_name.strip(),
        "contact_name": contractor.contact_name.strip(),
        "phone": contractor.phone.strip(),
        "email": contractor.email.strip(),
        "services_offered": contractor.services_offered.strip(),
        "service_area": contractor.service_area.strip(),
        "licensed_insured": contractor.licensed_insured.strip(),
        "notes": (contractor.notes or "").strip(),
        "approved": False,
        "rejected": False,
    }

    try:
        response = supabase.table("contractors").insert(payload).execute()
        inserted = response.data[0] if response.data else None
        return {
            "success": True,
            "message": "Contractor application received",
            "contractor": inserted,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save contractor: {str(e)}")


@app.get("/contractors")
def get_contractors():
    try:
        response = (
            supabase.table("contractors")
            .select("*")
            .eq("approved", True)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch contractors: {str(e)}")


@app.get("/contractors/{contractor_id}")
def get_contractor(contractor_id: str):
    try:
        response = (
            supabase.table("contractors")
            .select("*")
            .eq("id", contractor_id)
            .limit(1)
            .execute()
        )
        data = response.data or []
        if not data:
            raise HTTPException(status_code=404, detail="Contractor not found")
        return data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch contractor: {str(e)}")


@app.post("/contractors/approve/{contractor_id}")
def approve_contractor(contractor_id: str):
    try:
        response = (
            supabase.table("contractors")
            .update({"approved": True, "rejected": False})
            .eq("id", contractor_id)
            .execute()
        )
        return {
            "success": True,
            "message": "Contractor approved",
            "data": response.data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to approve contractor: {str(e)}")


@app.post("/contractors/reject/{contractor_id}")
def reject_contractor(contractor_id: str):
    try:
        response = (
            supabase.table("contractors")
            .update({"approved": False, "rejected": True})
            .eq("id", contractor_id)
            .execute()
        )
        return {
            "success": True,
            "message": "Contractor rejected",
            "data": response.data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reject contractor: {str(e)}")


# ----------------------------
# Admin
# ----------------------------

@app.get("/admin", response_class=HTMLResponse)
def admin():
    try:
        leads_response = (
            supabase.table("leads")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        contractors_response = (
            supabase.table("contractors")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )

        leads = leads_response.data or []
        contractors = contractors_response.data or []

        lead_rows = ""
        for lead in leads:
            lead_rows += f"""
            <tr>
                <td>{lead.get('id', '')}</td>
                <td>{lead.get('name', '')}</td>
                <td>{lead.get('phone', '')}</td>
                <td>{lead.get('email', '')}</td>
                <td>{lead.get('city', '')}, {lead.get('state', '')} {lead.get('zip_code', '')}</td>
                <td>{lead.get('service', '')}</td>
                <td>{lead.get('project_details', '')}</td>
                <td>{lead.get('created_at', '')}</td>
            </tr>
            """

        contractor_rows = ""
        for contractor in contractors:
            contractor_rows += f"""
            <tr>
                <td>{contractor.get('id', '')}</td>
                <td>{contractor.get('company_name', '')}</td>
                <td>{contractor.get('contact_name', '')}</td>
                <td>{contractor.get('phone', '')}</td>
                <td>{contractor.get('email', '')}</td>
                <td>{contractor.get('services_offered', '')}</td>
                <td>{contractor.get('service_area', '')}</td>
                <td>{contractor.get('licensed_insured', '')}</td>
                <td>{contractor.get('approved', False)}</td>
                <td>{contractor.get('rejected', False)}</td>
            </tr>
            """

        html = f"""
        <html>
        <head>
            <title>LeadForge Admin</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    padding: 20px;
                    background: #f5f5f5;
                    color: #222;
                }}
                h1, h2 {{
                    margin-top: 30px;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    background: white;
                    margin-bottom: 30px;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 8px;
                    font-size: 14px;
                    vertical-align: top;
                }}
                th {{
                    background: #111;
                    color: white;
                }}
            </style>
        </head>
        <body>
            <h1>LeadForge Admin Dashboard</h1>

            <h2>Homeowner Leads</h2>
            <table>
                <tr>
                    <th>ID</th>
                    <th>Name</th>
                    <th>Phone</th>
                    <th>Email</th>
                    <th>Location</th>
                    <th>Service</th>
                    <th>Project Details</th>
                    <th>Created</th>
                </tr>
                {lead_rows}
            </table>

            <h2>Contractor Applications</h2>
            <table>
                <tr>
                    <th>ID</th>
                    <th>Company</th>
                    <th>Contact</th>
                    <th>Phone</th>
                    <th>Email</th>
                    <th>Services</th>
                    <th>Area</th>
                    <th>Licensed / Insured</th>
                    <th>Approved</th>
                    <th>Rejected</th>
                </tr>
                {contractor_rows}
            </table>
        </body>
        </html>
        """
        return html

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load admin: {str(e)}")
