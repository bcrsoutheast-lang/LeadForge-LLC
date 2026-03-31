from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔥 NEW VARIABLES (bypass broken ones)
SUPABASE_URL = (os.getenv("SB_URL") or "").strip()
SUPABASE_KEY = (os.getenv("SB_KEY") or "").strip()

supabase = None
supabase_error = None

try:
    if not SUPABASE_URL:
        raise RuntimeError("SB_URL missing")
    if not SUPABASE_KEY:
        raise RuntimeError("SB_KEY missing")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    supabase_error = str(e)


@app.get("/")
def root():
    return {"message": "LeadForge API is running"}


@app.get("/debug-env")
def debug_env():
    return {
        "supabase_url": SUPABASE_URL,
        "url_starts_https": SUPABASE_URL.startswith("https://"),
        "url_ends_supabase": SUPABASE_URL.endswith(".supabase.co"),
        "url_length": len(SUPABASE_URL),
        "key_present": bool(SUPABASE_KEY),
        "key_length": len(SUPABASE_KEY),
        "client_init_error": supabase_error,
    }


@app.post("/leads")
def create_lead(lead: dict):
    if not supabase:
        raise HTTPException(status_code=500, detail=f"Supabase not initialized: {supabase_error}")

    try:
        response = supabase.table("leads").insert(lead).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating lead: {str(e)}")


@app.get("/leads")
def get_leads():
    if not supabase:
        raise HTTPException(status_code=500, detail=f"Supabase not initialized: {supabase_error}")

    try:
        response = supabase.table("leads").select("*").execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching leads: {str(e)}")


@app.post("/contractors")
def create_contractor(contractor: dict):
    if not supabase:
        raise HTTPException(status_code=500, detail=f"Supabase not initialized: {supabase_error}")

    try:
        contractor.setdefault("status", "pending")
        contractor.setdefault("verified", False)
        response = supabase.table("contractors").insert(contractor).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating contractor: {str(e)}")


@app.get("/contractors")
def get_contractors():
    if not supabase:
        raise HTTPException(status_code=500, detail=f"Supabase not initialized: {supabase_error}")

    try:
        response = supabase.table("contractors").select("*").execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching contractors: {str(e)}")


@app.post("/contractors/approve/{contractor_id}")
def approve_contractor(contractor_id: str):
    if not supabase:
        raise HTTPException(status_code=500, detail=f"Supabase not initialized: {supabase_error}")

    try:
        response = (
            supabase.table("contractors")
            .update({"status": "approved", "verified": True})
            .eq("id", contractor_id)
            .execute()
        )
        return {"message": "Contractor approved", "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error approving contractor: {str(e)}")


@app.post("/contractors/reject/{contractor_id}")
def reject_contractor(contractor_id: str):
    if not supabase:
        raise HTTPException(status_code=500, detail=f"Supabase not initialized: {supabase_error}")

    try:
        response = (
            supabase.table("contractors")
            .update({"status": "rejected", "verified": False})
            .eq("id", contractor_id)
            .execute()
        )
        return {"message": "Contractor rejected", "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rejecting contractor: {str(e)}")


@app.get("/admin")
def admin_dashboard():
    if not supabase:
        raise HTTPException(status_code=500, detail=f"Supabase not initialized: {supabase_error}")

    try:
        leads_response = supabase.table("leads").select("*").execute()
        contractors_response = supabase.table("contractors").select("*").execute()
        return {
            "leads": leads_response.data,
            "contractors": contractors_response.data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading admin dashboard: {str(e)}")
