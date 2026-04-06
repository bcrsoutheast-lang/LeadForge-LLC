def existing_active_lead(contractor_id: str, phone: str):
    db = db_required()
    result = (
        db.table("leads")
        .select("*")
        .eq("contractor_id", contractor_id)
        .eq("phone", phone)
        .limit(1)
        .execute()
    )
    return result.data or []


# ===============================
# UPDATE REQUEST SUBMIT (IMPORTANT)
# ===============================
@app.post("/request/{contractor_id}")
def submit_request(
    contractor_id: str,
    owner_name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(""),
    service: str = Form(...),
    project_details: str = Form(...),
    city: str = Form(...),
    state: str = Form(...),
    zip: str = Form(...),
):
    contractor = get_contractor_by_id(contractor_id)
    if not contractor or not contractor.get("approved"):
        raise HTTPException(status_code=404, detail="Contractor not found")

    # 🚨 NEW: Prevent duplicate requests
    existing = existing_active_lead(contractor_id, phone)
    if existing:
        return html_page(
            "Request Already Sent",
            """
            <div class="card">
                <h1>Request Already Sent</h1>
                <p>You already submitted a request to this contractor.</p>
                <a class="btn" href="/contractors">Back</a>
            </div>
            """
        )

    db = db_required()
    payload = {
        "contractor_id": contractor_id,
        "owner_name": owner_name,
        "phone": phone,
        "email": email,
        "service": service,
        "project_details": project_details,
        "city": city,
        "state": state,
        "zip": zip,
        "unlocked": False,
        "stripe_paid": False,
        "created_at": now_iso(),
    }
    db.table("leads").insert(payload).execute()

    return RedirectResponse(url="/request-success", status_code=303)


# ===============================
# UPDATE CONTRACTOR DASHBOARD FAIL
# ===============================
@app.get("/contractor/{contractor_id}", response_class=HTMLResponse)
def contractor_dashboard(contractor_id: str, token: Optional[str] = None):

    contractor = get_contractor_by_id(contractor_id)
    if not contractor:
        raise HTTPException(status_code=404)

    if not contractor.get("approved"):
        return render_forbidden_page(
            "Access Restricted",
            "This contractor is not approved yet."
        )

    if not token:
        return render_forbidden_page(
            "Private Access Required",
            "This page requires a private access link."
        )

    try:
        valid_token = require_contractor_token(contractor, token)
    except:
        return render_forbidden_page(
            "Invalid Access",
            "This link is invalid or expired."
        )
