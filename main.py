from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from supabase import create_client
from datetime import datetime, timezone
import stripe
import os
import html

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
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "https://leadforge-clean.vercel.app")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Missing SUPABASE_URL or SUPABASE_KEY environment variables")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY


class ContractorCreate(BaseModel):
    company_name: str
    contact_name: str
    phone: str
    email: str
    service_type: str
    city: str | None = ""
    state: str | None = ""
    zip_code: str | None = ""
    website: str | None = ""
    notes: str | None = ""


class LeadCreate(BaseModel):
    homeowner_name: str
    phone: str
    email: str
    city: str | None = ""
    state: str | None = ""
    zip_code: str | None = ""
    service: str | None = ""
    project_details: str | None = ""
    contractor_id: str | None = ""
    contractor_name: str | None = ""


class CheckoutRequest(BaseModel):
    lead_id: str


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def safe(value):
    if value is None:
        return ""
    return html.escape(str(value))


def fetch_lead_or_404(lead_id: str):
    result = (
        supabase.table("leads")
        .select("*")
        .eq("id", lead_id)
        .limit(1)
        .execute()
    )
    data = result.data or []
    if not data:
        raise HTTPException(status_code=404, detail="Lead not found")
    return data[0]


@app.get("/")
def root():
    return {"message": "API WORKING"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/contractors")
def create_contractor(contractor: ContractorCreate):
    payload = {
        "company_name": contractor.company_name,
        "contact_name": contractor.contact_name,
        "phone": contractor.phone,
        "email": contractor.email,
        "service_type": contractor.service_type,
        "city": contractor.city or "",
        "state": contractor.state or "",
        "zip_code": contractor.zip_code or "",
        "website": contractor.website or "",
        "notes": contractor.notes or "",
        "approved": False,
        "created_at": now_iso(),
    }

    result = supabase.table("contractors").insert(payload).execute()

    return {
        "success": True,
        "message": "Contractor submitted successfully",
        "data": result.data,
    }


@app.get("/contractors")
def get_contractors():
    result = (
        supabase.table("contractors")
        .select("*")
        .eq("approved", True)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []


@app.post("/contractors/approve/{contractor_id}")
def approve_contractor(contractor_id: str):
    result = (
        supabase.table("contractors")
        .update({"approved": True})
        .eq("id", contractor_id)
        .execute()
    )
    return {"success": True, "message": "Contractor approved", "data": result.data}


@app.post("/contractors/reject/{contractor_id}")
def reject_contractor(contractor_id: str):
    result = (
        supabase.table("contractors")
        .update({"approved": False})
        .eq("id", contractor_id)
        .execute()
    )
    return {"success": True, "message": "Contractor rejected", "data": result.data}


@app.post("/leads")
def create_lead(lead: LeadCreate):
    try:
        payload = {
            "homeowner_name": lead.homeowner_name,
            "phone": lead.phone,
            "email": lead.email,
            "city": lead.city or "",
            "state": lead.state or "",
            "zip_code": lead.zip_code or "",
            "service": lead.service or "",
            "project_details": lead.project_details or "",
            "contractor_id": lead.contractor_id or "",
            "contractor_name": lead.contractor_name or "",
            "created_at": now_iso(),
        }

        result = supabase.table("leads").insert(payload).execute()
        inserted = (result.data or [{}])[0]

        return {
            "success": True,
            "message": "Lead submitted successfully",
            "lead_id": inserted.get("id"),
            "data": inserted,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lead insert failed: {str(e)}")


@app.get("/leads/{lead_id}")
def get_lead(lead_id: str):
    lead = fetch_lead_or_404(lead_id)

    return {
        "id": lead.get("id"),
        "homeowner_name": lead.get("homeowner_name", ""),
        "phone": lead.get("phone", ""),
        "email": lead.get("email", ""),
        "city": lead.get("city", ""),
        "state": lead.get("state", ""),
        "zip_code": lead.get("zip_code", ""),
        "service": lead.get("service", ""),
        "project_details": lead.get("project_details", ""),
        "contractor_id": lead.get("contractor_id", ""),
        "contractor_name": lead.get("contractor_name", ""),
        "unlocked": bool(lead.get("unlocked", False)),
        "created_at": lead.get("created_at", ""),
    }


@app.post("/create-checkout-session")
def create_checkout_session(request: CheckoutRequest):
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="STRIPE_SECRET_KEY is missing on Render")

    lead = fetch_lead_or_404(request.lead_id)

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": "LeadForge Lead Unlock",
                            "description": f"Unlock access to lead {lead.get('id')}",
                        },
                        "unit_amount": 1000,
                    },
                    "quantity": 1,
                }
            ],
            metadata={
                "lead_id": str(lead.get("id", "")),
                "contractor_id": str(lead.get("contractor_id", "")),
                "contractor_name": str(lead.get("contractor_name", "")),
            },
            success_url=f"{FRONTEND_BASE_URL}/lead-detail.html?id={request.lead_id}&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{FRONTEND_BASE_URL}/unlock.html?id={request.lead_id}&canceled=1",
        )

        return {"url": session.url}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe session error: {str(e)}")


@app.get("/verify-unlock")
def verify_unlock(lead_id: str, session_id: str):
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="STRIPE_SECRET_KEY is missing on Render")

    fetch_lead_or_404(lead_id)

    try:
        session = stripe.checkout.Session.retrieve(session_id)

        if session.payment_status != "paid":
            return {"unlocked": False, "message": "Payment not completed"}

        metadata = session.metadata or {}
        if metadata.get("lead_id") != lead_id:
            raise HTTPException(status_code=400, detail="Session does not match this lead")

        try:
            (
                supabase.table("leads")
                .update({
                    "unlocked": True,
                    "stripe_session_id": session_id,
                })
                .eq("id", lead_id)
                .execute()
            )
        except Exception:
            (
                supabase.table("leads")
                .update({})
                .eq("id", lead_id)
                .execute()
            )

        return {"unlocked": True, "message": "Lead unlocked"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe verify error: {str(e)}")


@app.get("/admin", response_class=HTMLResponse)
def admin_page():
    contractors_result = (
        supabase.table("contractors")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    leads_result = (
        supabase.table("leads")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )

    contractors = contractors_result.data or []
    leads = leads_result.data or []

    contractor_rows = ""
    for c in contractors:
        approve_form = f"""
            <form method="post" action="/contractors/approve/{safe(c.get('id', ''))}" style="display:inline;">
                <button type="submit">Approve</button>
            </form>
        """
        reject_form = f"""
            <form method="post" action="/contractors/reject/{safe(c.get('id', ''))}" style="display:inline;">
                <button type="submit">Reject</button>
            </form>
        """

        contractor_rows += f"""
            <tr>
                <td>{safe(c.get('created_at'))}</td>
                <td>{safe(c.get('company_name'))}</td>
                <td>{safe(c.get('contact_name'))}</td>
                <td>{safe(c.get('phone'))}</td>
                <td>{safe(c.get('email'))}</td>
                <td>{safe(c.get('service_type'))}</td>
                <td>{safe(c.get('city'))}</td>
                <td>{safe(c.get('state'))}</td>
                <td>{safe(c.get('zip_code'))}</td>
                <td>{'Yes' if c.get('approved') else 'No'}</td>
                <td>{approve_form} {reject_form}</td>
            </tr>
        """

    lead_rows = ""
    for l in leads:
        lead_id = safe(l.get("id"))
        unlock_url = f"{FRONTEND_BASE_URL}/unlock.html?id={lead_id}"

        lead_rows += f"""
            <tr>
                <td>{safe(l.get('created_at'))}</td>
                <td>{lead_id}</td>
                <td>{safe(l.get('homeowner_name'))}</td>
                <td>{safe(l.get('phone'))}</td>
                <td>{safe(l.get('email'))}</td>
                <td>{safe(l.get('city'))}</td>
                <td>{safe(l.get('state'))}</td>
                <td>{safe(l.get('zip_code'))}</td>
                <td>{safe(l.get('service'))}</td>
                <td>{safe(l.get('project_details'))}</td>
                <td>{safe(l.get('contractor_name'))}</td>
                <td>{safe(l.get('contractor_id'))}</td>
                <td>{'Yes' if l.get('unlocked') else 'No'}</td>
                <td><a href="{unlock_url}" target="_blank">Open Unlock Page</a></td>
            </tr>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>LeadForge Admin</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <style>
            body {{
                font-family: Arial, sans-serif;
                padding: 20px;
                background: #f5f5f5;
            }}
            h1, h2 {{
                margin-bottom: 10px;
            }}
            .section {{
                background: white;
                padding: 20px;
                border-radius: 12px;
                margin-bottom: 30px;
                overflow-x: auto;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                min-width: 1200px;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
                vertical-align: top;
                font-size: 14px;
            }}
            th {{
                background: #111;
                color: white;
            }}
            button {{
                padding: 6px 10px;
                margin: 2px;
                cursor: pointer;
            }}
            a {{
                color: #0b57d0;
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <h1>LeadForge Admin</h1>

        <div class="section">
            <h2>Contractor Applications</h2>
            <table>
                <thead>
                    <tr>
                        <th>Created</th>
                        <th>Company</th>
                        <th>Contact</th>
                        <th>Phone</th>
                        <th>Email</th>
                        <th>Service</th>
                        <th>City</th>
                        <th>State</th>
                        <th>Zip</th>
                        <th>Approved</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {contractor_rows}
                </tbody>
            </table>
        </div>

        <div class="section">
            <h2>Homeowner Leads</h2>
            <table>
                <thead>
                    <tr>
                        <th>Created</th>
                        <th>Lead ID</th>
                        <th>Name</th>
                        <th>Phone</th>
                        <th>Email</th>
                        <th>City</th>
                        <th>State</th>
                        <th>Zip</th>
                        <th>Service</th>
                        <th>Project Details</th>
                        <th>Chosen Contractor</th>
                        <th>Contractor ID</th>
                        <th>Unlocked</th>
                        <th>Unlock Page</th>
                    </tr>
                </thead>
                <tbody>
                    {lead_rows}
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
