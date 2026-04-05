from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client
import os

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

supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def safe_text(value, fallback=""):
    if value is None:
        return fallback
    return str(value)


@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>LeadForge</title>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #f4f4f4;
                margin: 0;
                padding: 0;
            }
            .wrap {
                max-width: 900px;
                margin: 80px auto;
                background: white;
                padding: 40px 24px;
                border-radius: 14px;
                box-shadow: 0 8px 30px rgba(0,0,0,0.08);
                text-align: center;
            }
            h1 {
                margin-top: 0;
                color: #111;
            }
            p {
                color: #555;
                font-size: 18px;
                line-height: 1.5;
            }
            .buttons {
                margin-top: 28px;
                display: flex;
                gap: 14px;
                justify-content: center;
                flex-wrap: wrap;
            }
            a.button {
                display: inline-block;
                padding: 14px 22px;
                border-radius: 10px;
                background: #111;
                color: white;
                text-decoration: none;
                font-weight: bold;
            }
            a.button:hover {
                opacity: 0.92;
            }
        </style>
    </head>
    <body>
        <div class="wrap">
            <h1>LeadForge</h1>
            <p>Browse approved contractors and submit an exclusive homeowner request.</p>

            <div class="buttons">
                <a class="button" href="/contractors">Browse Contractors</a>
                <a class="button" href="/contractor-signup">Join as a Contractor</a>
                <a class="button" href="/admin">Admin</a>
                <a class="button" href="/health">Health Check</a>
            </div>
        </div>
    </body>
    </html>
    """


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/contractors", response_class=HTMLResponse)
def contractors():
    contractor_cards = ""

    if supabase:
        try:
            contractors = (
                supabase.table("contractors")
                .select("*")
                .eq("approved", True)
                .execute()
                .data
            )
        except Exception:
            contractors = []
    else:
        contractors = []

    if contractors:
        for c in contractors:
            contractor_id = safe_text(c.get("id"))
            business_name = safe_text(c.get("business_name"), "Contractor")
            service = safe_text(c.get("service"))
            city = safe_text(c.get("city"))
            state = safe_text(c.get("state"))

            location = city
            if state:
                location = f"{city}, {state}" if city else state

            contractor_cards += f"""
            <div class="card">
                <h2>{business_name}</h2>
                <p><strong>Service:</strong> {service}</p>
                <p><strong>Location:</strong> {location}</p>
                <div class="actions">
                    <a class="btn" href="/request/{contractor_id}">Request Quote</a>
                    <a class="btn secondary" href="/contractor/{contractor_id}">Contractor Lead View</a>
                </div>
            </div>
            """
    else:
        contractor_cards = "<p class='empty'>No approved contractors yet.</p>"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Browse Contractors</title>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <style>
            body {{
                font-family: Arial, sans-serif;
                background: #f4f4f4;
                margin: 0;
                padding: 0;
            }}
            .wrap {{
                max-width: 1100px;
                margin: 40px auto;
                padding: 0 20px 40px;
            }}
            .header {{
                text-align: center;
                margin-bottom: 24px;
            }}
            .header h1 {{
                color: #111;
                margin-bottom: 8px;
            }}
            .header p {{
                color: #555;
                margin: 0;
            }}
            .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
                gap: 20px;
            }}
            .card {{
                background: white;
                border-radius: 14px;
                padding: 22px;
                box-shadow: 0 6px 20px rgba(0,0,0,0.08);
            }}
            .card h2 {{
                margin-top: 0;
                color: #111;
            }}
            .card p {{
                color: #444;
                margin: 8px 0;
            }}
            .actions {{
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
                margin-top: 14px;
            }}
            .btn {{
                display: inline-block;
                padding: 12px 16px;
                border-radius: 10px;
                background: #111;
                color: white;
                text-decoration: none;
                font-weight: bold;
            }}
            .btn.secondary {{
                background: #666;
            }}
            .empty {{
                text-align: center;
                background: white;
                padding: 24px;
                border-radius: 14px;
                box-shadow: 0 6px 20px rgba(0,0,0,0.08);
            }}
            .back {{
                text-align: center;
                margin-top: 26px;
            }}
            .back a {{
                display: inline-block;
                padding: 12px 18px;
                background: #111;
                color: white;
                text-decoration: none;
                border-radius: 10px;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <div class="wrap">
            <div class="header">
                <h1>Browse Contractors</h1>
                <p>Select a contractor to send an exclusive homeowner request.</p>
            </div>

            <div class="grid">
                {contractor_cards}
            </div>

            <div class="back">
                <a href="/">Back Home</a>
            </div>
        </div>
    </body>
    </html>
    """


@app.get("/contractor-signup", response_class=HTMLResponse)
def contractor_signup():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Contractor Signup</title>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #f4f4f4;
                margin: 0;
                padding: 0;
            }
            .wrap {
                max-width: 760px;
                margin: 40px auto;
                background: white;
                padding: 32px 24px;
                border-radius: 14px;
                box-shadow: 0 8px 30px rgba(0,0,0,0.08);
            }
            h1 {
                margin-top: 0;
                text-align: center;
                color: #111;
            }
            .sub {
                text-align: center;
                color: #555;
                margin-bottom: 26px;
            }
            form {
                display: grid;
                gap: 16px;
            }
            label {
                font-weight: bold;
                color: #222;
                display: block;
                margin-bottom: 6px;
            }
            input, select, textarea {
                width: 100%;
                padding: 12px;
                border: 1px solid #d5d5d5;
                border-radius: 10px;
                font-size: 16px;
                box-sizing: border-box;
            }
            textarea {
                min-height: 110px;
                resize: vertical;
            }
            .checkbox-wrap {
                background: #fafafa;
                border: 1px solid #e6e6e6;
                border-radius: 12px;
                padding: 16px;
            }
            .checkbox-row {
                display: flex;
                align-items: flex-start;
                gap: 12px;
            }
            .checkbox-row input[type="checkbox"] {
                width: 20px;
                height: 20px;
                margin-top: 2px;
                flex-shrink: 0;
            }
            .checkbox-row label {
                margin: 0;
                font-weight: normal;
                color: #444;
                line-height: 1.5;
            }
            .checkbox-row strong {
                color: #111;
            }
            .btn {
                margin-top: 8px;
                border: none;
                background: #111;
                color: white;
                padding: 14px 18px;
                border-radius: 10px;
                font-size: 16px;
                font-weight: bold;
                cursor: pointer;
            }
            .note {
                margin-top: 18px;
                padding: 14px;
                background: #f8f8f8;
                border: 1px solid #ececec;
                border-radius: 10px;
                color: #555;
                font-size: 14px;
                line-height: 1.5;
            }
            .back {
                text-align: center;
                margin-top: 24px;
            }
            .back a {
                display: inline-block;
                padding: 12px 18px;
                background: #111;
                color: white;
                text-decoration: none;
                border-radius: 10px;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="wrap">
            <h1>Join LeadForge</h1>
            <p class="sub">Contractor signup form is visible. Submit wiring can be reconnected next.</p>

            <form>
                <div>
                    <label for="business_name">Business Name</label>
                    <input type="text" id="business_name" name="business_name" placeholder="Your business name" />
                </div>

                <div>
                    <label for="contact_name">Contact Name</label>
                    <input type="text" id="contact_name" name="contact_name" placeholder="Your full name" />
                </div>

                <div>
                    <label for="email">Email</label>
                    <input type="email" id="email" name="email" placeholder="you@example.com" />
                </div>

                <div>
                    <label for="phone">Phone</label>
                    <input type="text" id="phone" name="phone" placeholder="Your phone number" />
                </div>

                <div>
                    <label for="service">Primary Service</label>
                    <select id="service" name="service">
                        <option value="">Select a service</option>
                        <option>Roofing</option>
                        <option>Pressure Washing</option>
                        <option>Landscaping</option>
                        <option>Painting</option>
                        <option>Plumbing</option>
                        <option>Electrical</option>
                        <option>HVAC</option>
                        <option>Remodeling</option>
                    </select>
                </div>

                <div>
                    <label for="city">City</label>
                    <input type="text" id="city" name="city" placeholder="Your city" />
                </div>

                <div>
                    <label for="state">State</label>
                    <input type="text" id="state" name="state" placeholder="Your state" />
                </div>

                <div>
                    <label for="bio">Business Description</label>
                    <textarea id="bio" name="bio" placeholder="Tell homeowners about your company and services"></textarea>
                </div>

                <div class="checkbox-wrap">
                    <div class="checkbox-row">
                        <input type="checkbox" id="disclaimer" name="disclaimer" />
                        <label for="disclaimer">
                            <strong>Contractor Agreement:</strong> I understand that submitting this application does not guarantee approval. I agree that LeadForge may review my business information before listing my company, and I confirm that the information I provide is accurate to the best of my knowledge.
                        </label>
                    </div>
                </div>

                <button type="button" class="btn">Submit Application</button>
            </form>

            <div class="note">
                Contractor signup is still not writing to the database in this version. We kept that safe while restoring homeowner lead submission first.
            </div>

            <div class="back">
                <a href="/">Back Home</a>
            </div>
        </div>
    </body>
    </html>
    """


@app.get("/request/{contractor_id}", response_class=HTMLResponse)
def request_page(contractor_id: str):
    contractor_name = "Contractor"
    contractor_service = ""

    if supabase:
        try:
            result = (
                supabase.table("contractors")
                .select("*")
                .eq("id", contractor_id)
                .execute()
                .data
            )
            if result:
                contractor_name = safe_text(result[0].get("business_name"), "Contractor")
                contractor_service = safe_text(result[0].get("service"))
        except Exception:
            pass

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Request Service</title>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <style>
            body {{
                font-family: Arial, sans-serif;
                background: #f4f4f4;
                margin: 0;
                padding: 0;
            }}
            .wrap {{
                max-width: 760px;
                margin: 40px auto;
                background: white;
                padding: 32px 24px;
                border-radius: 14px;
                box-shadow: 0 8px 30px rgba(0,0,0,0.08);
            }}
            h1 {{
                margin-top: 0;
                color: #111;
            }}
            h2 {{
                color: #333;
                margin-top: 0;
            }}
            .sub {{
                color: #555;
                margin-bottom: 24px;
            }}
            form {{
                display: grid;
                gap: 16px;
            }}
            label {{
                font-weight: bold;
                color: #222;
                display: block;
                margin-bottom: 6px;
            }}
            input, textarea {{
                width: 100%;
                padding: 12px;
                border: 1px solid #d5d5d5;
                border-radius: 10px;
                font-size: 16px;
                box-sizing: border-box;
            }}
            textarea {{
                min-height: 120px;
                resize: vertical;
            }}
            .btn {{
                border: none;
                background: #111;
                color: white;
                padding: 14px 18px;
                border-radius: 10px;
                font-size: 16px;
                font-weight: bold;
                cursor: pointer;
            }}
            .back {{
                margin-top: 24px;
            }}
            .back a {{
                display: inline-block;
                padding: 12px 18px;
                background: #111;
                color: white;
                text-decoration: none;
                border-radius: 10px;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <div class="wrap">
            <h1>Request Service</h1>
            <h2>{contractor_name}</h2>
            <p class="sub">Fill this out to send your request to this contractor.</p>

            <form method="post" action="/request/{contractor_id}">
                <div>
                    <label for="homeowner_name">Your Name</label>
                    <input type="text" id="homeowner_name" name="homeowner_name" required />
                </div>

                <div>
                    <label for="phone">Phone</label>
                    <input type="text" id="phone" name="phone" required />
                </div>

                <div>
                    <label for="email">Email</label>
                    <input type="email" id="email" name="email" required />
                </div>

                <div>
                    <label for="city">City</label>
                    <input type="text" id="city" name="city" required />
                </div>

                <div>
                    <label for="state">State</label>
                    <input type="text" id="state" name="state" required />
                </div>

                <div>
                    <label for="zip_code">Zip Code</label>
                    <input type="text" id="zip_code" name="zip_code" required />
                </div>

                <div>
                    <label for="service">Service Needed</label>
                    <input type="text" id="service" name="service" value="{contractor_service}" required />
                </div>

                <div>
                    <label for="project_details">Describe Your Project</label>
                    <textarea id="project_details" name="project_details" required></textarea>
                </div>

                <button type="submit" class="btn">Submit Request</button>
            </form>

            <div class="back">
                <a href="/contractors">Back to Contractors</a>
            </div>
        </div>
    </body>
    </html>
    """


@app.post("/request/{contractor_id}")
def submit_request(
    contractor_id: str,
    homeowner_name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    city: str = Form(...),
    state: str = Form(...),
    zip_code: str = Form(...),
    service: str = Form(...),
    project_details: str = Form(...),
):
    contractor_name = "Contractor"

    if supabase:
        try:
            contractor_result = (
                supabase.table("contractors")
                .select("*")
                .eq("id", contractor_id)
                .execute()
                .data
            )
            if contractor_result:
                contractor_name = safe_text(contractor_result[0].get("business_name"), "Contractor")
        except Exception:
            pass

        try:
            supabase.table("leads").insert(
                {
                    "homeowner_name": homeowner_name,
                    "phone": phone,
                    "email": email,
                    "city": city,
                    "state": state,
                    "zip_code": zip_code,
                    "service": service,
                    "project_details": project_details,
                    "contractor_id": contractor_id,
                    "contractor_name": contractor_name,
                    "unlocked": False,
                    "stripe_session_id": "",
                }
            ).execute()
        except Exception:
            return HTMLResponse(
                """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Request Error</title>
                    <meta charset="UTF-8" />
                    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
                    <style>
                        body { font-family: Arial, sans-serif; background: #f4f4f4; padding: 30px; }
                        .box { max-width: 700px; margin: 40px auto; background: white; padding: 30px; border-radius: 14px; box-shadow: 0 8px 30px rgba(0,0,0,0.08); }
                        a { display: inline-block; margin-top: 16px; }
                    </style>
                </head>
                <body>
                    <div class="box">
                        <h1>Could not submit request</h1>
                        <p>Something went wrong while saving this lead.</p>
                        <a href="/contractors">Back to Contractors</a>
                    </div>
                </body>
                </html>
                """,
                status_code=500,
            )

    return RedirectResponse(url="/request-success", status_code=303)


@app.get("/request-success", response_class=HTMLResponse)
def request_success():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Request Submitted</title>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #f4f4f4;
                margin: 0;
                padding: 0;
            }
            .wrap {
                max-width: 760px;
                margin: 60px auto;
                background: white;
                padding: 36px 24px;
                border-radius: 14px;
                box-shadow: 0 8px 30px rgba(0,0,0,0.08);
                text-align: center;
            }
            h1 {
                margin-top: 0;
                color: #111;
            }
            p {
                color: #555;
                line-height: 1.5;
                font-size: 18px;
            }
            a.button {
                display: inline-block;
                margin-top: 18px;
                padding: 14px 22px;
                border-radius: 10px;
                background: #111;
                color: white;
                text-decoration: none;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="wrap">
            <h1>Request Submitted</h1>
            <p>Your homeowner request was saved successfully.</p>
            <p>The selected contractor is now tied to this lead.</p>
            <a class="button" href="/contractors">Back to Contractors</a>
        </div>
    </body>
    </html>
    """


@app.get("/contractor/{contractor_id}", response_class=HTMLResponse)
def contractor_dashboard(contractor_id: str):
    contractor_name = "Contractor Dashboard"
    leads_html = ""

    if supabase:
        try:
            contractor_result = (
                supabase.table("contractors")
                .select("*")
                .eq("id", contractor_id)
                .execute()
                .data
            )
            if contractor_result:
                contractor_name = safe_text(contractor_result[0].get("business_name"), "Contractor Dashboard")
        except Exception:
            pass

        try:
            leads = (
                supabase.table("leads")
                .select("*")
                .eq("contractor_id", contractor_id)
                .order("created_at", desc=True)
                .execute()
                .data
            )
        except Exception:
            leads = []
    else:
        leads = []

    if leads:
        for lead in leads:
            unlocked = bool(lead.get("unlocked", False))
            service = safe_text(lead.get("service"))
            city = safe_text(lead.get("city"))
            state = safe_text(lead.get("state"))
            project_details = safe_text(lead.get("project_details"))
            homeowner_name = safe_text(lead.get("homeowner_name"))
            phone = safe_text(lead.get("phone"))
            email = safe_text(lead.get("email"))
            zip_code = safe_text(lead.get("zip_code"))
            lead_id = safe_text(lead.get("id"))

            location = city
            if state:
                location = f"{city}, {state}" if city else state

            if unlocked:
                leads_html += f"""
                <div class="lead-card unlocked">
                    <div class="status unlocked-badge">Unlocked</div>
                    <h2>{service}</h2>
                    <p><strong>Location:</strong> {location}</p>
                    <p><strong>Zip Code:</strong> {zip_code}</p>
                    <p><strong>Homeowner:</strong> {homeowner_name}</p>
                    <p><strong>Phone:</strong> {phone}</p>
                    <p><strong>Email:</strong> {email}</p>
                    <p><strong>Project Details:</strong> {project_details}</p>
                </div>
                """
            else:
                leads_html += f"""
                <div class="lead-card locked">
                    <div class="status locked-badge">Locked</div>
                    <h2>{service}</h2>
                    <p><strong>Location:</strong> {location}</p>
                    <p><strong>Zip Code:</strong> {zip_code}</p>
                    <p><strong>Project Details:</strong> {project_details[:120]}{"..." if len(project_details) > 120 else ""}</p>
                    <p><strong>Homeowner:</strong> Hidden until unlock</p>
                    <p><strong>Phone:</strong> Hidden until unlock</p>
                    <p><strong>Email:</strong> Hidden until unlock</p>
                    <div class="unlock-row">
                        <a class="unlock-btn" href="/unlock/{lead_id}">Unlock for $10</a>
                    </div>
                </div>
                """
    else:
        leads_html = "<p class='empty'>No leads assigned to this contractor yet.</p>"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{contractor_name}</title>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <style>
            body {{
                font-family: Arial, sans-serif;
                background: #f4f4f4;
                margin: 0;
                padding: 0;
            }}
            .wrap {{
                max-width: 960px;
                margin: 40px auto;
                background: white;
                padding: 32px 24px;
                border-radius: 14px;
                box-shadow: 0 8px 30px rgba(0,0,0,0.08);
            }}
            h1 {{
                margin-top: 0;
                color: #111;
                text-align: center;
            }}
            .sub {{
                text-align: center;
                color: #555;
                margin-bottom: 28px;
            }}
            .lead-card {{
                border-radius: 14px;
                padding: 22px;
                margin-bottom: 18px;
                box-shadow: 0 6px 18px rgba(0,0,0,0.06);
            }}
            .lead-card.locked {{
                background: #fafafa;
                border: 1px solid #e7e7e7;
            }}
            .lead-card.unlocked {{
                background: #f9fff8;
                border: 1px solid #d8edd2;
            }}
            .lead-card h2 {{
                margin-top: 0;
                color: #111;
            }}
            .lead-card p {{
                color: #444;
                line-height: 1.5;
                margin: 8px 0;
            }}
            .status {{
                display: inline-block;
                padding: 6px 10px;
                border-radius: 999px;
                font-size: 13px;
                font-weight: bold;
                margin-bottom: 12px;
            }}
            .locked-badge {{
                background: #f3e8c8;
                color: #7a5b00;
            }}
            .unlocked-badge {{
                background: #dff1db;
                color: #246a1d;
            }}
            .unlock-row {{
                margin-top: 16px;
            }}
            .unlock-btn {{
                display: inline-block;
                padding: 12px 18px;
                border-radius: 10px;
                background: #111;
                color: white;
                text-decoration: none;
                font-weight: bold;
            }}
            .empty {{
                text-align: center;
                color: #555;
                background: #fafafa;
                border: 1px solid #ececec;
                border-radius: 12px;
                padding: 20px;
            }}
            .back {{
                text-align: center;
                margin-top: 24px;
                display: flex;
                gap: 12px;
                justify-content: center;
                flex-wrap: wrap;
            }}
            .back a {{
                display: inline-block;
                padding: 12px 18px;
                background: #111;
                color: white;
                text-decoration: none;
                border-radius: 10px;
                font-weight: bold;
            }}
            .back a.secondary {{
                background: #666;
            }}
        </style>
    </head>
    <body>
        <div class="wrap">
            <h1>{contractor_name}</h1>
            <p class="sub">Leads assigned to this contractor. Locked leads require unlock before full contact details show.</p>

            {leads_html}

            <div class="back">
                <a href="/contractors">Back to Contractors</a>
                <a class="secondary" href="/">Back Home</a>
            </div>
        </div>
    </body>
    </html>
    """


@app.get("/unlock/{lead_id}")
def unlock_lead(lead_id: str):
    contractor_id = ""

    if supabase:
        try:
            lead_result = (
                supabase.table("leads")
                .select("*")
                .eq("id", lead_id)
                .execute()
                .data
            )
            if lead_result:
                contractor_id = safe_text(lead_result[0].get("contractor_id"))
                supabase.table("leads").update({"unlocked": True}).eq("id", lead_id).execute()
        except Exception:
            pass

    if contractor_id:
        return RedirectResponse(url=f"/contractor/{contractor_id}", status_code=303)

    return RedirectResponse(url="/admin", status_code=303)


@app.get("/admin", response_class=HTMLResponse)
def admin():
    contractors_html = ""
    leads_html = ""

    if supabase:
        try:
            contractors = supabase.table("contractors").select("*").execute().data
        except Exception:
            contractors = []

        try:
            leads = supabase.table("leads").select("*").order("created_at", desc=True).execute().data
        except Exception:
            leads = []
    else:
        contractors = []
        leads = []

    if contractors:
        for c in contractors:
            contractor_id = safe_text(c.get("id"))
            contractors_html += f"""
            <div class="card">
                <div><strong>Business:</strong> {safe_text(c.get("business_name"))}</div>
                <div><strong>Service:</strong> {safe_text(c.get("service"))}</div>
                <div><strong>City:</strong> {safe_text(c.get("city"))}</div>
                <div><strong>Approved:</strong> {safe_text(c.get("approved"))}</div>
                <div class="actions">
                    <a class="btn" href="/approve/{contractor_id}">Approve</a>
                    <a class="btn gray" href="/reject/{contractor_id}">Reject</a>
                    <a class="btn blue" href="/contractor/{contractor_id}">Lead Dashboard</a>
                </div>
            </div>
            """
    else:
        contractors_html = "<p>No contractors found.</p>"

    if leads:
        for l in leads:
            leads_html += f"""
            <div class="card">
                <div><strong>Homeowner:</strong> {safe_text(l.get("homeowner_name"))}</div>
                <div><strong>Phone:</strong> {safe_text(l.get("phone"))}</div>
                <div><strong>Email:</strong> {safe_text(l.get("email"))}</div>
                <div><strong>Service:</strong> {safe_text(l.get("service"))}</div>
                <div><strong>City:</strong> {safe_text(l.get("city"))}</div>
                <div><strong>State:</strong> {safe_text(l.get("state"))}</div>
                <div><strong>Zip:</strong> {safe_text(l.get("zip_code"))}</div>
                <div><strong>Contractor Name:</strong> {safe_text(l.get("contractor_name"))}</div>
                <div><strong>Contractor ID:</strong> {safe_text(l.get("contractor_id"))}</div>
                <div><strong>Unlocked:</strong> {safe_text(l.get("unlocked"))}</div>
            </div>
            """
    else:
        leads_html = "<p>No leads found.</p>"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>LeadForge Admin</title>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <style>
            body {{
                font-family: Arial, sans-serif;
                background: #f4f4f4;
                margin: 0;
                padding: 0;
            }}
            .wrap {{
                max-width: 1100px;
                margin: 40px auto;
                background: white;
                padding: 32px 24px;
                border-radius: 14px;
                box-shadow: 0 8px 30px rgba(0,0,0,0.08);
            }}
            h1 {{
                text-align: center;
                color: #111;
                margin-top: 0;
            }}
            h2 {{
                color: #111;
                margin-top: 30px;
            }}
            .card {{
                border: 1px solid #e4e4e4;
                border-radius: 12px;
                padding: 18px;
                margin-bottom: 16px;
                background: #fafafa;
                color: #444;
                line-height: 1.6;
            }}
            .actions {{
                margin-top: 12px;
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
            }}
            .btn {{
                display: inline-block;
                padding: 10px 14px;
                border-radius: 8px;
                text-decoration: none;
                font-size: 14px;
                font-weight: bold;
                background: #111;
                color: white;
            }}
            .btn.gray {{
                background: #666;
            }}
            .btn.blue {{
                background: #2457d6;
            }}
            .back {{
                text-align: center;
                margin-top: 24px;
            }}
            .back a {{
                display: inline-block;
                padding: 12px 18px;
                background: #111;
                color: white;
                text-decoration: none;
                border-radius: 10px;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <div class="wrap">
            <h1>LeadForge Admin</h1>

            <h2>Contractors</h2>
            {contractors_html}

            <h2>Leads</h2>
            {leads_html}

            <div class="back">
                <a href="/">Back Home</a>
            </div>
        </div>
    </body>
    </html>
    """


@app.get("/approve/{contractor_id}")
def approve(contractor_id: str):
    if supabase:
        try:
            supabase.table("contractors").update({"approved": True}).eq("id", contractor_id).execute()
        except Exception:
            pass
    return RedirectResponse("/admin", status_code=303)


@app.get("/reject/{contractor_id}")
def reject(contractor_id: str):
    if supabase:
        try:
            supabase.table("contractors").update({"approved": False}).eq("id", contractor_id).execute()
        except Exception:
            pass
    return RedirectResponse("/admin", status_code=303)
