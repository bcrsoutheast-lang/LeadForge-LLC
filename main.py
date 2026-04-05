from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from supabase import create_client
from datetime import datetime, timezone
import stripe
import os
import html
import json

app = FastAPI()
templates = Jinja2Templates(directory="templates")

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
LEAD_UNLOCK_PRICE = os.getenv("LEAD_UNLOCK_PRICE", "1000")
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "https://leadforge-llc.onrender.com")
FRONTEND_BASE_URL = os.getenv(
    "FRONTEND_BASE_URL",
    "https://lead-forge-frontend-git-main-bcrsoutheast-langs-projects.vercel.app",
)

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
    contractor_id: str | None = None
    contractor_name: str | None = ""


class CheckoutRequest(BaseModel):
    lead_id: str


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def safe(value):
    if value is None:
        return ""
    return html.escape(str(value))


def js_string(value):
    return json.dumps("" if value is None else str(value))


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


def fetch_contractor_or_404(contractor_id: str):
    result = (
        supabase.table("contractors")
        .select("*")
        .eq("id", contractor_id)
        .limit(1)
        .execute()
    )
    data = result.data or []
    if not data:
        raise HTTPException(status_code=404, detail="Contractor not found")
    return data[0]


def get_stripe_metadata_value(metadata, key: str) -> str:
    if metadata is None:
        return ""

    if isinstance(metadata, dict):
        return str(metadata.get(key, "") or "")

    try:
        value = metadata[key]
        return str(value or "")
    except Exception:
        pass

    try:
        value = getattr(metadata, key, "")
        return str(value or "")
    except Exception:
        return ""


def verify_session_and_unlock(lead_id: str, session_id: str):
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="STRIPE_SECRET_KEY is missing on Render")

    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not retrieve Stripe session: {str(e)}")

    payment_status = getattr(session, "payment_status", "")
    if payment_status != "paid":
        return {"unlocked": False, "message": "Payment not completed"}

    metadata = getattr(session, "metadata", None)
    session_lead_id = get_stripe_metadata_value(metadata, "lead_id")

    if session_lead_id != str(lead_id):
        raise HTTPException(status_code=400, detail="Session does not match this lead")

    supabase.table("leads").update(
        {
            "unlocked": True,
            "stripe_session_id": session_id,
        }
    ).eq("id", lead_id).execute()

    return {"unlocked": True, "message": "Lead unlocked"}


@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/contractor-signup", response_class=HTMLResponse)
def contractor_signup_page():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <title>Join LeadForge</title>
      <style>
        body {
          font-family: Arial, sans-serif;
          background: #f7f7f7;
          margin: 0;
          padding: 20px;
          color: #111;
        }

        .container {
          max-width: 640px;
          margin: 20px auto;
          background: #fff;
          padding: 24px;
          border-radius: 14px;
          box-shadow: 0 4px 18px rgba(0,0,0,0.08);
        }

        h1 {
          margin-top: 0;
          font-size: 32px;
        }

        p {
          color: #555;
          line-height: 1.5;
        }

        label {
          display: block;
          font-weight: 700;
          margin-top: 12px;
          margin-bottom: 6px;
        }

        input, select, textarea {
          width: 100%;
          padding: 12px;
          border-radius: 10px;
          border: 1px solid #ddd;
          font-size: 16px;
          box-sizing: border-box;
          margin-bottom: 6px;
          background: #fff;
        }

        button {
          width: 100%;
          padding: 14px;
          background: #111;
          color: white;
          border: none;
          border-radius: 10px;
          font-size: 16px;
          font-weight: bold;
          cursor: pointer;
          margin-top: 18px;
        }

        button:disabled {
          opacity: 0.65;
          cursor: not-allowed;
        }

        .success {
          background: #e8f7ec;
          color: #166534;
          padding: 12px;
          border-radius: 8px;
          margin-top: 15px;
          border: 1px solid #b7e4c7;
        }

        .error {
          background: #fdecec;
          color: #991b1b;
          padding: 12px;
          border-radius: 8px;
          margin-top: 15px;
          border: 1px solid #f5b5b5;
        }

        .hint {
          font-size: 13px;
          color: #666;
          margin-bottom: 8px;
        }

        .top-link {
          display: inline-block;
          margin-top: 14px;
          color: #0b57d0;
          text-decoration: none;
          font-weight: 600;
        }
      </style>
    </head>
    <body>
      <div class="container">
        <h1>Join LeadForge</h1>
        <p>Get exclusive homeowner requests in your area. Only pay when you choose to unlock a job.</p>

        <div id="message"></div>

        <form id="contractorForm" novalidate>
          <label for="company">Company Name</label>
          <input type="text" id="company" placeholder="ABC Roofing" />

          <label for="name">Contact Name</label>
          <input type="text" id="name" placeholder="John Smith" />

          <label for="phone">Phone</label>
          <input type="tel" id="phone" placeholder="2055551234" inputmode="tel" />

          <label for="email">Email</label>
          <input type="email" id="email" placeholder="name@company.com" inputmode="email" />

          <label for="service">Service Type</label>
          <select id="service">
            <option value="">Select Service</option>
            <option value="Roofing">Roofing</option>
            <option value="HVAC">HVAC</option>
            <option value="Plumbing">Plumbing</option>
            <option value="Landscaping">Landscaping</option>
            <option value="General Contractor">General Contractor</option>
          </select>

          <label for="city">City</label>
          <input type="text" id="city" placeholder="Birmingham" />

          <label for="state">State</label>
          <input type="text" id="state" placeholder="AL" maxlength="2" />

          <label for="zip">Zip Code</label>
          <input type="text" id="zip" placeholder="35203" inputmode="numeric" />

          <div class="hint">Fill the main fields, then submit your application.</div>

          <button type="submit" id="submitBtn">Apply Now</button>
        </form>

        <a class="top-link" href="/admin">Admin</a>
      </div>

      <script>
        const form = document.getElementById("contractorForm");
        const message = document.getElementById("message");
        const submitBtn = document.getElementById("submitBtn");

        function showMessage(type, text) {
          message.innerHTML = `<div class="${type}">${text}</div>`;
          window.scrollTo({ top: 0, behavior: "smooth" });
        }

        function clean(value) {
          return (value || "").trim();
        }

        form.addEventListener("submit", async function (e) {
          e.preventDefault();
          message.innerHTML = "";

          const payload = {
            company_name: clean(document.getElementById("company").value),
            contact_name: clean(document.getElementById("name").value),
            phone: clean(document.getElementById("phone").value),
            email: clean(document.getElementById("email").value),
            service_type: clean(document.getElementById("service").value),
            city: clean(document.getElementById("city").value),
            state: clean(document.getElementById("state").value).toUpperCase(),
            zip_code: clean(document.getElementById("zip").value),
            website: "",
            notes: ""
          };

          if (!payload.company_name) {
            showMessage("error", "Enter company name.");
            return;
          }

          if (!payload.contact_name) {
            showMessage("error", "Enter contact name.");
            return;
          }

          if (!payload.phone) {
            showMessage("error", "Enter phone number.");
            return;
          }

          if (!payload.email) {
            showMessage("error", "Enter email.");
            return;
          }

          if (!payload.service_type) {
            showMessage("error", "Choose a service type.");
            return;
          }

          submitBtn.disabled = true;
          submitBtn.textContent = "Submitting...";

          try {
            const res = await fetch("/contractors", {
              method: "POST",
              headers: {
                "Content-Type": "application/json"
              },
              body: JSON.stringify(payload)
            });

            const raw = await res.text();
            let data = {};

            try {
              data = raw ? JSON.parse(raw) : {};
            } catch (parseError) {
              throw new Error(`Unexpected response: ${raw || "empty response"}`);
            }

            if (!res.ok) {
              throw new Error(data.detail || data.message || "Error submitting contractor application.");
            }

            showMessage("success", "Application submitted! We'll review and approve you shortly.");
            form.reset();
          } catch (err) {
            showMessage("error", err.message || "Could not submit application.");
          } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = "Apply Now";
          }
        });
      </script>
    </body>
    </html>
    """


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
    fetch_contractor_or_404(contractor_id)
    supabase.table("contractors").update({"approved": True}).eq("id", contractor_id).execute()
    return RedirectResponse(url="/admin", status_code=303)


@app.post("/contractors/reject/{contractor_id}")
def reject_contractor(contractor_id: str):
    fetch_contractor_or_404(contractor_id)
    supabase.table("contractors").update({"approved": False}).eq("id", contractor_id).execute()
    return RedirectResponse(url="/admin", status_code=303)


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
            "contractor_id": lead.contractor_id if lead.contractor_id else None,
            "contractor_name": lead.contractor_name or "",
            "unlocked": False,
            "stripe_session_id": "",
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

    if bool(lead.get("unlocked", False)):
        return {"url": f"{BACKEND_BASE_URL}/lead-detail/{request.lead_id}"}

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
                        "unit_amount": int(LEAD_UNLOCK_PRICE),
                    },
                    "quantity": 1,
                }
            ],
            metadata={
                "lead_id": str(lead.get("id", "")),
                "contractor_id": str(lead.get("contractor_id", "") or ""),
                "contractor_name": str(lead.get("contractor_name", "") or ""),
            },
            success_url=f"{BACKEND_BASE_URL}/lead-detail/{request.lead_id}?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{BACKEND_BASE_URL}/unlock/{request.lead_id}?canceled=1",
        )

        return {"url": session.url}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe session error: {str(e)}")


@app.get("/verify-unlock")
def verify_unlock(lead_id: str, session_id: str):
    try:
        result = verify_session_and_unlock(lead_id, session_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe verify error: {str(e)}")


@app.get("/unlock/{lead_id}", response_class=HTMLResponse)
def unlock_page(lead_id: str, canceled: int | None = None):
    lead = fetch_lead_or_404(lead_id)

    location = ", ".join(
        [part for part in [lead.get("city"), lead.get("state"), lead.get("zip_code")] if part]
    ) or "Not provided"

    already_unlocked = bool(lead.get("unlocked", False))

    status_html = ""
    button_label = "Unlock for $10"

    if canceled == 1:
        status_html = """
        <div class="status error">
            Checkout canceled. You can try again whenever you're ready.
        </div>
        """

    if already_unlocked:
        status_html = """
        <div class="status success">
            This lead is already unlocked.
        </div>
        """
        button_label = "View Full Lead Details"

    action_html = (
        f"<a class='link-btn' href='/lead-detail/{safe(lead_id)}'>View Full Lead Details</a>"
        if already_unlocked
        else f"<button id='unlockBtn'>{button_label}</button>"
    )

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Unlock Lead | LeadForge</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <style>
            body {{
                font-family: Arial, sans-serif;
                background: #f7f7f7;
                margin: 0;
                padding: 20px;
                color: #111;
            }}
            .wrap {{
                max-width: 760px;
                margin: 20px auto;
                background: #fff;
                padding: 24px;
                border-radius: 14px;
                box-shadow: 0 4px 18px rgba(0,0,0,0.08);
            }}
            h1 {{
                margin-top: 0;
                font-size: 30px;
            }}
            p {{
                color: #555;
                line-height: 1.5;
            }}
            .card {{
                background: #fafafa;
                border: 1px solid #e5e5e5;
                border-radius: 12px;
                padding: 18px;
                margin-top: 18px;
            }}
            .row {{
                margin-bottom: 14px;
            }}
            .label {{
                display: block;
                font-size: 13px;
                font-weight: 700;
                color: #666;
                margin-bottom: 4px;
                text-transform: uppercase;
                letter-spacing: 0.04em;
            }}
            .value {{
                font-size: 16px;
                word-break: break-word;
            }}
            .hidden-value {{
                color: #999;
                font-style: italic;
            }}
            .price-box {{
                margin-top: 18px;
                background: #111;
                color: #fff;
                border-radius: 12px;
                padding: 18px;
            }}
            .price {{
                font-size: 34px;
                font-weight: 800;
                margin: 6px 0 2px;
            }}
            .small {{
                font-size: 14px;
                color: #d6d6d6;
            }}
            .status {{
                margin-top: 18px;
                padding: 12px;
                border-radius: 10px;
                font-weight: 600;
            }}
            .status.error {{
                background: #fdecec;
                color: #991b1b;
                border: 1px solid #f5b5b5;
            }}
            .status.success {{
                background: #e8f7ec;
                color: #166534;
                border: 1px solid #b7e4c7;
            }}
            button, .link-btn {{
                display: inline-block;
                width: 100%;
                margin-top: 22px;
                padding: 15px;
                border: none;
                border-radius: 10px;
                background: #111;
                color: #fff;
                font-size: 16px;
                font-weight: 700;
                cursor: pointer;
                text-align: center;
                text-decoration: none;
                box-sizing: border-box;
            }}
            button:disabled {{
                opacity: 0.65;
                cursor: not-allowed;
            }}
            .back-link {{
                display: inline-block;
                margin-top: 18px;
                color: #0b57d0;
                text-decoration: none;
                font-weight: 600;
            }}
        </style>
    </head>
    <body>
        <div class="wrap">
            <h1>Unlock This Lead</h1>
            <p>
                Review the opportunity below. To view the homeowner's full contact details,
                unlock this lead for a one-time access fee.
            </p>

            {status_html}

            <div class="card">
                <div class="row">
                    <span class="label">Chosen Contractor</span>
                    <div class="value">{safe(lead.get("contractor_name") or "Not assigned")}</div>
                </div>

                <div class="row">
                    <span class="label">Service Needed</span>
                    <div class="value">{safe(lead.get("service") or "Not provided")}</div>
                </div>

                <div class="row">
                    <span class="label">Project Details</span>
                    <div class="value">{safe(lead.get("project_details") or "Not provided")}</div>
                </div>

                <div class="row">
                    <span class="label">Location</span>
                    <div class="value">{safe(location)}</div>
                </div>

                <div class="row">
                    <span class="label">Homeowner Name</span>
                    <div class="value hidden-value">Hidden until unlocked</div>
                </div>

                <div class="row">
                    <span class="label">Phone</span>
                    <div class="value hidden-value">Hidden until unlocked</div>
                </div>

                <div class="row">
                    <span class="label">Email</span>
                    <div class="value hidden-value">Hidden until unlocked</div>
                </div>
            </div>

            <div class="price-box">
                <div>Lead Access</div>
                <div class="price">$10</div>
                <div class="small">One-time unlock to view full homeowner details.</div>
            </div>

            {action_html}

            <a class="back-link" href="/admin">Back to Admin</a>
        </div>

        <script>
            const leadId = {js_string(lead_id)};
            const unlockBtn = document.getElementById("unlockBtn");

            if (unlockBtn) {{
                unlockBtn.addEventListener("click", async function () {{
                    try {{
                        unlockBtn.disabled = true;
                        unlockBtn.textContent = "Redirecting...";

                        const response = await fetch("/create-checkout-session", {{
                            method: "POST",
                            headers: {{
                                "Content-Type": "application/json"
                            }},
                            body: JSON.stringify({{ lead_id: leadId }})
                        }});

                        const result = await response.json();

                        if (!response.ok) {{
                            throw new Error(result.detail || "Could not start checkout");
                        }}

                        if (!result.url) {{
                            throw new Error("No checkout URL returned");
                        }}

                        window.location.href = result.url;
                    }} catch (error) {{
                        alert(error.message || "Could not start checkout");
                        unlockBtn.disabled = false;
                        unlockBtn.textContent = "Unlock for $10";
                    }}
                }});
            }}
        </script>
    </body>
    </html>
    """


@app.get("/lead-detail/{lead_id}", response_class=HTMLResponse)
def lead_detail_page(lead_id: str, session_id: str | None = None):
    status_html = ""

    try:
        if session_id:
            result = verify_session_and_unlock(lead_id, session_id)
            if result.get("unlocked"):
                status_html = """
                <div class="status success">
                    Payment verified. Lead unlocked successfully.
                </div>
                """
    except HTTPException as e:
        status_html = f"""
        <div class="status error">
            {safe(e.detail)}
        </div>
        """
    except Exception as e:
        status_html = f"""
        <div class="status error">
            {safe(str(e))}
        </div>
        """

    lead = fetch_lead_or_404(lead_id)
    unlocked = bool(lead.get("unlocked", False))

    if not unlocked and not session_id:
        status_html = """
        <div class="status error">
            This lead has not been unlocked yet.
        </div>
        """

    location = ", ".join(
        [part for part in [lead.get("city"), lead.get("state"), lead.get("zip_code")] if part]
    ) or "Not provided"

    def visible(value):
        return safe(value if unlocked else "-")

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Lead Details | LeadForge</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <style>
            body {{
                font-family: Arial, sans-serif;
                background: #f7f7f7;
                margin: 0;
                padding: 20px;
                color: #111;
            }}
            .wrap {{
                max-width: 760px;
                margin: 20px auto;
                background: #fff;
                padding: 24px;
                border-radius: 14px;
                box-shadow: 0 4px 18px rgba(0,0,0,0.08);
            }}
            h1 {{
                margin-top: 0;
                font-size: 30px;
            }}
            p {{
                color: #555;
                line-height: 1.5;
            }}
            .card {{
                background: #fafafa;
                border: 1px solid #e5e5e5;
                border-radius: 12px;
                padding: 18px;
                margin-top: 18px;
            }}
            .row {{
                margin-bottom: 14px;
            }}
            .label {{
                display: block;
                font-size: 13px;
                font-weight: 700;
                color: #666;
                margin-bottom: 4px;
                text-transform: uppercase;
                letter-spacing: 0.04em;
            }}
            .value {{
                font-size: 16px;
                word-break: break-word;
            }}
            .status {{
                margin-top: 18px;
                padding: 12px;
                border-radius: 10px;
                font-weight: 600;
            }}
            .status.error {{
                background: #fdecec;
                color: #991b1b;
                border: 1px solid #f5b5b5;
            }}
            .status.success {{
                background: #e8f7ec;
                color: #166534;
                border: 1px solid #b7e4c7;
            }}
            .back-link {{
                display: inline-block;
                margin-top: 18px;
                color: #0b57d0;
                text-decoration: none;
                font-weight: 600;
            }}
            .lock-link {{
                display: inline-block;
                margin-top: 18px;
                margin-left: 12px;
                color: #0b57d0;
                text-decoration: none;
                font-weight: 600;
            }}
        </style>
    </head>
    <body>
        <div class="wrap">
            <h1>Lead Details</h1>
            <p>
                This page shows the full homeowner information after payment is verified.
            </p>

            {status_html}

            <div class="card">
                <div class="row">
                    <span class="label">Homeowner Name</span>
                    <div class="value">{visible(lead.get("homeowner_name"))}</div>
                </div>

                <div class="row">
                    <span class="label">Phone</span>
                    <div class="value">{visible(lead.get("phone"))}</div>
                </div>

                <div class="row">
                    <span class="label">Email</span>
                    <div class="value">{visible(lead.get("email"))}</div>
                </div>

                <div class="row">
                    <span class="label">Location</span>
                    <div class="value">{visible(location)}</div>
                </div>

                <div class="row">
                    <span class="label">Service Needed</span>
                    <div class="value">{visible(lead.get("service"))}</div>
                </div>

                <div class="row">
                    <span class="label">Project Details</span>
                    <div class="value">{visible(lead.get("project_details"))}</div>
                </div>

                <div class="row">
                    <span class="label">Chosen Contractor</span>
                    <div class="value">{visible(lead.get("contractor_name"))}</div>
                </div>

                <div class="row">
                    <span class="label">Unlocked</span>
                    <div class="value">{"Yes" if unlocked else "No"}</div>
                </div>
            </div>

            <a class="back-link" href="/admin">Back to Admin</a>
            <a class="lock-link" href="/unlock/{safe(lead_id)}">Back to Unlock Page</a>
        </div>
    </body>
    </html>
    """


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
                <td>{"Yes" if c.get('approved') else "No"}</td>
                <td>{approve_form} {reject_form}</td>
            </tr>
        """

    lead_rows = ""
    for l in leads:
        lead_id = safe(l.get("id"))
        unlock_url = f"{BACKEND_BASE_URL}/unlock/{lead_id}"
        detail_url = f"{BACKEND_BASE_URL}/lead-detail/{lead_id}"

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
                <td>{"Yes" if l.get('unlocked') else "No"}</td>
                <td>
                    <a href="{unlock_url}" target="_blank">Open Unlock Page</a><br/>
                    <a href="{detail_url}" target="_blank">Open Lead Details</a>
                </td>
            </tr>
        """

    if not contractor_rows:
        contractor_rows = """
            <tr>
                <td colspan="11">No contractors found.</td>
            </tr>
        """

    if not lead_rows:
        lead_rows = """
            <tr>
                <td colspan="14">No leads found.</td>
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
                        <th>Lead Actions</th>
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
