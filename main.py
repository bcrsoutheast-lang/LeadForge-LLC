from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

leads_db = []

class Lead(BaseModel):
    name: str
    phone: str
    email: str
    city: str
    state: str
    zip_code: str
    service: str
    project_details: str

@app.get("/")
def root():
    return {"message": "API is live"}

@app.post("/leads")
def create_lead(lead: Lead):
    leads_db.append(lead.dict())
    return {"success": True, "message": "Lead received", "data": lead}

@app.get("/leads")
def get_leads():
    return leads_db

# 🔥 NEW: Admin dashboard
@app.get("/admin", response_class=HTMLResponse)
def admin():
    html = """
    <html>
    <head>
        <title>LeadForge Dashboard</title>
        <style>
            body { font-family: Arial; padding: 20px; }
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #ccc; padding: 8px; }
            th { background: #eee; }
        </style>
    </head>
    <body>
        <h1>Leads Dashboard</h1>
        <table>
            <tr>
                <th>Name</th>
                <th>Phone</th>
                <th>Email</th>
                <th>City</th>
                <th>State</th>
                <th>Zip</th>
                <th>Service</th>
                <th>Project</th>
            </tr>
    """

    for lead in leads_db:
        html += f"""
        <tr>
            <td>{lead['name']}</td>
            <td>{lead['phone']}</td>
            <td>{lead['email']}</td>
            <td>{lead['city']}</td>
            <td>{lead['state']}</td>
            <td>{lead['zip_code']}</td>
            <td>{lead['service']}</td>
            <td>{lead['project_details']}</td>
        </tr>
        """

    html += """
        </table>
    </body>
    </html>
    """

    return html
