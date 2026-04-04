from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
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

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def safe(value):
    if value is None:
        return ""
    return str(value)


@app.get("/")
def root():
    return {"message": "API WORKING"}


@app.post("/contractors")
async def create_contractor(data: dict):
    try:
        response = supabase.table("contractors").insert({
            "contact_name": data.get("name"),
            "business_name": data.get("business"),
            "trade": data.get("service"),
            "service_area": data.get("location"),
            "phone": data.get("phone"),
            "email": data.get("email"),
            "notes": data.get("about"),
            "approved": False
        }).execute()

        return {
            "success": True,
            "data": response.data
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/contractors")
def get_contractors():
    try:
        response = supabase.table("contractors").select("*").execute()
        return response.data or []
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.post("/leads")
async def create_lead(data: dict):
    try:
        payload = {
            "name": data.get("name"),
            "phone": data.get("phone"),
            "email": data.get("email"),
            "city": data.get("city"),
            "state": data.get("state"),
            "zip_code": data.get("zip_code"),
            "service": data.get("service"),
            "project_details": data.get("project_details"),
            "contractor_id": data.get("contractor_id"),
            "contractor_name": data.get("contractor_name"),
        }

        response = supabase.table("leads").insert(payload).execute()

        return {
            "success": True,
            "saved_payload": payload,
            "data": response.data
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/admin", response_class=HTMLResponse)
def admin():
    try:
        contractors_response = supabase.table("contractors").select("*").execute()
        leads_response = supabase.table("leads").select("*").execute()

        contractors = contractors_response.data or []
        leads = leads_response.data or []

        contractor_lookup = {}
        for c in contractors:
            contractor_lookup[str(c.get("id"))] = c.get("business_name") or ""

        contractor_rows = ""
        for c in contractors:
            contractor_rows += f"""
            <tr>
                <td>{safe(c.get('business_name'))}</td>
                <td>{safe(c.get('contact_name'))}</td>
                <td>{safe(c.get('phone'))}</td>
                <td>{safe(c.get('email'))}</td>
                <td>{safe(c.get('trade'))}</td>
                <td>{safe(c.get('service_area'))}</td>
                <td>{safe(c.get('approved'))}</td>
            </tr>
            """

        lead_rows = ""
        for l in leads:
            contractor_id = safe(l.get("contractor_id"))
            chosen_contractor = safe(l.get("contractor_name"))

            if not chosen_contractor and contractor_id:
                chosen_contractor = contractor_lookup.get(contractor_id, "")

            city = safe(l.get("city"))
            state = safe(l.get("state"))
            zip_code = safe(l.get("zip_code"))

            location_parts = [part for part in [city, state] if part]
            location = ", ".join(location_parts)
            if zip_code:
                location = f"{location} {zip_code}".strip()

            lead_rows += f"""
            <tr>
                <td>{safe(l.get('name'))}</td>
                <td>{safe(l.get('phone'))}</td>
                <td>{safe(l.get('email'))}</td>
                <td>{location}</td>
                <td>{safe(l.get('service'))}</td>
                <td>{safe(l.get('project_details'))}</td>
                <td>{chosen_contractor}</td>
                <td>{contractor_id}</td>
            </tr>
            """

        return f"""
        <html>
        <head>
            <title>LeadForge Admin</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    padding: 20px;
                    background: #f5f5f5;
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
                    padding: 10px;
                    font-size: 14px;
                    vertical-align: top;
                    text-align: left;
                }}
                th {{
                    background: #111;
                    color: white;
                }}
            </style>
        </head>
        <body>
            <h1>LeadForge Admin Dashboard</h1>

            <h2>Contractor Applications</h2>
            <table>
                <tr>
                    <th>Business</th>
                    <th>Contact</th>
                    <th>Phone</th>
                    <th>Email</th>
                    <th>Trade</th>
                    <th>Area</th>
                    <th>Approved</th>
                </tr>
                {contractor_rows}
            </table>

            <h2>Homeowner Leads</h2>
            <table>
                <tr>
                    <th>Homeowner</th>
                    <th>Phone</th>
                    <th>Email</th>
                    <th>Location</th>
                    <th>Service</th>
                    <th>Project Details</th>
                    <th>Chosen Contractor</th>
                    <th>Contractor ID</th>
                </tr>
                {lead_rows}
            </table>
        </body>
        </html>
        """

    except Exception as e:
        return f"Error: {str(e)}"
