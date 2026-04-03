from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from supabase import create_client, Client
from datetime import datetime, timezone
from typing import Optional, Any, Dict
import os
import stripe

app = FastAPI(title="LeadForge API", version="1.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
FRONTEND_BASE_URL = os.getenv(
    "FRONTEND_BASE_URL",
    "https://leadforge-clean.vercel.app"
).rstrip("/")
LEAD_UNLOCK_PRICE_CENTS = int(os.getenv("LEAD_UNLOCK_PRICE_CENTS", "1000"))

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Missing SUPABASE_URL or SUPABASE_KEY environment variables")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY


# ----------------------------
# Models
# ----------------------------

class LeadCreate(BaseModel):
    name: str
    phone: str
    email: str
    city: str
    state: str
    zip_code: str
    service: str
    project_details: str


class ContractorCreate(BaseModel):
    # Old/simple frontend fields
    name: Optional[str] = ""
    business: Optional[str] = ""
    service: Optional[str] = ""
    location: Optional[str] = ""
    about: Optional[str] = ""

    # Newer/expanded fields
    company_name: Optional[str] = ""
    contact_name: Optional[str] = ""
    first_name: Optional[str] = ""
    last_name: Optional[str] = ""
    business_name: Optional[str] = ""
    trade: Optional[str] = ""
    experience_years: Optional[str] = ""
    service_area: Optional[str] = ""
    license_number: Optional[str] = ""
    licensed_insured: Optional[str] = ""
    insured: Optional[bool] = False
    notes: Optional[str] = ""
    agreed_to_terms: Optional[bool] = False
    agreement_version: Optional[str] = "v1.0"

    # Required contact fields
    phone: str
    email: str


class UnlockTestRequest(BaseModel):
    contractor_id: Optional[str] = None
    payment_reference: Optional[str] = None


class CheckoutCreateRequest(BaseModel):
    contractor_id: Optional[str] = None
    contractor_email: Optional[str] = None


# ----------------------------
# Helpers
# ----------------------------

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_stripe_configured() -> None:
    if not STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=500,
            detail="Missing STRIPE_SECRET_KEY environment variable"
        )


def clean_str(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    value = value.strip()
    return value if value else None


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
                detail="lead_unlocks table is missing in Supabase."
            )
        raise HTTPException(status_code=500, detail=f"Failed to query lead unlocks: {message}")

    data = response.data or []
    return data[0] if data else None


def build_lead_preview(lead: Dict[str, Any]) -> Dict[str, Any]:
    submitted_at = lead.get("created_at") or lead.get("submitted_at") or ""
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
        "area": lead.get("zip_code") or "",
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


def create_unlock_record_if_missing(
    lead_id: str,
    contractor_id: Optional[str],
    payment_reference: str,
) -> Dict[str, Any]:
    existing_unlock = get_unlock_record(lead_id)
    if existing_unlock:
        return existing_unlock

    insert_payload = {
        "lead_id": lead_id,
        "contractor_id": contractor_id,
        "status": "paid",
        "payment_reference": payment_reference,
    }

    try:
        response = supabase.table("lead_unlocks").insert(insert_payload).execute()
        unlock_row = response.data[0] if response.data else None
        if not unlock_row:
            raise HTTPException(
                status_code=500,
                detail="Unlock record was not returned after insert"
            )
        return unlock_row
    except HTTPException:
        raise
    except Exception as e:
        message = str(e)
        if "lead_unlocks" in message.lower() or "relation" in message.lower():
            raise HTTPException(
                status_code=500,
                detail="lead_unlocks table is missing in Supabase."
            )
        raise HTTPException(status_code=500, detail=f"Failed to create unlock record: {message}")


def fulfill_checkout_session(session: Any) -> Dict[str, Any]:
    metadata = session.get("metadata") or {}
    lead_id = metadata.get("lead_id")
    contractor_id = metadata.get("contractor_id")
    payment_status = session.get("payment_status")
    session_id = session.get("id")

    if not lead_id:
        raise HTTPException(
            status_code=400,
            detail="Checkout session missing lead_id metadata"
        )

    get_lead_by_id(lead_id)

    if payment_status != "paid":
        raise HTTPException(status_code=400, detail="Checkout session is not paid")

    unlock_row = create_unlock_record_if_missing(
        lead_id=lead_id,
        contractor_id=contractor_id,
        payment_reference=session_id or f"stripe-session-{lead_id}",
    )

    return unlock_row


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
    lead = get_lead_by_id(lead_id)

    existing_unlock = get_unlock_record(lead_id)
    if existing_unlock:
        return {
            "success": True,
            "message": "Lead already unlocked",
            "lead_id": lead.get("id"),
            "unlock": existing_unlock,
        }

    unlock_row = create_unlock_record_if_missing(
        lead_id=lead_id,
        contractor_id=payload.contractor_id,
        payment_reference=payload.payment_reference or f"manual-test-{lead_id}",
    )

    return {
        "success": True,
        "message": "Lead unlocked for testing",
        "lead_id": lead.get("id"),
        "unlock": unlock_row,
    }


@app.post("/leads/{lead_id}/create-checkout-session")
def create_checkout_session(lead_id: str, payload: CheckoutCreateRequest):
    ensure_stripe_configured()
    lead = get_lead_by_id(lead_id)

    existing_unlock = get_unlock_record(lead_id)
    if existing_unlock:
        return {
            "success": True,
            "already_unlocked": True,
            "checkout_url": f"{FRONTEND_BASE_URL}/lead-unlock.html?lead_id={lead_id}",
            "lead_id": lead_id,
        }

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            success_url=f"{FRONTEND_BASE_URL}/lead-unlock.html?lead_id={lead_id}&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{FRONTEND_BASE_URL}/lead-unlock.html?lead_id={lead_id}&canceled=1",
            client_reference_id=lead_id,
            customer_email=payload.contractor_email or None,
            metadata={
                "lead_id": lead_id,
                "contractor_id": payload.contractor_id or "",
            },
            line_items=[
                {
                    "quantity": 1,
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": LEAD_UNLOCK_PRICE_CENTS,
                        "product_data": {
                            "name": "Lead Unlock",
                            "description": f"Unlock lead for {lead.get('service') or 'project'} in {lead.get('zip_code') or ''}",
                        },
                    },
                }
            ],
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create Stripe checkout session: {str(e)}"
        )

    return {
        "success": True,
        "checkout_url": session.url,
        "session_id": session.id,
        "lead_id": lead_id,
    }


@app.get("/payments/verify-session/{session_id}")
def verify_checkout_session(session_id: str):
    ensure_stripe_configured()

    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve Stripe checkout session: {str(e)}"
        )

    unlock_row = None
    if session.get("payment_status") == "paid":
        unlock_row = fulfill_checkout_session(session)

    return {
        "success": True,
        "session_id": session.get("id"),
        "payment_status": session.get("payment_status"),
        "status": "paid" if unlock_row else "unpaid",
        "lead_id": (session.get("metadata") or {}).get("lead_id"),
        "unlocked": unlock_row is not None,
    }


@app.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    ensure_stripe_configured()

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Missing STRIPE_WEBHOOK_SECRET environment variable"
        )

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=STRIPE_WEBHOOK_SECRET,
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid webhook payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        fulfill_checkout_session(session)

    return {"received": True}


# ----------------------------
# Contractors
# ----------------------------

@app.post("/contractors")
def create_contractor(contractor: ContractorCreate):
    """
    Accepts both the older simple contractor form and the newer expanded form.
    Inserts a simpler contractor payload to maximize compatibility with the
    existing Supabase contractors table.
    """

    contact_name = (
        clean_str(contractor.name)
        or clean_str(contractor.contact_name)
        or "Unknown Contact"
    )

    business_name = (
        clean_str(contractor.business)
        or clean_str(contractor.business_name)
        or clean_str(contractor.company_name)
        or "Unknown Business"
    )

    trade = (
        clean_str(contractor.service)
        or clean_str(contractor.trade)
        or "General"
    )

    service_area = (
        clean_str(contractor.location)
        or clean_str(contractor.service_area)
        or ""
    )

    notes = (
        clean_str(contractor.about)
        or clean_str(contractor.notes)
        or ""
    )

    payload = {
        "contact_name": contact_name,
        "business_name": business_name,
        "trade": trade,
        "service_area": service_area,
        "phone": contractor.phone.strip(),
        "email": contractor.email.strip(),
        "notes": notes,
        "approved": False,
        "rejected": False,
        "status": "pending",
        "verified": False,
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
            .update({"approved": True, "rejected": False, "status": "approved"})
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
            .update({"approved": False, "rejected": True, "status": "rejected"})
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
            display_business = (
                contractor.get("business_name")
                or contractor.get("company_name")
                or contractor.get("business")
                or ""
            )
            display_contact = (
                contractor.get("contact_name")
                or contractor.get("name")
                or f"{contractor.get('first_name', '')} {contractor.get('last_name', '')}".strip()
            )
            display_trade = (
                contractor.get("trade")
                or contractor.get("service")
                or contractor.get("services_offered")
                or ""
            )
            display_area = (
                contractor.get("service_area")
                or contractor.get("location")
                or ""
            )
            display_license = (
                contractor.get("license_number")
                or contractor.get("licensed_insured")
                or ""
            )

            contractor_rows += f"""
            <tr>
                <td>{contractor.get('id', '')}</td>
                <td>{display_business}</td>
                <td>{display_contact}</td>
                <td>{contractor.get('phone', '')}</td>
                <td>{contractor.get('email', '')}</td>
                <td>{display_trade}</td>
                <td>{display_area}</td>
                <td>{display_license}</td>
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
                    <th>Business</th>
                    <th>Contact</th>
                    <th>Phone</th>
                    <th>Email</th>
                    <th>Trade</th>
                    <th>Area</th>
                    <th>License / Insured</th>
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
