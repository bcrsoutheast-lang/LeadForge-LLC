from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

templates = Jinja2Templates(directory="templates")

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")


# =====================
# BASIC ROUTES
# =====================

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request, "index.html", {})


@app.get("/health")
def health():
    return {"status": "ok"}


# =====================
# SERVICES PAGE
# =====================

@app.get("/services", response_class=HTMLResponse)
def services_page(request: Request):
    return templates.TemplateResponse(request, "services.html", {})


# =====================
# CONTRACTOR SIGNUP
# =====================

@app.get("/join-contractor", response_class=HTMLResponse)
def join_contractor(request: Request):
    return templates.TemplateResponse(request, "join-contractor.html", {})


@app.post("/join-contractor")
def submit_contractor():
    return RedirectResponse("/join-contractor-success", status_code=303)


@app.get("/join-contractor-success", response_class=HTMLResponse)
def join_success(request: Request):
    return templates.TemplateResponse(request, "join-contractor-success.html", {})


# =====================
# CONTRACTOR BROWSE
# =====================

@app.get("/contractors", response_class=HTMLResponse)
def contractors(request: Request, service: str = None):
    return templates.TemplateResponse(
        request,
        "contractors.html",
        {
            "service": service
        }
    )


# =====================
# HOMEOWNER REQUEST
# =====================

@app.get("/request/{contractor_id}", response_class=HTMLResponse)
def request_page(request: Request, contractor_id: str):
    return templates.TemplateResponse(
        request,
        "request.html",
        {
            "contractor_id": contractor_id
        }
    )


@app.post("/request/{contractor_id}")
def submit_request(contractor_id: str):
    return RedirectResponse("/request-success", status_code=303)


@app.get("/request-success", response_class=HTMLResponse)
def request_success(request: Request):
    return templates.TemplateResponse(request, "request-success.html", {})


# =====================
# ADMIN
# =====================

@app.get("/admin-login", response_class=HTMLResponse)
def admin_login(request: Request):
    return templates.TemplateResponse(request, "admin-login.html", {})


@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    return templates.TemplateResponse(request, "admin.html", {})


# =====================
# CONTRACTOR DASHBOARD
# =====================

@app.get("/contractor/{contractor_id}", response_class=HTMLResponse)
def contractor_dashboard(request: Request, contractor_id: str, token: str = None):
    return templates.TemplateResponse(
        request,
        "contractor-dashboard.html",
        {
            "contractor_id": contractor_id,
            "token": token
        }
    )


# =====================
# STRIPE UNLOCK FLOW
# =====================

@app.get("/unlock/{lead_id}")
def unlock_lead(lead_id: str, token: str = None):
    return RedirectResponse(f"/stripe-success?session_id=test&token={token}")


@app.get("/stripe-success", response_class=HTMLResponse)
def stripe_success(request: Request, session_id: str = None, token: str = None):
    return templates.TemplateResponse(
        request,
        "stripe-success.html",
        {
            "session_id": session_id,
            "token": token
        }
    )
