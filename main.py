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

# -----------------------
# DATABASE (temporary)
# -----------------------
leads_db = []
contractors_db = []

# -----------------------
# MODELS
# -----------------------
class Lead(BaseModel):
    name: str
    phone: str
    email: str
    city: str
    state: str
    zip_code: str
    service: str
    project_details: str

class Contractor(BaseModel):
    company_name: str
    contact_name: str
    phone: str
    email: str
    services_offered: str
    service_area: str
    licensed_insured: str
    notes: str = ""

# -----------------------
# ROOT
# -----------------------
@app.get("/")
def root():
    return {"message": "API is live"}

# -----------------------
# LEADS ROUTES
# -----------------------
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

# -----------------------
# CONTRACTOR ROUTES
# -----------------------
@app.post("/contractors")
def create_contractor(contractor: Contractor):
    contractors_db.append(contractor.dict())
    return {
        "success": True,
        "message": "Contractor application received",
        "data": contractor
    }

@app.get("/contractors")
def get_contractors():
    return contractors_db

# -----------------------
# ADMIN DASHBOARD
# -----------------------
@app.get("/admin", response_class=HTMLResponse)
def admin():
    html = """
    <html>
    <head>
        <title>LeadForge Dashboard</title>
        <style>
            body { font-family: Arial; padding: 20px; }
            h1, h2 { margin-top: 30px; }
            table { border-collapse: collapse; width: 100%; margin-bottom: 30px; }
            th, td { border: 1px solid #ccc; padding: 8px; vertical-align: top; }
            th { background: #eee; }
        </style>
    </head>
    <body>
        <h1>LeadForge Admin Dashboard</h1>

        <h2>Homeowner Leads</h2>
        <table>
            <tr>
                <th>Name</th>
                <th>Phone</th>
                <th>Email</th>
                <th>City</th>
                <th>State</th>
                <th>Zip</th>
                <th>Service</th>
                <th>Project Details</th>
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

        <h2>Contractor Applications</h2>
        <table>
            <tr>
                <th>Company</th>
                <th>Contact</th>
                <th>Phone</th>
                <th>Email</th>
                <th>Services</th>
                <th>Service Area</th>
                <th>Licensed/Insured</th>
                <th>Notes</th>
            </tr>
    """

    for contractor in contractors_db:
        html += f"""
        <tr>
            <td>{contractor['company_name']}</td>
            <td>{contractor['contact_name']}</td>
            <td>{contractor['phone']}</td>
            <td>{contractor['email']}</td>
            <td>{contractor['services_offered']}</td>
            <td>{contractor['service_area']}</td>
            <td>{contractor['licensed_insured']}</td>
            <td>{contractor['notes']}</td>
        </tr>
        """

    html += """
        </table>
    </body>
    </html>
    """

    return html
