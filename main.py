from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uuid

print("NEW VERSION DEPLOYED")
print("DEPLOY TEST APRIL 8")
print("REQUEST-FIRST TEMPLATERESPONSE VERSION")

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


PENDING_CONTRACTORS = []
APPROVED_CONTRACTORS = []
LEADS = []


def get_contractor(contractor_id: str):
    for contractor in APPROVED_CONTRACTORS:
        if contractor["id"] == contractor_id:
            return contractor
    return None


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {}
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/services", response_class=HTMLResponse)
def services_page(request: Request):
    return templates.TemplateResponse(
        request,
        "services.html",
        {}
    )


@app.get("/join-contractor", response_class=HTMLResponse)
def join_contractor(request: Request):
    return templates.TemplateResponse(
        request,
        "join-contractor.html",
        {}
    )


@app.post("/join-contractor")
def submit_contractor(
    full_name: str = Form(...),
    company_name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    service: str = Form(...),
    city: str = Form(...),
    state: str = Form(...),
    zip_code: str = Form(...),
    bio: str = Form(...)
):
    contractor = {
        "id": str(uuid.uuid4()),
        "name": full_name,
        "company_name": company_name,
        "service": service,
        "city": city,
        "state": state,
        "zip_code": zip_code,
        "phone": phone,
        "email": email,
        "bio": bio,
        "approved": False,
    }

    PENDING_CONTRACTORS.append(contractor)

    return RedirectResponse("/join-contractor-success", status_code=303)


@app.get("/join-contractor-success", response_class=HTMLResponse)
def join_success(request: Request):
    return templates.TemplateResponse(
        request,
        "join-contractor-success.html",
        {}
    )


@app.get("/contractors", response_class=HTMLResponse)
def contractors(request: Request, service: str = None):
    data = APPROVED_CONTRACTORS

    if service:
        data = [c for c in data if c["service"].lower() == service.lower()]

    return templates.TemplateResponse(
        request,
        "contractors.html",
        {
            "contractors": data,
            "service": service
        }
    )


@app.get("/request/{contractor_id}", response_class=HTMLResponse)
def request_page(request: Request, contractor_id: str):
    contractor = get_contractor(contractor_id)

    return templates.TemplateResponse(
        request,
        "request.html",
        {
            "contractor": contractor,
            "contractor_id": contractor_id
        }
    )


@app.post("/request/{contractor_id}")
def submit_request(contractor_id: str):
    return RedirectResponse("/request-success", status_code=303)


@app.get("/request-success", response_class=HTMLResponse)
def request_success(request: Request):
    return templates.TemplateResponse(
        request,
        "request-success.html",
        {}
    )


@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    return templates.TemplateResponse(
        request,
        "admin.html",
        {
            "pending_contractors": PENDING_CONTRACTORS,
            "approved_contractors": APPROVED_CONTRACTORS,
            "contractors": APPROVED_CONTRACTORS,
            "leads": LEADS
        }
    )


@app.post("/approve/{contractor_id}")
def approve_contractor(contractor_id: str):
    global PENDING_CONTRACTORS, APPROVED_CONTRACTORS

    for contractor in PENDING_CONTRACTORS:
        if contractor["id"] == contractor_id:
            contractor["approved"] = True
            APPROVED_CONTRACTORS.append(contractor)
            break

    PENDING_CONTRACTORS = [
        contractor for contractor in PENDING_CONTRACTORS
        if contractor["id"] != contractor_id
    ]

    return RedirectResponse("/admin", status_code=303)


@app.post("/reject/{contractor_id}")
def reject_contractor(contractor_id: str):
    global PENDING_CONTRACTORS

    PENDING_CONTRACTORS = [
        contractor for contractor in PENDING_CONTRACTORS
        if contractor["id"] != contractor_id
    ]

    return RedirectResponse("/admin", status_code=303)


@app.get("/contractor/{contractor_id}", response_class=HTMLResponse)
def contractor_dashboard(request: Request, contractor_id: str):
    contractor = get_contractor(contractor_id)
    contractor_leads = [lead for lead in LEADS if lead.get("contractor_id") == contractor_id]

    return templates.TemplateResponse(
        request,
        "contractor-dashboard.html",
        {
            "contractor": contractor,
            "leads": contractor_leads
        }
    )
