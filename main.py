from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

leads_db = []

class Lead(BaseModel):
    name: str
    phone: str
    email: str
    city: str
    service: str

@app.get("/")
def root():
    return {"message": "API is live"}

@app.post("/leads")
def create_lead(lead: Lead):
    leads_db.append(lead.dict())
    return {
        "success": True,
        "message": "Lead received",
        "data": lead
    }

@app.get("/leads")
def get_leads():
    return leads_db
