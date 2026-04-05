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
    <a href="/contractors">Browse Contractors</a><br>
    <a href="/contractor-signup">Join</a><br>
    <a href="/admin">Admin</a><br>
    <a href="/health">Health</a>
    """


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/contractors", response_class=HTMLResponse)
def contractors():
    contractor_cards = ""

    if supabase:
        contractors = supabase.table("contractors").select("*").eq("approved", True).execute().data
    else:
        contractors = []

    if contractors:
        for c in contractors:
            contractor_cards += f"""
            <div style='border:1px solid #ccc;padding:16px;margin:12px;border-radius:10px;'>
                <h2>{c.get("business_name","")}</h2>
                <p><b>Service:</b> {c.get("service","")}</p>
                <p><b>City:</b> {c.get("city","")}</p>
                <a href="/request/{c.get("id")}">Request Quote</a>
            </div>
            """
    else:
        contractor_cards = "<p>No approved contractors yet</p>"

    return f"<h1>Browse Contractors</h1>{contractor_cards}<a href='/'>Back</a>"


@app.get("/request/{contractor_id}", response_class=HTMLResponse)
def request_page(contractor_id: str):
    contractor_name = "Contractor"

    if supabase:
        result = supabase.table("contractors").select("*").eq("id", contractor_id).execute().data
        if result:
            contractor_name = result[0].get("business_name", "Contractor")

    return f"""
    <h1>Request Service</h1>
    <h2>{contractor_name}</h2>

    <form>
        <input type="text" placeholder="Your Name"><br><br>
        <input type="text" placeholder="Phone"><br><br>
        <input type="text" placeholder="City"><br><br>
        <textarea placeholder="Describe your project"></textarea><br><br>

        <button type="button">Submit Request</button>
    </form>

    <br><a href="/contractors">Back</a>
    """


@app.get("/admin", response_class=HTMLResponse)
def admin():
    contractors_html = ""

    if supabase:
        contractors = supabase.table("contractors").select("*").execute().data
    else:
        contractors = []

    for c in contractors:
        contractor_id = c.get("id")

        contractors_html += f"""
        <div style='border:1px solid #ccc;padding:12px;margin:10px;'>
            <b>{c.get("business_name","")}</b><br>
            Approved: {c.get("approved","")}<br>
            <a href="/approve/{contractor_id}">Approve</a> |
            <a href="/reject/{contractor_id}">Reject</a>
        </div>
        """

    return f"<h1>Admin</h1>{contractors_html}<a href='/'>Back</a>"


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
