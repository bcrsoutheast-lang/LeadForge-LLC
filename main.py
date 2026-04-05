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
                opacity: 0.9;
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
            contractor_id = c.get("id", "")
            business_name = c.get("business_name", "Contractor")
            service = c.get("service", "")
            city = c.get("city", "")
            state = c.get("state", "")

            location = city
            if state:
                location = f"{city}, {state}" if city else state

            contractor_cards += f"""
            <div class="card">
                <h2>{business_name}</h2>
                <p><strong>Service:</strong> {service}</p>
                <p><strong>Location:</strong> {location}</p>
                <a class="btn" href="/request/{contractor_id}">Request Quote</a>
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

            .btn {{
                display: inline-block;
                margin-top: 14px;
                padding: 12px 16px;
                border-radius: 10px;
                background: #111;
                color: white;
                text-decoration: none;
                font-weight: bold;
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
                contractor_name = result[0].get("business_name", "Contractor")
                contractor_service = result[0].get("service", "")
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
                    <label for="zip_code">ZIP Code</label>
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
                contractor_name = contractor_result[0].get("business_name", "Contractor")
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
            <p>The request is now tied to the selected contractor.</p>
            <a class="button" href="/contractors">Back to Contractors</a>
        </div>
    </body>
    </html>
    """


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
            leads = supabase.table("leads").select("*").execute().data
        except Exception:
            leads = []
    else:
        contractors = []
        leads = []

    if contractors:
        for c in contractors:
            contractor_id = c.get("id")
            contractors_html += f"""
            <div class="card">
                <div><strong>Business:</strong> {c.get("business_name", "")}</div>
                <div><strong>Service:</strong> {c.get("service", "")}</div>
                <div><strong>City:</strong> {c.get("city", "")}</div>
                <div><strong>Approved:</strong> {c.get("approved", "")}</div>
                <div class="actions">
                    <a class="btn" href="/approve/{contractor_id}">Approve</a>
                    <a class="btn gray" href="/reject/{contractor_id}">Reject</a>
                </div>
            </div>
            """
    else:
        contractors_html = "<p>No contractors found.</p>"

    if leads:
        for l in leads:
            leads_html += f"""
            <div class="card">
                <div><strong>Homeowner:</strong> {l.get("homeowner_name", "")}</div>
                <div><strong>Phone:</strong> {l.get("phone", "")}</div>
                <div><strong>Email:</strong> {l.get("email", "")}</div>
                <div><strong>Service:</strong> {l.get("service", "")}</div>
                <div><strong>City:</strong> {l.get("city", "")}, {l.get("state", "")} {l.get("zip_code", "")}</div>
                <div><strong>Contractor:</strong> {l.get("contractor_name", "")}</div>
                <div><strong>Contractor ID:</strong> {l.get("contractor_id", "")}</div>
                <div><strong>Unlocked:</strong> {l.get("unlocked", "")}</div>
                <div><strong>Project Details:</strong> {l.get("project_details", "")}</div>
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
