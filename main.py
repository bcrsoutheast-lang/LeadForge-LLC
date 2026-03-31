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

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


@app.get("/")
def root():
    return {"message": "LeadForge API is running"}


@app.post("/leads")
def create_lead(lead: dict):
    try:
        response = supabase.table("leads").insert(lead).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating lead: {str(e)}")


@app.get("/leads")
def get_leads():
    try:
        response = supabase.table("leads").select("*").execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching leads: {str(e)}")


@app.post("/contractors")
def create_contractor(contractor: dict):
    try:
        contractor.setdefault("status", "pending")
        contractor.setdefault("verified", False)
        response = supabase.table("contractors").insert(contractor).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating contractor: {str(e)}")


@app.get("/contractors")
def get_contractors():
    try:
        response = supabase.table("contractors").select("*").execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching contractors: {str(e)}")


@app.post("/contractors/approve/{contractor_id}")
def approve_contractor(contractor_id: str):
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
    try:
        leads_response = supabase.table("leads").select("*").execute()
        contractors_response = supabase.table("contractors").select("*").execute()

        return {
            "leads": leads_response.data,
            "contractors": contractors_response.data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading admin dashboard: {str(e)}")
