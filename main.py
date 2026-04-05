import os
from html import escape
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
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


def safe_insert_record(
    supabase: Client, table_name: str, payload: Dict[str, Any]
) -> tuple[bool, str]:
    try:
        supabase.table(table_name).insert(payload).execute()
        return True, "Saved successfully."
    except Exception as exc:
        return False, str(exc)


def safe_update_record(
    supabase: Client, table_name: str, record_id: str, payload: Dict[str, Any]
) -> tuple[bool, str]:
    try:
        supabase.table(table_name).update(payload).eq("id", record_id).execute()
        return True, "Updated successfully."
    except Exception as exc:
        return False, str(exc)


def page_shell(title: str, body: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{escape(title)}</title>
        <style>
            * {{
                box-sizing: border-box;
            }}

            body {{
                margin: 0;
                font-family: Arial, sans-serif;
                background: #f5f7fb;
                color: #111827;
            }}

            .container {{
                max-width: 1180px;
                margin: 0 auto;
                padding: 24px 16px 48px;
            }}

            .hero {{
                background: linear-gradient(135deg, #0f172a, #1f2937);
                color: white;
                padding: 28px 22px;
                border-radius: 20px;
                margin-bottom: 22px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.18);
            }}

            .hero h1 {{
                margin: 0 0 10px;
                font-size: 34px;
                line-height: 1.1;
            }}

            .hero p {{
                margin: 0;
                color: rgba(255,255,255,0.88);
                line-height: 1.5;
            }}

            .nav-row {{
                margin-top: 18px;
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
            }}

            .btn {{
                display: inline-block;
                padding: 12px 18px;
                border-radius: 12px;
                text-decoration: none;
                font-weight: 700;
                border: none;
                cursor: pointer;
            }}

            .btn-primary {{
                background: white;
                color: #111827;
            }}

            .btn-dark {{
                background: #111827;
                color: white;
            }}

            .btn-gray {{
                background: #374151;
                color: white;
            }}

            .btn-green {{
                background: #166534;
                color: white;
            }}

            .btn-red {{
                background: #991b1b;
                color: white;
            }}

            .btn-sm {{
                padding: 10px 12px;
                border-radius: 10px;
                font-size: 14px;
            }}

            .card {{
                background: white;
                border-radius: 18px;
                padding: 22px;
                box-shadow: 0 10px 28px rgba(15, 23, 42, 0.08);
                margin-bottom: 20px;
            }}

            .muted {{
                color: #6b7280;
            }}

            .section-title {{
                margin: 0 0 10px;
                font-size: 28px;
            }}

            .section-text {{
                margin: 0;
                color: #4b5563;
                line-height: 1.5;
            }}

            .form-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 14px;
            }}

            .full {{
                grid-column: 1 / -1;
            }}

            label {{
                display: block;
                margin-bottom: 6px;
                font-weight: 700;
            }}

            input, textarea {{
                width: 100%;
                padding: 12px 14px;
                border: 1px solid #d1d5db;
                border-radius: 12px;
                font-size: 16px;
                background: #fff;
            }}

            textarea {{
                min-height: 120px;
                resize: vertical;
            }}

            .success {{
                background: #ecfdf5;
                color: #065f46;
                border: 1px solid #10b981;
                padding: 14px 16px;
                border-radius: 12px;
                margin-bottom: 16px;
            }}

            .error {{
                background: #fef2f2;
                color: #991b1b;
                border: 1px solid #ef4444;
                padding: 14px 16px;
                border-radius: 12px;
                margin-bottom: 16px;
            }}

            .stats {{
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 14px;
                margin-bottom: 22px;
            }}

            .stat {{
                background: white;
                border-radius: 18px;
                padding: 18px;
                box-shadow: 0 10px 28px rgba(15, 23, 42, 0.08);
            }}

            .stat-label {{
                color: #6b7280;
                font-size: 14px;
                margin-bottom: 8px;
            }}

            .stat-value {{
                font-size: 28px;
                font-weight: 800;
            }}

            .cards-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 18px;
            }}

            .contractor-card {{
                background: white;
                border-radius: 18px;
                padding: 20px;
                box-shadow: 0 12px 30px rgba(15, 23, 42, 0.08);
                border: 1px solid #e5e7eb;
            }}

            .contractor-top {{
                display: flex;
                align-items: flex-start;
                justify-content: space-between;
                gap: 12px;
                margin-bottom: 12px;
            }}

            .contractor-name {{
                margin: 0;
                font-size: 22px;
                line-height: 1.2;
            }}

            .badge {{
                display: inline-block;
                font-size: 12px;
                font-weight: 800;
                letter-spacing: 0.02em;
                padding: 8px 10px;
                border-radius: 999px;
                white-space: nowrap;
            }}

            .badge-approved {{
                background: #dcfce7;
                color: #166534;
            }}

            .badge-pending {{
                background: #fef3c7;
                color: #92400e;
            }}

            .meta-list {{
                display: grid;
                gap: 8px;
                margin: 14px 0 0;
            }}

            .meta-item {{
                color: #374151;
                line-height: 1.45;
            }}

            .meta-label {{
                font-weight: 700;
                color: #111827;
            }}

            .empty {{
                text-align: center;
                padding: 42px 18px;
                background: white;
                border-radius: 18px;
                box-shadow: 0 10px 28px rgba(15, 23, 42, 0.08);
            }}

            .table-wrap {{
                overflow-x: auto;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 14px;
            }}

            th, td {{
                border: 1px solid #e5e7eb;
                padding: 10px;
                text-align: left;
                vertical-align: top;
                font-size: 14px;
            }}

            th {{
                background: #111827;
                color: white;
            }}

            .actions {{
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
            }}

            .action-form {{
                margin: 0;
            }}

            .check-row {{
                display: flex;
                align-items: flex-start;
                gap: 10px;
                margin-top: 8px;
                padding: 14px;
                background: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
            }}

            .check-row input[type="checkbox"] {{
                width: auto;
                margin-top: 3px;
                transform: scale(1.2);
            }}

            .check-row label {{
                margin: 0;
                font-weight: 400;
                line-height: 1.5;
            }}

            @media (max-width: 800px) {{
                .form-grid,
                .stats {{
                    grid-template-columns: 1fr;
                }}

                .full {{
                    grid-column: auto;
                }}

                .hero h1 {{
                    font-size: 28px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            {body}
        </div>
    </body>
    </html>
    """


def build_admin_table(title: str, rows: List[Dict[str, Any]]) -> str:
    if not rows:
        return f"""
        <section class="card">
            <h2>{escape(title)}</h2>
            <p class="muted">No records found.</p>
        </section>
        """

    columns = sorted({key for row in rows for key in row.keys()})
    header_html = "".join(f"<th>{escape(str(col))}</th>" for col in columns)

    body_rows = []
    for row in rows:
        cells = []
        for col in columns:
            value = row.get(col, "")
            if value is None:
                value = ""
            cells.append(f"<td>{escape(str(value))}</td>")
        body_rows.append(f"<tr>{''.join(cells)}</tr>")

    return f"""
    <section class="card">
        <h2>{escape(title)} ({len(rows)})</h2>
        <div class="table-wrap">
            <table>
                <thead>
                    <tr>{header_html}</tr>
                </thead>
                <tbody>
                    {''.join(body_rows)}
                </tbody>
            </table>
        </div>
    </section>
    """


def build_contractor_admin_table(contractors: List[Dict[str, Any]]) -> str:
    if not contractors:
        return """
        <section class="card">
            <h2>Contractors</h2>
            <p class="muted">No contractors found.</p>
        </section>
        """

    columns = [
        "business_name",
        "company_name",
        "contact_name",
        "owner_name",
        "service",
        "service_type",
        "city",
        "state",
        "zip_code",
        "phone",
        "email",
        "approved",
    ]

    header_html = "".join(f"<th>{escape(col)}</th>" for col in columns)
    header_html += "<th>actions</th>"

    body_rows = []
    for contractor in contractors:
        cells = []
        for col in columns:
            value = contractor.get(col, "")
            if value is None:
                value = ""
            cells.append(f"<td>{escape(str(value))}</td>")

        contractor_id = str(contractor.get("id", "") or "")
        actions_html = f"""
        <div class="actions">
            <form class="action-form" method="post" action="/admin/contractors/{escape(contractor_id)}/approve">
                <button class="btn btn-green btn-sm" type="submit">Approve</button>
            </form>
            <form class="action-form" method="post" action="/admin/contractors/{escape(contractor_id)}/reject">
                <button class="btn btn-red btn-sm" type="submit">Reject</button>
            </form>
        </div>
        """
        cells.append(f"<td>{actions_html}</td>")
        body_rows.append(f"<tr>{''.join(cells)}</tr>")

    return f"""
    <section class="card">
        <h2>Contractors ({len(contractors)})</h2>
        <p class="muted">Approve or reject contractor visibility here.</p>
        <div class="table-wrap">
            <table>
                <thead>
                    <tr>{header_html}</tr>
                </thead>
                <tbody>
                    {''.join(body_rows)}
                </tbody>
            </table>
        </div>
    </section>
    """


def display_service(contractor: Dict[str, Any]) -> str:
    return (
        str(contractor.get("service_type") or "").strip()
        or str(contractor.get("service") or "").strip()
        or "General Contractor"
    )


def display_location(contractor: Dict[str, Any]) -> str:
    city = str(contractor.get("city") or "").strip()
    state = str(contractor.get("state") or "").strip()
    zip_code = str(contractor.get("zip_code") or "").strip() or str(contractor.get("zip") or "").strip()

    first = ", ".join([part for part in [city, state] if part])
    if first and zip_code:
        return f"{first} {zip_code}"
    if zip_code:
        return zip_code
    return first or "Location not listed"


def display_business_name(contractor: Dict[str, Any]) -> str:
    return (
        str(contractor.get("business_name") or "").strip()
        or str(contractor.get("company_name") or "").strip()
        or "Unnamed Contractor"
    )


def contractor_card_html(contractor: Dict[str, Any]) -> str:
    business_name = display_business_name(contractor)
    contact_name = str(contractor.get("contact_name") or contractor.get("owner_name") or "").strip()
    service = display_service(contractor)
    location = display_location(contractor)
    phone = str(contractor.get("phone") or "").strip()
    email = str(contractor.get("email") or "").strip()
    bio = str(contractor.get("bio") or "").strip()
    website = str(contractor.get("website") or "").strip()
    approved = contractor.get("approved") is True

    badge = (
        '<span class="badge badge-approved">APPROVED</span>'
        if approved
        else '<span class="badge badge-pending">PENDING</span>'
    )

    rows = [
        f'<div class="meta-item"><span class="meta-label">Service:</span> {escape(service)}</div>',
        f'<div class="meta-item"><span class="meta-label">Location:</span> {escape(location)}</div>',
    ]

    if contact_name:
        rows.append(
            f'<div class="meta-item"><span class="meta-label">Contact:</span> {escape(contact_name)}</div>'
        )
    if phone:
        rows.append(
            f'<div class="meta-item"><span class="meta-label">Phone:</span> {escape(phone)}</div>'
        )
    if email:
        rows.append(
            f'<div class="meta-item"><span class="meta-label">Email:</span> {escape(email)}</div>'
        )
    if website:
        rows.append(
            f'<div class="meta-item"><span class="meta-label">Website:</span> {escape(website)}</div>'
        )
    if bio:
        rows.append(
            f'<div class="meta-item"><span class="meta-label">About:</span> {escape(bio)}</div>'
        )

    return f"""
    <article class="contractor-card">
        <div class="contractor-top">
            <h3 class="contractor-name">{escape(business_name)}</h3>
            {badge}
        </div>
        <div class="meta-list">
            {''.join(rows)}
        </div>
    </article>
    """


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    body = """
    <section class="hero">
        <h1>LeadForge</h1>
        <p>
            Browse local contractors, compare profiles, and rebuild the homeowner
            request flow from a stable live app.
        </p>
        <div class="nav-row">
            <a class="btn btn-primary" href="/contractors">Browse Contractors</a>
            <a class="btn btn-primary" href="/homeowner">Homeowner</a>
            <a class="btn btn-primary" href="/contractor-signup">Contractor Signup</a>
            <a class="btn btn-primary" href="/admin">Admin</a>
        </div>
    </section>

    <section class="card">
        <h2 class="section-title">Current Stable Step</h2>
        <p class="section-text">
            Contractor browse page is live, contractor signup includes acknowledgment,
            and admin approval buttons are back.
        </p>
    </section>
    """
    return page_shell("LeadForge", body)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/contractors", response_class=HTMLResponse)
def contractors_page() -> str:
    supabase = get_supabase()

    if supabase is None:
        body = """
        <section class="hero">
            <h1>Browse Contractors</h1>
            <p>Supabase is not connected.</p>
            <div class="nav-row">
                <a class="btn btn-primary" href="/">Homepage</a>
            </div>
        </section>
        """
        return page_shell("Browse Contractors - LeadForge", body)

    contractors = safe_fetch_table(supabase, "contractors")
    approved_contractors = [c for c in contractors if c.get("approved") is True]
    visible_contractors = approved_contractors if approved_contractors else contractors

    cards = "".join(contractor_card_html(contractor) for contractor in visible_contractors)

    if not cards:
        cards = """
        <div class="empty">
            <h2>No contractors available yet</h2>
            <p class="muted">Once contractors sign up, they will show here.</p>
        </div>
        """

    body = f"""
    <section class="hero">
        <h1>Browse Contractors</h1>
        <p>
            Homeowners can review contractor profiles here first. This page shows
            approved contractors first, or all contractors if none are approved yet.
        </p>
        <div class="nav-row">
            <a class="btn btn-primary" href="/">Homepage</a>
            <a class="btn btn-primary" href="/homeowner">Homeowner</a>
            <a class="btn btn-primary" href="/contractor-signup">Contractor Signup</a>
            <a class="btn btn-primary" href="/admin">Admin</a>
        </div>
    </section>

    <section class="stats">
        <div class="stat">
            <div class="stat-label">Visible on page</div>
            <div class="stat-value">{len(visible_contractors)}</div>
        </div>
        <div class="stat">
            <div class="stat-label">Approved contractors</div>
            <div class="stat-value">{len(approved_contractors)}</div>
        </div>
        <div class="stat">
            <div class="stat-label">Total contractors</div>
            <div class="stat-value">{len(contractors)}</div>
        </div>
    </section>

    <section class="cards-grid">
        {cards}
    </section>
    """
    return page_shell("Browse Contractors - LeadForge", body)


@app.get("/homeowner", response_class=HTMLResponse)
def homeowner_page() -> str:
    body = """
    <section class="hero">
        <h1>Homeowner</h1>
        <p>
            Step 1 is live: browse contractors. The homeowner request form will be
            reconnected next after we map the leads table exactly.
        </p>
        <div class="nav-row">
            <a class="btn btn-primary" href="/contractors">Browse Contractors</a>
            <a class="btn btn-primary" href="/">Homepage</a>
        </div>
    </section>

    <section class="card">
        <h2 class="section-title">What to do right now</h2>
        <p class="section-text">
            Homeowners can browse contractors first. Next step will be selecting one
            contractor and submitting one exclusive request.
        </p>
    </section>
    """
    return page_shell("Homeowner - LeadForge", body)


@app.get("/contractor-signup", response_class=HTMLResponse)
def contractor_signup_page() -> str:
    body = """
    <section class="hero">
        <h1>Contractor Signup</h1>
        <p>Simple stable contractor form connected to the backend.</p>
        <div class="nav-row">
            <a class="btn btn-primary" href="/">Homepage</a>
            <a class="btn btn-primary" href="/contractors">Browse Contractors</a>
            <a class="btn btn-primary" href="/admin">Admin</a>
        </div>
    </section>

    <section class="card">
        <form method="post" action="/contractor-signup">
            <div class="form-grid">
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
                    <input id="service" name="service" required>
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
                    <textarea id="bio" name="bio"></textarea>
                </div>

                <div class="full">
                    <label>Contractor Acknowledgment</label>
                    <div class="check-row">
                        <input id="agreement" name="agreement" type="checkbox" value="yes" required>
                        <label for="agreement">
                            I confirm the information I entered is accurate, and I understand
                            LeadForge may review my submission before approval.
                        </label>
                    </div>
                </div>

                <div class="full">
                    <button class="btn btn-dark" type="submit">Submit Contractor Signup</button>
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
    agreement: str = Form(...),
) -> str:
    supabase = get_supabase()

    if supabase is None:
        body = """
        <section class="card">
            <h1>Contractor Signup</h1>
            <div class="error">Supabase is not connected.</div>
            <a class="btn btn-dark" href="/contractor-signup">Back to Form</a>
        </section>
        """
        return page_shell("Contractor Signup Error - LeadForge", body)

    if agreement != "yes":
        body = """
        <section class="card">
            <h1>Contractor Signup</h1>
            <div class="error">You must accept the contractor acknowledgment to continue.</div>
            <a class="btn btn-dark" href="/contractor-signup">Back to Form</a>
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
            <div class="error">{escape(message)}</div>
            <a class="btn btn-dark" href="/contractor-signup">Back to Form</a>
        </section>
        """
        return page_shell("Contractor Signup Error - LeadForge", body)

    body = f"""
    <section class="card">
        <h1>Contractor Signup Submitted</h1>
        <div class="success">Your contractor profile was submitted successfully.</div>
        <p><strong>Business:</strong> {escape(business_name)}</p>
        <p><strong>Service:</strong> {escape(service)}</p>
        <p><strong>Location:</strong> {escape(city)}, {escape(state)} {escape(zip_code)}</p>
        <div class="nav-row">
            <a class="btn btn-dark" href="/contractors">Browse Contractors</a>
            <a class="btn btn-gray" href="/admin">Admin</a>
            <a class="btn btn-gray" href="/">Homepage</a>
        </div>
    </section>
    """
    return page_shell("Contractor Signup Submitted - LeadForge", body)


@app.post("/admin/contractors/{contractor_id}/approve")
def approve_contractor(contractor_id: str):
    supabase = get_supabase()
    if supabase is not None:
        safe_update_record(supabase, "contractors", contractor_id, {"approved": True})
    return RedirectResponse(url="/admin", status_code=303)


@app.post("/admin/contractors/{contractor_id}/reject")
def reject_contractor(contractor_id: str):
    supabase = get_supabase()
    if supabase is not None:
        safe_update_record(supabase, "contractors", contractor_id, {"approved": False})
    return RedirectResponse(url="/admin", status_code=303)


@app.get("/contractors/data")
def contractors_data() -> JSONResponse:
    supabase = get_supabase()

    if supabase is None:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": "Supabase is not connected."},
        )

    contractors = safe_fetch_table(supabase, "contractors")
    return JSONResponse(content={"ok": True, "contractors": contractors})


@app.get("/admin", response_class=HTMLResponse)
def admin_page() -> str:
    supabase = get_supabase()

    if supabase is None:
        body = """
        <section class="card">
            <h1>LeadForge Admin</h1>
            <div class="error">Supabase is not connected.</div>
            <a class="btn btn-dark" href="/">Homepage</a>
        </section>
        """
        return page_shell("LeadForge Admin", body)

    contractors = safe_fetch_table(supabase, "contractors")
    leads = safe_fetch_table(supabase, "leads")

    body = f"""
    <section class="hero">
        <h1>LeadForge Admin</h1>
        <p>Approval buttons are restored here while contractor browse stays live.</p>
        <div class="nav-row">
            <a class="btn btn-primary" href="/">Homepage</a>
            <a class="btn btn-primary" href="/contractors">Browse Contractors</a>
            <a class="btn btn-primary" href="/contractor-signup">Contractor Signup</a>
        </div>
    </section>

    {build_contractor_admin_table(contractors)}
    {build_admin_table("Leads", leads)}
    """
    return page_shell("LeadForge Admin", body)


@app.get("/admin/data")
def admin_data() -> JSONResponse:
    supabase = get_supabase()

    if supabase is None:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": "Supabase is not connected."},
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
