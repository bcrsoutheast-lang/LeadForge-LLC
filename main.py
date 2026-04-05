from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client
import os
import stripe
import traceback

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
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID")
BASE_URL = os.getenv("LEADFORGE_BASE_URL", "https://leadforge-llc.onrender.com").rstrip("/")

supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY


def safe_text(value, fallback=""):
    if value is None:
        return fallback
    return str(value)


def html_page(title: str, body: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
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
            }}
            h2 {{
                color: #222;
            }}
            p {{
                color: #555;
                line-height: 1.5;
            }}
            .button-row {{
                display: flex;
                gap: 12px;
                flex-wrap: wrap;
                margin-top: 18px;
            }}
            a.button {{
                display: inline-block;
                padding: 12px 18px;
                background: #111;
                color: white;
                text-decoration: none;
                border-radius: 10px;
                font-weight: bold;
            }}
            a.button.gray {{
                background: #666;
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
            .badge {{
                display: inline-block;
                padding: 6px 10px;
                border-radius: 999px;
                font-size: 13px;
                font-weight: bold;
                margin-bottom: 12px;
            }}
            .badge.locked {{
                background: #f3e8c8;
                color: #7a5b00;
            }}
            .badge.unlocked {{
                background: #dff1db;
                color: #246a1d;
            }}
            .badge.pending {{
                background: #dfe7fb;
                color: #224a9f;
            }}
            input, select, textarea {{
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
            label {{
                font-weight: bold;
                color: #222;
                display: block;
                margin-bottom: 6px;
            }}
            form {{
                display: grid;
                gap: 16px;
            }}
            button {{
                border: none;
                background: #111;
                color: white;
                padding: 14px 18px;
                border-radius: 10px;
                font-size: 16px;
                font-weight: bold;
                cursor: pointer;
            }}
            .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
                gap: 20px;
            }}
            pre {{
                white-space: pre-wrap;
                word-break: break-word;
                background: #111;
                color: #fff;
                padding: 14px;
                border-radius: 10px;
                overflow-x: auto;
            }}
        </style>
    </head>
    <body>
        <div class="wrap">
            {body}
        </div>
    </body>
    </html>
    """


@app.get("/", response_class=HTMLResponse)
def home():
    return html_page(
        "LeadForge",
        """
        <h1>LeadForge</h1>
        <p>Browse approved contractors and submit an exclusive homeowner request.</p>
        <div class="button-row">
            <a class="button" href="/contractors">Browse Contractors</a>
            <a class="button" href="/contractor-signup">Join as a Contractor</a>
            <a class="button" href="/admin">Admin</a>
            <a class="button" href="/health">Health Check</a>
        </div>
        """,
    )


@app.get("/health")
def health():
    return {
        "status": "ok",
        "supabase_connected": bool(supabase),
        "stripe_secret_key_present": bool(STRIPE_SECRET_KEY),
        "stripe_price_id_present": bool(STRIPE_PRICE_ID),
        "base_url": BASE_URL,
        "stripe_configured": bool(STRIPE_SECRET_KEY and STRIPE_PRICE_ID and BASE_URL),
    }


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
        except Exception as e:
            print(f"ERROR loading contractors: {e}")
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
                <div class="button-row">
                    <a class="button" href="/request/{contractor_id}">Request Quote</a>
                    <a class="button gray" href="/contractor/{contractor_id}">Contractor Lead View</a>
                </div>
            </div>
            """
    else:
        contractor_cards = "<p>No approved contractors yet.</p>"

    return html_page(
        "Browse Contractors",
        f"""
        <h1>Browse Contractors</h1>
        <p>Select a contractor to send an exclusive homeowner request.</p>
        <div class="grid">
            {contractor_cards}
        </div>
        <div class="button-row">
            <a class="button" href="/">Back Home</a>
        </div>
        """,
    )


@app.get("/contractor-signup", response_class=HTMLResponse)
def contractor_signup():
    return html_page(
        "Contractor Signup",
        """
        <h1>Join LeadForge</h1>
        <p>Contractor signup form is visible. Submit wiring can be reconnected next.</p>

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

            <div class="card">
                <label>
                    <input type="checkbox" />
                    Contractor Agreement: I understand that submitting this application does not guarantee approval.
                </label>
            </div>

            <button type="button">Submit Application</button>
        </form>

        <div class="button-row">
            <a class="button" href="/">Back Home</a>
        </div>
        """,
    )


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
        except Exception as e:
            print(f"ERROR loading contractor request page: {e}")

    return html_page(
        "Request Service",
        f"""
        <h1>Request Service</h1>
        <h2>{contractor_name}</h2>
        <p>Fill this out to send your request to this contractor.</p>

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

            <button type="submit">Submit Request</button>
        </form>

        <div class="button-row">
            <a class="button" href="/contractors">Back to Contractors</a>
        </div>
        """,
    )


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
        except Exception as e:
            print(f"ERROR loading contractor during submit_request: {e}")

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
        except Exception as e:
            print(f"ERROR inserting lead: {e}")
            print(traceback.format_exc())
            return HTMLResponse(
                html_page(
                    "Request Error",
                    """
                    <h1>Could not submit request</h1>
                    <p>Something went wrong while saving this lead.</p>
                    <div class="button-row">
                        <a class="button" href="/contractors">Back to Contractors</a>
                    </div>
                    """,
                ),
                status_code=500,
            )

    return RedirectResponse(url="/request-success", status_code=303)


@app.get("/request-success", response_class=HTMLResponse)
def request_success():
    return html_page(
        "Request Submitted",
        """
        <h1>Request Submitted</h1>
        <p>Your homeowner request was saved successfully.</p>
        <p>The selected contractor is now tied to this lead.</p>
        <div class="button-row">
            <a class="button" href="/contractors">Back to Contractors</a>
        </div>
        """,
    )


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
        except Exception as e:
            print(f"ERROR loading contractor dashboard contractor: {e}")

        try:
            leads = (
                supabase.table("leads")
                .select("*")
                .eq("contractor_id", contractor_id)
                .order("created_at", desc=True)
                .execute()
                .data
            )
        except Exception as e:
            print(f"ERROR loading contractor dashboard leads: {e}")
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
                <div class="card">
                    <div class="badge unlocked">Unlocked</div>
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
                short_project = project_details[:120] + ("..." if len(project_details) > 120 else "")
                leads_html += f"""
                <div class="card">
                    <div class="badge locked">Locked</div>
                    <h2>{service}</h2>
                    <p><strong>Location:</strong> {location}</p>
                    <p><strong>Zip Code:</strong> {zip_code}</p>
                    <p><strong>Project Details:</strong> {short_project}</p>
                    <p><strong>Homeowner:</strong> Hidden until unlock</p>
                    <p><strong>Phone:</strong> Hidden until unlock</p>
                    <p><strong>Email:</strong> Hidden until unlock</p>
                    <div class="button-row">
                        <a class="button" href="/unlock/{lead_id}">Unlock for $10</a>
                    </div>
                </div>
                """
    else:
        leads_html = "<p>No leads assigned to this contractor yet.</p>"

    return html_page(
        contractor_name,
        f"""
        <h1>{contractor_name}</h1>
        <p>Leads assigned to this contractor. Locked leads require payment before full contact details show.</p>

        {leads_html}

        <div class="button-row">
            <a class="button" href="/contractors">Back to Contractors</a>
            <a class="button gray" href="/">Back Home</a>
        </div>
        """,
    )


@app.get("/unlock/{lead_id}")
def unlock_lead(lead_id: str):
    if not supabase:
        return HTMLResponse(
            html_page(
                "Unlock Error",
                """
                <h1>Supabase is not connected</h1>
                <p>The app cannot find the database connection right now.</p>
                <div class="button-row">
                    <a class="button" href="/admin">Back to Admin</a>
                </div>
                """,
            ),
            status_code=500,
        )

    if not STRIPE_SECRET_KEY or not STRIPE_PRICE_ID:
        return HTMLResponse(
            html_page(
                "Stripe Not Configured",
                f"""
                <h1>Stripe is not configured yet</h1>
                <p>Add these Render environment variables:</p>
                <div class="card">
                    <strong>STRIPE_SECRET_KEY</strong><br>
                    <strong>STRIPE_PRICE_ID</strong><br>
                    <strong>LEADFORGE_BASE_URL</strong> = {BASE_URL}
                </div>
                <div class="button-row">
                    <a class="button" href="/admin">Back to Admin</a>
                </div>
                """,
            ),
            status_code=500,
        )

    contractor_id = ""

    try:
        lead_result = (
            supabase.table("leads")
            .select("*")
            .eq("id", lead_id)
            .execute()
            .data
        )
        if not lead_result:
            return HTMLResponse(
                html_page(
                    "Lead Not Found",
                    """
                    <h1>Lead not found</h1>
                    <div class="button-row">
                        <a class="button" href="/admin">Back to Admin</a>
                    </div>
                    """,
                ),
                status_code=404,
            )

        lead = lead_result[0]
        contractor_id = safe_text(lead.get("contractor_id"))

        if bool(lead.get("unlocked", False)):
            if contractor_id:
                return RedirectResponse(url=f"/contractor/{contractor_id}", status_code=303)
            return RedirectResponse(url="/admin", status_code=303)

        success_url = f"{BASE_URL}/stripe-success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{BASE_URL}/contractor/{contractor_id}" if contractor_id else f"{BASE_URL}/admin"

        print("DEBUG STRIPE CONFIG")
        print(f"BASE_URL: {BASE_URL}")
        print(f"STRIPE_PRICE_ID: {STRIPE_PRICE_ID}")
        print(f"lead_id: {lead_id}")
        print(f"contractor_id: {contractor_id}")
        print(f"success_url: {success_url}")
        print(f"cancel_url: {cancel_url}")

        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[
                {
                    "price": STRIPE_PRICE_ID,
                    "quantity": 1,
                }
            ],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "lead_id": lead_id,
                "contractor_id": contractor_id,
            },
        )

        print(f"Stripe session created: {session.id}")
        print(f"Stripe session url: {session.url}")

        supabase.table("leads").update(
            {"stripe_session_id": session.id}
        ).eq("id", lead_id).execute()

        return RedirectResponse(url=session.url, status_code=303)

    except Exception as e:
        print(f"UNLOCK ROUTE ERROR: {e}")
        print(traceback.format_exc())

        fallback = f"/contractor/{contractor_id}" if contractor_id else "/admin"
        return HTMLResponse(
            html_page(
                "Stripe Checkout Error",
                f"""
                <h1>Could not start checkout</h1>
                <p>Something went wrong while creating the Stripe checkout session.</p>
                <div class="card">
                    <strong>Error:</strong><br>
                    <pre>{safe_text(e)}</pre>
                </div>
                <div class="button-row">
                    <a class="button" href="{fallback}">Go Back</a>
                </div>
                """,
            ),
            status_code=500,
        )


@app.get("/stripe-success")
def stripe_success(session_id: str = ""):
    if not supabase:
        return HTMLResponse(
            html_page(
                "Supabase Error",
                """
                <h1>Supabase is not connected</h1>
                <p>The payment returned, but the database is unavailable.</p>
                <div class="button-row">
                    <a class="button" href="/admin">Back to Admin</a>
                </div>
                """,
            ),
            status_code=500,
        )

    if not STRIPE_SECRET_KEY:
        return HTMLResponse(
            html_page(
                "Stripe Error",
                """
                <h1>Stripe is not configured</h1>
                <div class="button-row">
                    <a class="button" href="/admin">Back to Admin</a>
                </div>
                """,
            ),
            status_code=500,
        )

    try:
        session = stripe.checkout.Session.retrieve(session_id)
        lead_id = safe_text(session.metadata.get("lead_id")) if session.metadata else ""
        contractor_id = safe_text(session.metadata.get("contractor_id")) if session.metadata else ""

        print(f"stripe_success session_id: {session_id}")
        print(f"stripe_success payment_status: {session.payment_status}")
        print(f"stripe_success lead_id: {lead_id}")
        print(f"stripe_success contractor_id: {contractor_id}")

        if session.payment_status == "paid" and lead_id:
            supabase.table("leads").update({"unlocked": True}).eq("id", lead_id).execute()

        if contractor_id:
            return RedirectResponse(url=f"/contractor/{contractor_id}", status_code=303)

        return RedirectResponse(url="/admin", status_code=303)
    except Exception as e:
        print(f"STRIPE SUCCESS ERROR: {e}")
        print(traceback.format_exc())
        return HTMLResponse(
            html_page(
                "Payment Verification Error",
                f"""
                <h1>Could not verify payment</h1>
                <p>The checkout returned, but payment verification failed.</p>
                <div class="card">
                    <strong>Error:</strong><br>
                    <pre>{safe_text(e)}</pre>
                </div>
                <div class="button-row">
                    <a class="button" href="/admin">Back to Admin</a>
                </div>
                """,
            ),
            status_code=500,
        )


@app.get("/admin", response_class=HTMLResponse)
def admin():
    contractors_html = ""
    leads_html = ""

    if supabase:
        try:
            contractors = supabase.table("contractors").select("*").execute().data
        except Exception as e:
            print(f"ERROR loading admin contractors: {e}")
            contractors = []

        try:
            leads = supabase.table("leads").select("*").order("created_at", desc=True).execute().data
        except Exception as e:
            print(f"ERROR loading admin leads: {e}")
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
                <div class="button-row">
                    <a class="button" href="/approve/{contractor_id}">Approve</a>
                    <a class="button gray" href="/reject/{contractor_id}">Reject</a>
                    <a class="button" href="/contractor/{contractor_id}">Lead Dashboard</a>
                </div>
            </div>
            """
    else:
        contractors_html = "<p>No contractors found.</p>"

    if leads:
        for l in leads:
            unlocked = bool(l.get("unlocked", False))
            session_id = safe_text(l.get("stripe_session_id"))
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
                <div><strong>Unlocked:</strong> {safe_text(unlocked)}</div>
                <div><strong>Stripe Session ID:</strong> {session_id}</div>
            </div>
            """
    else:
        leads_html = "<p>No leads found.</p>"

    return html_page(
        "LeadForge Admin",
        f"""
        <h1>LeadForge Admin</h1>

        <h2>Contractors</h2>
        {contractors_html}

        <h2>Leads</h2>
        {leads_html}

        <div class="button-row">
            <a class="button" href="/">Back Home</a>
        </div>
        """,
    )


@app.get("/approve/{contractor_id}")
def approve(contractor_id: str):
    if supabase:
        try:
            supabase.table("contractors").update({"approved": True}).eq("id", contractor_id).execute()
        except Exception as e:
            print(f"ERROR approving contractor {contractor_id}: {e}")
    return RedirectResponse("/admin", status_code=303)


@app.get("/reject/{contractor_id}")
def reject(contractor_id: str):
    if supabase:
        try:
            supabase.table("contractors").update({"approved": False}).eq("id", contractor_id).execute()
        except Exception as e:
            print(f"ERROR rejecting contractor {contractor_id}: {e}")
    return RedirectResponse("/admin", status_code=303)
