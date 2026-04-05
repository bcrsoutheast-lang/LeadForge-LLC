from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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

templates = Jinja2Templates(directory="templates")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

supabase: Client | None = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# -----------------------------
# Models
# -----------------------------
class ContractorCreate(BaseModel):
    company_name: str
    contact_name: str
    phone: str
    email: str
    service_type: str


class LeadCreate(BaseModel):
    homeowner_name: str
    phone: str
    service: str
    project_details: str
    contractor_id: str


# -----------------------------
# Pages
# -----------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/homeowner", response_class=HTMLResponse)
def homeowner(request: Request):
    return templates.TemplateResponse("homeowner.html", {"request": request})


@app.get("/contractor-signup", response_class=HTMLResponse)
def contractor_signup():
    return HTMLResponse("""
        <html>
            <body>
                <h1>Contractor Signup</h1>
                <p>Form connected to backend.</p>
                <a href="/">Back</a>
            </body>
        </html>
    """)


@app.get("/health")
def health():
    return {"status": "ok"}


# -----------------------------
# Contractors
# -----------------------------
@app.get("/contractors")
def get_contractors():
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    result = supabase.table("contractors").select("*").eq("approved", True).execute()
    return result.data or []


@app.post("/contractors")
def create_contractor(contractor: ContractorCreate):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    data = contractor.dict()
    data["approved"] = False

    result = supabase.table("contractors").insert(data).execute()
    return result.data


# -----------------------------
# Leads
# -----------------------------
@app.post("/leads")
def create_lead(lead: LeadCreate):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    data = lead.dict()
    data["unlocked"] = False

    result = supabase.table("leads").insert(data).execute()
    return result.data


# -----------------------------
# Admin
# -----------------------------
@app.get("/admin", response_class=HTMLResponse)
def admin():
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    contractors = supabase.table("contractors").select("*").execute().data or []
    leads = supabase.table("leads").select("*").execute().data or []

    return HTMLResponse(f"""
        <html>
            <body>
                <h1>Admin</h1>

                <h2>Contractors</h2>
                <pre>{contractors}</pre>

                <h2>Leads</h2>
                <pre>{leads}</pre>
            </body>
        </html>
    """)
