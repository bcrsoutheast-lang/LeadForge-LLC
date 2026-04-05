

@app.post("/homeowner", response_class=HTMLResponse)
def homeowner_submit(
    owner_name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(""),
    service: str = Form(...),
    city: str = Form(...),
    state: str = Form(...),
    zip_code: str = Form(...),
    contractor_id: str = Form(...),
    project_details: str = Form(...),
) -> str:
    supabase = get_supabase()

    if supabase is None:
        body = """
        <section class="card">
            <h1>Homeowner Request</h1>
            <div class="error">
                Supabase is not connected.
            </div>
            <a class="btn" href="/homeowner">Back</a>
        </section>
        """
        return page_shell("Error", body)

    payload = {
        "owner_name": owner_name.strip(),
        "phone": phone.strip(),
        "email": email.strip(),
        "service": service.strip(),
        "city": city.strip(),
        "state": state.strip(),
        "zip_code": zip_code.strip(),
        "project_details": project_details.strip(),
        "contractor_id": contractor_id,
    }

    ok, message = safe_insert_record(supabase, "leads", payload)

    if not ok:
        body = f"""
        <section class="card">
            <h1>Homeowner Request</h1>
            <div class="error">
                Submission failed.<br><br>
                {escape(message)}
            </div>
            <a class="btn" href="/homeowner">Back</a>
        </section>
        """
        return page_shell("Error", body)

    body = f"""
    <section class="card">
        <h1>Request Submitted</h1>
        <div class="success">
            Your request was submitted successfully.
        </div>

        <a class="btn" href="/homeowner">Submit Another</a>
        <a class="btn btn-secondary" href="/admin">Admin</a>
    </section>
    """
    return page_shell("Success", body)
