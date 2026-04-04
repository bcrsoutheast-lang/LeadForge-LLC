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

        return {"success": True, "data": response.data}

    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/contractors")
def get_contractors():
    try:
        response = supabase.table("contractors").select("*").execute()
        return response.data
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/leads")
async def create_lead(data: dict):
    try:
        response = supabase.table("leads").insert({
            "name": data.get("name"),
            "phone": data.get("phone"),
            "email": data.get("email"),
            "city": data.get("city"),
            "state": data.get("state"),
            "zip_code": data.get("zip_code"),
            "service": data.get("service"),
            "project_details": data.get("project_details"),
            "contractor_id": data.get("contractor_id"),
            "contractor_name": data.get("contractor_name")
        }).execute()

        return {"success": True, "data": response.data}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/admin", response_class=HTMLResponse)
def admin():
    try:
        contractors_response = supabase.table("contractors").select("*").execute()
        leads_response = supabase.table("leads").select("*").execute()

        contractors = contractors_response.data or []
        leads = leads_response.data or []

        contractor_rows = ""
        for c in contractors:
            contractor_rows += f"""
            <tr>
                <td>{c.get('business_name','')}</td>
                <td>{c.get('contact_name','')}</td>
                <td>{c.get('phone','')}</td>
                <td>{c.get('email','')}</td>
                <td>{c.get('trade','')}</td>
                <td>{c.get('service_area','')}</td>
                <td>{c.get('approved','')}</td>
            </tr>
            """

        lead_rows = ""
        for l in leads:
            lead_rows += f"""
            <tr>
                <td>{l.get('name','')}</td>
                <td>{l.get('phone','')}</td>
                <td>{l.get('email','')}</td>
                <td>{l.get('city','')}, {l.get('state','')} {l.get('zip_code','')}</td>
                <td>{l.get('service','')}</td>
                <td>{l.get('project_details','')}</td>
                <td>{l.get('contractor_name','')}</td>
                <td>{l.get('contractor_id','')}</td>
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
