from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client
from datetime import datetime
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

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Missing SUPABASE_URL or SUPABASE_KEY environment variables")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


@app.get("/")
def root():
    return {"message": "API WORKING"}


@app.get("/admin")
def get_all_contractors():
    result = supabase.table("contractors").select("*").execute()
    return {"success": True, "data": result.data}


@app.get("/contractors")
def get_approved_contractors():
    result = (
        supabase
        .table("contractors")
        .select("*")
        .eq("status", "approved")
        .execute()
    )
    return {"success": True, "data": result.data}


@app.post("/contractors")
async def create_contractor(request: Request):
    data = await request.json()

    payload = {
        "first_name": data.get("first_name") or "",
        "last_name": data.get("last_name") or "",
        "business_name": data.get("business_name") or "",
        "email": data.get("email") or "",
        "phone": data.get("phone") or "",
        "trade": data.get("trade") or "",
        "service_area": data.get("service_area") or "",
        "experience_years": data.get("experience_years") or "",
        "license_number": data.get("license_number") or "",
        "insured": data.get("insured") if data.get("insured") is not None else False,
        "agreed_to_terms": data.get("agreed_to_terms") if data.get("agreed_to_terms") is not None else False,
        "agreement_version": data.get("agreement_version") or "v1.0",
        "agreement_timestamp": datetime.utcnow().isoformat(),
        "status": "pending"
    }

    supabase.table("contractors").insert(payload).execute()
    return {"success": True}


@app.post("/contractors/approve/{contractor_id}")
def approve_contractor(contractor_id: str):
    result = (
        supabase
        .table("contractors")
        .update({"status": "approved"})
        .eq("id", contractor_id)
        .execute()
    )
    return {"success": True, "data": result.data}


@app.post("/contractors/reject/{contractor_id}")
def reject_contractor(contractor_id: str):
    result = (
        supabase
        .table("contractors")
        .update({"status": "rejected"})
        .eq("id", contractor_id)
        .execute()
    )
    return {"success": True, "data": result.data}


@app.post("/leads")
async def create_lead(request: Request):
    data = await request.json()

    payload = {
        "name": data.get("name") or "",
        "phone": data.get("phone") or "",
        "email": data.get("email") or "",
        "city": data.get("city") or "",
        "state": data.get("state") or "",
        "zip_code": data.get("zip_code") or "",
        "service": data.get("service") or "",
        "project_details": data.get("project_details") or "",
        "created_at": datetime.utcnow().isoformat()
    }

    supabase.table("leads").insert(payload).execute()
    return {"success": True}
