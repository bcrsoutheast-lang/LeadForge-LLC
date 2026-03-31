from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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


def get_supabase():
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        raise Exception("Missing SUPABASE_URL or SUPABASE_KEY environment variables")

    return create_client(supabase_url, supabase_key)


@app.get("/")
def root():
    return {"message": "API WORKING"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/admin")
def get_all_contractors():
    try:
        supabase = get_supabase()
        result = supabase.table("contractors").select("*").execute()
        return {"success": True, "data": result.data}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "route": "/admin", "error": str(e)}
        )


@app.get("/contractors")
def get_approved_contractors():
    try:
        supabase = get_supabase()
        result = (
            supabase
            .table("contractors")
            .select("*")
            .eq("status", "approved")
            .execute()
        )
        return {"success": True, "data": result.data}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "route": "/contractors", "error": str(e)}
        )


@app.post("/contractors")
async def create_contractor(request: Request):
    try:
        supabase = get_supabase()
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

        result = supabase.table("contractors").insert(payload).execute()
        return {"success": True, "data": result.data}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "route": "/contractors POST", "error": str(e)}
        )


@app.post("/contractors/approve/{contractor_id}")
def approve_contractor(contractor_id: str):
    try:
        supabase = get_supabase()
        result = (
            supabase
            .table("contractors")
            .update({"status": "approved"})
            .eq("id", contractor_id)
            .execute()
        )
        return {"success": True, "data": result.data}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "route": "/contractors/approve", "error": str(e)}
        )


@app.post("/contractors/reject/{contractor_id}")
def reject_contractor(contractor_id: str):
    try:
        supabase = get_supabase()
        result = (
            supabase
            .table("contractors")
            .update({"status": "rejected"})
            .eq("id", contractor_id)
            .execute()
        )
        return {"success": True, "data": result.data}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "route": "/contractors/reject", "error": str(e)}
        )


@app.post("/leads")
async def create_lead(request: Request):
    try:
        supabase = get_supabase()
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

        result = supabase.table("leads").insert(payload).execute()
        return {"success": True, "data": result.data}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "route": "/leads", "error": str(e)}
        )
