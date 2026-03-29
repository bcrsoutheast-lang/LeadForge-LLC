from fastapi import FastAPI
from pydantic import BaseModel
import uuid

app = FastAPI()

LEADS = []

class Lead(BaseModel):
    name: str
    phone: str
    city: str
    service: str

@app.get("/")
def home():
    return {"message": "LeadForge API is live"}

def score(service: str):
    s = service.lower()
    sc = 10
    if "roof" in s:
        sc += 50
    if "hvac" in s:
        sc += 45
    if "plumb" in s:
        sc += 40
    if "emergency" in s:
        sc += 20
    if "repair" in s:
        sc += 15
    return min(sc, 100)

def tier(sc):
    if sc >= 80:
        return "HOT"
    if sc >= 50:
        return "WARM"
    return "COLD"

@app.post("/lead")
def create_lead(l: Lead):
    item = l.dict()
    item["id"] = str(uuid.uuid4())
    item["score"] = score(item["service"])
    item["tier"] = tier(item["score"])
    LEADS.append(item)
    return item

@app.get("/leads")
def get_leads():
    return sorted(LEADS, key=lambda x: x["score"], reverse=True)
