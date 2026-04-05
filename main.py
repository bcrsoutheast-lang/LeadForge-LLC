import os
from html import escape
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from supabase import Client, create_client


app = FastAPI(title="LeadForge Stable Rebuild")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_supabase() -> Optional[Client]:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or os.getenv("SUPABASE_KEY")
        or os.getenv("SUPABASE_ANON_KEY")
    )

    if not supabase_url or not supabase_key:
        return None

    try:
        return create_client(supabase_url, supabase_key)
    except Exception:
        return None


def safe_fetch_table(supabase: Client, table_name: str) -> List[Dict[str, Any]]:
    try:
        response = supabase.table(table_name).select("*").execute()
        return response.data if response.data else []
    except Exception:
        return []


def safe_insert_record(supabase: Client, table_name: str, payload: Dict[str, Any]) -> tuple[bool, str]:
    try:
        supabase.table(table_name).insert(payload).execute()
        return True, "Saved successfully."
    except Exception as exc:
        return False, str(exc)


def page_shell(title: str, body: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: Arial, sans-serif;
                background: #f7f7f7;
                margin: 0;
                padding: 30px 15px;
            }}
            .wrap {{
                max-width: 900px;
                margin: 0 auto;
            }}
            .card {{
                background: white;
                padding: 24px;
                border-radius: 14px;
                box-shadow: 0 4px 18px rgba(0,0,0,0.08);
                margin-bottom: 20px;
            }}
            h1, h2, h3 {{
                margin-top: 0;
            }}
            p {{
                color: #444;
                line-height: 1.5;
            }}
            .btn {{
                display: inline-block;
                margin: 8px 8px 0 0;
                padding: 12px 18px;
                background: #111827;
                color: white;
                text-decoration: none;
                border-radius: 10px;
                font-weight: bold;
                border: none;
                cursor: pointer;
            }}
            .btn:hover {{
                opacity: 0.92;
            }}
            .btn-secondary {{
                background: #374151;
            }}
            .grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 14px;
            }}
            label {{
                display: block;
                font-weight: bold;
                margin-bottom: 6px;
            }}
            input, select, textarea {{
                width: 100%;
                box-sizing: border-box;
                padding: 12px;
                border: 1px solid #d1d5db;
                border-radius: 10px;
                font-size: 16px;
                background: #fff;
            }}
            textarea {{
                min-height: 110px;
                resize: vertical;
            }}
            .full {{
                grid-column: 1 / -1;
            }}
            .success {{
                background: #ecfdf5;
                border: 1px solid #10b981;
                color: #065f46;
                padding: 14px;
                border-radius: 10px;
                margin-bottom: 18px;
            }}
            .error {{
                background: #fef2f2;
                border: 1px solid #ef4444;
                color: #991b1b;
                padding: 14px;
                border-radius: 10px;
                margin-bottom: 18px;
            }}
            .muted {{
                color: #6b7280;
                font-size: 14px;
            }}
            .table-wrap {{
                overflow-x: auto;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 12px;
            }}
            th, td {{
                border: 1px solid #e5e7eb;
                padding: 10px;
                text-align: left;
                font-size: 14px;
                vertical-align: top;
                white-space: nowrap;
            }}
            th {{
                background: #111827;
                color: white;
            }}
            a {{
                color: #111827;
                font-weight: bold;
                text-decoration: none;
            }}
            @media (max-width: 700px) {{
                .grid {{
                    grid-template-columns: 1fr;
                }}
                .full {{
                    grid-column: auto;
                }}
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


def build_admin_table(title: str, rows: List[Dict[str, Any]]) -> str:
    if not rows:
        return f"""
        <section class="card">
            <h2>{title}</h2>
            <p>No records found.</p>
        </section>
        """

    columns = sorted({key for row in rows for key in row.keys()})
    header_html = "".join(f"<th>{escape(str(col))}</th>" for col in columns)

    body_parts = []
    for row in rows:
        cells = []
        for col in columns:
            value = row.get(col, "")
            if value is None:
                value = ""
            cells.append(f"<td>{escape(str(value))}</td>")
        body_parts.append(f"<tr>{''.join(cells)}</tr>")

    return f"""
    <section class="card">
        <h2>{title} ({len(rows)})</h2>
        <div class="table-wrap">
            <table>
                <thead>
                    <tr>{header_html}</tr>
                </thead>
                <tbody>
                    {''.join(body_parts)}
                </tbody>
            </table>
        </div>
    </section>
    """


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>LeadForge LLC</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #f7f7f7;
                margin: 0;
                padding: 40px 20px;
                text-align: center;
            }
            .wrap {
                max-width: 700px;
                margin: 0 auto;
                background: white;
                padding: 40px 25px;
                border-radius: 14px;
                box-shadow: 0 4px 18px rgba(0,0,0,0.08);
            }
            h1 {
                margin-bottom: 10px;
            }
            p {
                color: #555;
                margin-bottom: 30px;
            }
            .btn {
                display: inline-block;
                margin: 10px;
                padding: 14px 22px;
                background: #111827;
                color: white;
                text-decoration: none;
                border-radius: 10px;
                font-weight: bold;
            }
            .btn:hover {
                opacity: 0.9;
            }
        </style>
    </head>
    <body>
        <div class="wrap">
            <h1>LeadForge LLC</h1>
            <p>Stable fallback homepage is live.</p>
            <a class="btn" href="/contractor-signup">Contractor Signup</a>
            <a class="btn" href="/admin">Admin</a>
        </div>
    </body>
    </html>
    """


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/contractor-signup", response_class=HTMLResponse)
def contractor_signup_page() -> str:
    body = """
    <section class="card">
        <h1>Contractor Signup</h1>
        <p>We are rebuilding from the stable fallback app, one route at a time.</p>
        <p class="muted">This is now a clean live contractor submission form tied back into the backend.</p>
    </section>

    <section class="card">
        <form method="post" action="/contractor-signup">
            <div class="grid">
                <div>
                    <label for="business_name">Business Name</label>
                    <input id="business_name" name="business_name" required>
                </div>

                <div>
                    <label for="contact_name">Contact Name</label>
                    <input id="contact_name" name="contact_name" required>
                </div>

                <div>
                    <label for="email">Email</label>
                    <input id="email" name="email" type="email" required>
                </div>

                <div>
                    <label for="phone">Phone</label>
                    <input id="phone" name="phone" required>
                </div>

                <div>
                    <label for="service">Service</label>
                    <input id="service" name="service" placeholder="Roofing, Plumbing, HVAC..." required>
                </div>

                <div>
                    <label for="city">City</label>
                    <input id="city" name="city" required>
                </div>

                <div>
                    <label for="state">State</label>
                    <input id="state" name="state" required>
                </div>

                <div>
                    <label for="zip_code">ZIP Code</label>
                    <input id="zip_code" name="zip_code" required>
                </div>

                <div class="full">
                    <label for="bio">Short Bio</label>
                    <textarea id="bio" name="bio" placeholder="Tell homeowners about your company, experience, and service area."></textarea>
                </div>

                <div class="full">
                    <button class="btn" type="submit">Submit Contractor Signup</button>
                    <a class="btn btn-secondary" href="/">Back to Homepage</a>
                </div>
            </div>
        </form>
    </section>
    """
    return page_shell("Contractor Signup - LeadForge", body)


@app.post("/contractor-signup", response_class=HTMLResponse)
def contractor_signup_submit(
    business_name: str = Form(...),
    contact_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    service: str = Form(...),
    city: str = Form(...),
    state: str = Form(...),
    zip_code: str = Form(...),
    bio: str = Form(""),
) -> str:
    supabase = get_supabase()

    if supabase is None:
        body = """
        <section class="card">
            <h1>Contractor Signup</h1>
            <div class="error">
                Supabase is not connected. Check Render environment variables before testing submissions.
            </div>
            <a class="btn" href="/contractor-signup">Back to Form</a>
            <a class="btn btn-secondary" href="/">Homepage</a>
        </section>
        """
        return page_shell("Contractor Signup Error - LeadForge", body)

    payload = {
        "business_name": business_name.strip(),
        "contact_name": contact_name.strip(),
        "email": email.strip(),
        "phone": phone.strip(),
        "service": service.strip(),
        "city": city.strip(),
        "state": state.strip(),
        "zip_code": zip_code.strip(),
        "bio": bio.strip(),
        "approved": False,
    }

    ok, message = safe_insert_record(supabase, "contractors", payload)

    if not ok:
        body = f"""
        <section class="card">
            <h1>Contractor Signup</h1>
            <div class="error">
                Submission failed.<br><br>
                {escape(message)}
            </div>
            <a class="btn" href="/contractor-signup">Back to Form</a>
            <a class="btn btn-secondary" href="/">Homepage</a>
        </section>
        """
        return page_shell("Contractor Signup Error - LeadForge", body)

    body = f"""
    <section class="card">
        <h1>Contractor Signup Submitted</h1>
        <div class="success">
            Your contractor information was submitted successfully.
        </div>

        <h3>Submitted Info</h3>
        <p><strong>Business:</strong> {escape(business_name)}</p>
        <p><strong>Contact:</strong> {escape(contact_name)}</p>
        <p><strong>Email:</strong> {escape(email)}</p>
        <p><strong>Phone:</strong> {escape(phone)}</p>
        <p><strong>Service:</strong> {escape(service)}</p>
        <p><strong>Location:</strong> {escape(city)}, {escape(state)} {escape(zip_code)}</p>

        <a class="btn" href="/contractor-signup">Submit Another</a>
        <a class="btn btn-secondary" href="/admin">Go to Admin</a>
    </section>
    """
    return page_shell("Contractor Signup Submitted - LeadForge", body)


@app.get("/contractors")
def contractors_json() -> JSONResponse:
    supabase = get_supabase()

    if supabase is None:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": "Supabase is not connected."},
        )

    contractors = safe_fetch_table(supabase, "contractors")
    return JSONResponse(content={"ok": True, "contractors": contractors})


@app.get("/admin", response_class=HTMLResponse)
def admin_page() -> HTMLResponse:
    supabase = get_supabase()

    if supabase is None:
        body = """
        <section class="card">
            <h1>LeadForge Admin</h1>
            <div class="error">
                Supabase is not connected. Check Render environment variables:
                SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY
                (or SUPABASE_KEY / SUPABASE_ANON_KEY).
            </div>
            <a class="btn" href="/">Back to Homepage</a>
        </section>
        """
        return HTMLResponse(content=page_shell("LeadForge Admin", body))

    contractors = safe_fetch_table(supabase, "contractors")
    leads = safe_fetch_table(supabase, "leads")

    body = f"""
    <section class="card">
        <h1>LeadForge Admin</h1>
        <p class="muted">Stable rebuild step: contractor route restored cleanly.</p>
        <a class="btn" href="/">Homepage</a>
        <a class="btn btn-secondary" href="/contractor-signup">Contractor Signup</a>
    </section>

    {build_admin_table("Contractors", contractors)}
    {build_admin_table("Leads", leads)}
    """

    return HTMLResponse(content=page_shell("LeadForge Admin", body))


@app.get("/admin/data")
def admin_data() -> JSONResponse:
    supabase = get_supabase()

    if supabase is None:
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": "Supabase is not connected. Check environment variables."
            },
        )

    contractors = safe_fetch_table(supabase, "contractors")
    leads = safe_fetch_table(supabase, "leads")

    return JSONResponse(
        content={
            "ok": True,
            "contractors": contractors,
            "leads": leads,
        }
    )
