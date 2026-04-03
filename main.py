from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
