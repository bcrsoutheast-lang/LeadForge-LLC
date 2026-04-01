from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client
from datetime import datetime
import os

app = FastAPI()

# CORS (allow frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Missing Supabase env vars")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -----------------------------
# HEALTH
# -----------------------------
@app.get("/")
def root():
    return {"message": "API WORKING"}

@app.get("/health")
def health():
    return {"status": "ok"}

# -----------------------------
# GET ALL CONTRACTORS
# -----------------------------
@app.get("/contractors")
def get_contractors():
    res = supabase.table("contractors").select("*").execute()
    return res.data

# -----------------------------
# GET APPROVED CONTRACTORS
# -----------------------------
@app.get("/contractors/approved")
def get_approved_contractors():
    res = (
        supabase
        .table("contractors")
        .select("*")
        .eq("approved", True)
        .execute()
    )
    return res.data

# -----------------------------
# GET SINGLE CONTRACTOR (UUID FIX)
# -----------------------------
@app.get("/contractors/{contractor_id}")
def get_contractor(contractor_id: str):
    res = (
        supabase
        .table("contractors")
        .select("*")
        .eq("id", contractor_id)
        .single()
        .execute()
    )
    return res.data

# -----------------------------
# APPROVE CONTRACTOR (FIXED)
# -----------------------------
@app.post("/contractors/approve/{contractor_id}")
def approve_contractor(contractor_id: str):
    res = (
        supabase
        .table("contractors")
        .update({
            "status": "approved",
            "approved": True
        })
        .eq("id", contractor_id)
        .execute()
    )

    return {
        "message": "approved",
        "id": contractor_id
    }

# -----------------------------
# REJECT CONTRACTOR
# -----------------------------
@app.post("/contractors/reject/{contractor_id}")
def reject_contractor(contractor_id: str):
    supabase.table("contractors").delete().eq("id", contractor_id).execute()
    return {"message": "rejected"}

# -----------------------------
# CREATE LEAD (FIXED)
# -----------------------------
@app.post("/leads")
async def create_lead(request: Request):
    data = await request.json()

    contractor_id = data.get("contractor_id")
    email = data.get("email")
    phone = data.get("phone")

    if not contractor_id:
        return {"detail": "Missing contractor_id"}

    # 🚫 BLOCK duplicates
    existing = (
        supabase
        .table("leads")
        .select("*")
        .eq("contractor_id", contractor_id)
        .eq("email", email)
        .execute()
    )

    if existing.data:
        return {"detail": "You already submitted a request"}

    # ✅ Insert lead
    insert = supabase.table("leads").insert({
        "contractor_id": contractor_id,
        "name": data.get("name"),
        "email": email,
        "phone": phone,
        "city": data.get("city"),
        "state": data.get("state"),
        "zip": data.get("zip"),
        "details": data.get("details"),
        "created_at": datetime.utcnow().isoformat()
    }).execute()

    return {"message": "Lead created"}
