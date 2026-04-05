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
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

    if not url or not key:
        return None

    try:
        return create_client(url, key)
    except Exception:
        return None


def safe_fetch_table(supabase: Client, table: str):
    try:
        res = supabase.table(table).select("*").execute()
        return res.data or []
    except:
        return []


def safe_insert(supabase: Client, table: str, payload: dict):
    try:
        supabase.table(table).insert(payload).execute()
        return True, ""
    except Exception as e:
        return False, str(e)


# ---------- HOME ----------

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <h1>LeadForge</h1>
    <a href="/homeowner">Homeowner</a><br><br>
    <a href="/contractor-signup">Contractor Signup</a><br><br>
    <a href="/admin">Admin</a>
    """


@app.get("/health")
def health():
    return {"status": "ok"}


# ---------- HOMEOWNER ----------

@app.get("/homeowner", response_class=HTMLResponse)
def homeowner():
    supabase = get_supabase()
    contractors = safe_fetch_table(supabase, "contractors")

    options = ""
    for c in contractors:
        options += f'<option value="{c.get("id")}">{c.get("business_name")}</option>'

    return f"""
    <h1>Homeowner Request</h1>

    <form method="post">
        Name:<br><input name="owner_name"><br>
        Phone:<br><input name="phone"><br>
        Service:<br><input name="service"><br>
        City:<br><input name="city"><br>
        State:<br><input name="state"><br>
        Zip:<br><input name="zip_code"><br>

        Contractor:<br>
        <select name="contractor_id">
            {options}
        </select><br><br>

        Details:<br>
        <textarea name="project_details"></textarea><br><br>

        <button type="submit">Submit</button>
    </form>
    """


@app.post("/homeowner", response_class=HTMLResponse)
def homeowner_submit(
    owner_name: str = Form(...),
    phone: str = Form(...),
    service: str = Form(...),
    city: str = Form(...),
    state: str = Form(...),
    zip_code: str = Form(...),
    contractor_id: str = Form(...),
    project_details: str = Form(...),
):
    supabase = get_supabase()

    payload = {
        "owner_name": owner_name,
        "phone": phone,
        "service": service,
        "city": city,
        "state": state,
        "zip_code": zip_code,
        "project_details": project_details,
        "contractor_id": contractor_id,
    }

    ok, msg = safe_insert(supabase, "leads", payload)

    if not ok:
        return f"<h2>Error:</h2><pre>{msg}</pre>"

    return "<h2>Submitted successfully</h2><a href='/admin'>Go to admin</a>"


# ---------- CONTRACTOR ----------

@app.get("/contractor-signup", response_class=HTMLResponse)
def contractor_page():
    return """
    <h1>Contractor Signup</h1>
    <form method="post">
        Business:<br><input name="business_name"><br>
        Contact:<br><input name="contact_name"><br>
        Email:<br><input name="email"><br>
        Phone:<br><input name="phone"><br>
        Service:<br><input name="service"><br>
        City:<br><input name="city"><br>
        State:<br><input name="state"><br>
        Zip:<br><input name="zip_code"><br><br>
        <button type="submit">Submit</button>
    </form>
    """


@app.post("/contractor-signup")
def contractor_submit(
    business_name: str = Form(...),
    contact_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    service: str = Form(...),
    city: str = Form(...),
    state: str = Form(...),
    zip_code: str = Form(...),
):
    supabase = get_supabase()

    payload = {
        "business_name": business_name,
        "contact_name": contact_name,
        "email": email,
        "phone": phone,
        "service": service,
        "city": city,
        "state": state,
        "zip_code": zip_code,
    }

    ok, msg = safe_insert(supabase, "contractors", payload)

    if not ok:
        return f"<h2>Error:</h2><pre>{msg}</pre>"

    return "<h2>Contractor saved</h2><a href='/admin'>Admin</a>"


# ---------- ADMIN ----------

@app.get("/admin", response_class=HTMLResponse)
def admin():
    supabase = get_supabase()

    contractors = safe_fetch_table(supabase, "contractors")
    leads = safe_fetch_table(supabase, "leads")

    return f"""
    <h1>Admin</h1>

    <h2>Contractors</h2>
    <pre>{contractors}</pre>

    <h2>Leads</h2>
    <pre>{leads}</pre>
    """
