from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse
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

supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <h1>LeadForge</h1>
    <a href="/contractors">Contractors</a><br>
    <a href="/contractor-signup">Join</a><br>
    <a href="/admin">Admin</a><br>
    <a href="/health">Health</a>
    """


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/admin", response_class=HTMLResponse)
def admin():
    contractors_html = ""
    leads_html = ""

    if supabase:
        try:
            contractors = supabase.table("contractors").select("*").execute().data
        except:
            contractors = []

        try:
            leads = supabase.table("leads").select("*").execute().data
        except:
            leads = []
    else:
        contractors = []
        leads = []

    # Contractors
    if contractors:
        for c in contractors:
            contractor_id = c.get("id")

            contractors_html += f"""
            <div style='border:1px solid #ccc;padding:12px;margin:10px;'>
                <b>{c.get("business_name","No Name")}</b><br>
                Service: {c.get("service","")}<br>
                City: {c.get("city","")}<br>
                Approved: {c.get("approved","")}<br><br>

                <a href="/approve/{contractor_id}">✅ Approve</a> |
                <a href="/reject/{contractor_id}">❌ Reject</a>
            </div>
            """
    else:
        contractors_html = "<p>No contractors found</p>"

    # Leads
    if leads:
        for l in leads:
            leads_html += f"""
            <div style='border:1px solid #ccc;padding:12px;margin:10px;'>
                <b>{l.get("owner_name","")}</b><br>
                Service: {l.get("service","")}<br>
                City: {l.get("city","")}
            </div>
            """
    else:
        leads_html = "<p>No leads found</p>"

    return f"""
    <h1>Admin Dashboard</h1>

    <h2>Contractors</h2>
    {contractors_html}

    <h2>Leads</h2>
    {leads_html}

    <br><a href="/">Back</a>
    """


@app.get("/approve/{contractor_id}")
def approve(contractor_id: str):
    if supabase:
        supabase.table("contractors").update({"approved": True}).eq("id", contractor_id).execute()
    return RedirectResponse("/admin")


@app.get("/reject/{contractor_id}")
def reject(contractor_id: str):
    if supabase:
        supabase.table("contractors").update({"approved": False}).eq("id", contractor_id).execute()
    return RedirectResponse("/admin")
