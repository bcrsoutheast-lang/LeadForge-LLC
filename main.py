from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

leads_db = []
contractors_db = []

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
    owner_name: str
    business_type: str
    service_area: str
    crew_size: str
    years_in_business: str
    bio: str
    phone: str
    email: str
    license_number: str
    insurance_type: str
    insurance_coverage: str
    notes: str = ""
    status: str = "pending"
    verified: bool = False

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

@app.get("/contractors/approve/{contractor_index}")
def approve_contractor(contractor_index: int):
    if 0 <= contractor_index < len(contractors_db):
        contractors_db[contractor_index]["status"] = "approved"
        contractors_db[contractor_index]["verified"] = True
    return RedirectResponse(url="/admin", status_code=302)

@app.get("/contractors/reject/{contractor_index}")
def reject_contractor(contractor_index: int):
    if 0 <= contractor_index < len(contractors_db):
        contractors_db[contractor_index]["status"] = "rejected"
        contractors_db[contractor_index]["verified"] = False
    return RedirectResponse(url="/admin", status_code=302)

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
            a.action {
                display: inline-block;
                padding: 6px 10px;
                margin-right: 6px;
                text-decoration: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
            }
            a.approve { background: #0f7b0f; color: white; }
            a.reject { background: #b30000; color: white; }
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
                <th>Owner</th>
                <th>Business Type</th>
                <th>Service Area</th>
                <th>Crew Size</th>
                <th>Years in Business</th>
                <th>Bio</th>
                <th>Phone</th>
                <th>Email</th>
                <th>License Number</th>
                <th>Insurance Type</th>
                <th>Insurance Coverage</th>
                <th>Notes</th>
                <th>Status</th>
                <th>Verified</th>
                <th>Actions</th>
            </tr>
    """

    for i, contractor in enumerate(contractors_db):
        html += f"""
        <tr>
            <td>{contractor['company_name']}</td>
            <td>{contractor['owner_name']}</td>
            <td>{contractor['business_type']}</td>
            <td>{contractor['service_area']}</td>
            <td>{contractor['crew_size']}</td>
            <td>{contractor['years_in_business']}</td>
            <td>{contractor['bio']}</td>
            <td>{contractor['phone']}</td>
            <td>{contractor['email']}</td>
            <td>{contractor['license_number']}</td>
            <td>{contractor['insurance_type']}</td>
            <td>{contractor['insurance_coverage']}</td>
            <td>{contractor['notes']}</td>
            <td>{contractor['status']}</td>
            <td>{contractor['verified']}</td>
            <td>
                <a class="action approve" href="/contractors/approve/{i}">Approve</a>
                <a class="action reject" href="/contractors/reject/{i}">Reject</a>
            </td>
        </tr>
        """

    html += """
        </table>
    </body>
    </html>
    """

    return html
