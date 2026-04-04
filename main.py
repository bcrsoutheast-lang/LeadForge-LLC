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
        response = supabase.table("contractors").select("*").execute()
        contractors = response.data

        rows = ""
        for c in contractors:
            rows += f"""
            <tr>
                <td>{c.get('business_name','')}</td>
                <td>{c.get('contact_name','')}</td>
                <td>{c.get('phone','')}</td>
                <td>{c.get('email','')}</td>
                <td>{c.get('trade','')}</td>
                <td>{c.get('service_area','')}</td>
            </tr>
            """

        return f"""
        <html>
        <body style="font-family:Arial;padding:20px;">
            <h1>Contractor Applications</h1>
            <table border="1" cellpadding="10">
                <tr>
                    <th>Business</th>
                    <th>Contact</th>
                    <th>Phone</th>
                    <th>Email</th>
                    <th>Trade</th>
                    <th>Area</th>
                </tr>
                {rows}
            </table>
        </body>
        </html>
        """

    except Exception as e:
        return f"Error: {str(e)}"
