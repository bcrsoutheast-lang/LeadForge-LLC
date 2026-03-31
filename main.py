from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os
from supabase import create_client
from datetime import datetime

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
    return {"message": "API running"}


@app.post("/contractors")
async def create_contractor(request: Request):
    data = await request.json()

    payload = {
        "first_name": data.get("first_name"),
        "last_name": data.get("last_name"),
        "business_name": data.get("business_name"),
        "email": data.get("email"),
        "phone": data.get("phone"),
        "trade": data.get("trade"),
        "service_area": data.get("service_area"),
        "experience_years": data.get("experience_years"),
        "license_number": data.get("license_number"),
        "insured": data.get("insured"),
        "agreed_to_terms": data.get("agreed_to_terms"),
        "agreement_version": data.get("agreement_version"),
        "agreement_timestamp": datetime.utcnow().isoformat(),
        "status": "pending"
    }

    supabase.table("contractors").insert(payload).execute()

    return {"success": True}
