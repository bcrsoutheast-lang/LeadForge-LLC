from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Lead(BaseModel):
    name: str
    phone: str
    email: str
    service: Optional[str] = None
    zip_code: Optional[str] = None
    notes: Optional[str] = None

@app.get("/")
def root():
    return {"status": "LeadForge backend running"}

@app.post("/leads")
async def create_lead(lead: Lead):
    return {
        "success": True,
        "message": "Lead received",
        "data": lead.dict()
    }
