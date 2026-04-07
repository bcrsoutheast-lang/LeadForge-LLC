from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()

templates = Jinja2Templates(directory="templates")

# Static files (logo, etc.)
app.mount("/static", StaticFiles(directory="static"), name="static")


# =====================
# BASIC ROUTES
# =====================

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
def health():
    return {"status": "ok"}


# =====================
# NEW SERVICES PAGE
# =====================

@app.get("/services", response_class=HTMLResponse)
def services_page(request: Request):
    return templates.TemplateResponse("services.html", {"request": request})


# =====================
# CONTRACTOR SIGNUP
# =====================

@app.get("/join-contractor", response_class=HTMLResponse)
def join_contractor(request: Request):
    return templates.TemplateResponse("join-contractor.html", {"request": request})


@app.post("/join-contractor")
def submit_contractor():
    # Placeholder (you already have working logic)
    return RedirectResponse("/join-contractor-success", status_code=303)


@app.get("/join-contractor-success", response_class=HTMLResponse)
def join_success(request: Request):
    return templates.TemplateResponse("join-contractor-success.html", {"request": request})


# =====================
# CONTRACTOR BROWSE
# =====================

@app.get("/contractors", response_class=HTMLResponse)
def contractors(request: Request, service: str = None):
    # service filter will be used later
    return templates.TemplateResponse("contractors.html", {
        "request": request,
        "service": service
    })


# =====================
# HOMEOWNER REQUEST
# =====================

@app.get("/request/{contractor_id}", response_class=HTMLResponse)
def request_page(request: Request, contractor_id: str):
    return templates.TemplateResponse("request.html", {
        "request": request,
        "contractor_id": contractor_id
    })


@app.post("/request/{contractor_id}")
def submit_request(contractor_id: str):
    return RedirectResponse("/request-success", status_code=303)


@app.get("/request-success", response_class=HTMLResponse)
def request_success(request: Request):
    return templates.TemplateResponse("request-success.html", {"request": request})


# =====================
# ADMIN
# =====================

@app.get("/admin-login", response_class=HTMLResponse)
def admin_login(request: Request):
    return templates.TemplateResponse("admin-login.html", {"request": request})


@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})


# =====================
# CONTRACTOR DASHBOARD
# =====================

@app.get("/contractor/{contractor_id}", response_class=HTMLResponse)
def contractor_dashboard(request: Request, contractor_id: str, token: str = None):
    return templates.TemplateResponse("contractor-dashboard.html", {
        "request": request,
        "contractor_id": contractor_id,
        "token": token
    })


# =====================
# STRIPE UNLOCK FLOW
# =====================

@app.get("/unlock/{lead_id}")
def unlock_lead(lead_id: str, token: str = None):
    # placeholder for stripe redirect
    return RedirectResponse("/stripe-success?session_id=test&token=" + str(token))


@app.get("/stripe-success", response_class=HTMLResponse)
def stripe_success(request: Request, session_id: str = None, token: str = None):
    return templates.TemplateResponse("stripe-success.html", {
        "request": request,
        "session_id": session_id,
        "token": token
    })
