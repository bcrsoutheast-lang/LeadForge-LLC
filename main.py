from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from supabase import create_client
from datetime import datetime, timezone
import os
import re


app = FastAPI()

# -----------------------------------
# CORS
# -----------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------
# SUPABASE
# -----------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Missing SUPABASE_URL or SUPABASE_KEY environment variables")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# -----------------------------------
# HELPERS
# -----------------------------------
def clean_string(value):
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    value = value.strip()
    return value if value else None


def normalize_email(value):
    value = clean_string(value)
    return value.lower() if value else None


def normalize_phone(value):
    value = clean_string(value)
    if not value:
        return None
    return re.sub(r"\D", "", value)


def get_first_present(data, keys):
    for key in keys:
        value = data.get(key)
        value = clean_string(value)
        if value is not None:
            return value
    return None


# -----------------------------------
# HEALTH
# -----------------------------------
@app.get("/")
def root():
    return {"message": "API WORKING"}


@app.get("/health")
def health():
    return {"status": "ok"}


# -----------------------------------
# ADMIN
# -----------------------------------
@app.get("/admin")
def admin():
    try:
        res = (
            supabase
            .table("contractors")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        return res.data
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Admin fetch failed: {str(e)}"}
        )


# -----------------------------------
# CONTRACTORS
# -----------------------------------
@app.get("/contractors")
def get_public_contractors():
    try:
        res = (
            supabase
            .table("contractors")
            .select("*")
            .eq("approved", True)
            .order("created_at", desc=True)
            .execute()
        )
        return res.data
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Could not fetch contractors: {str(e)}"}
        )


@app.get("/contractors/approved")
def get_approved_contractors():
    try:
        res = (
            supabase
            .table("contractors")
            .select("*")
            .eq("approved", True)
            .order("created_at", desc=True)
            .execute()
        )
        return res.data
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Could not fetch approved contractors: {str(e)}"}
        )


@app.get("/contractors/{contractor_id}")
def get_contractor(contractor_id: str):
    try:
        res = (
            supabase
            .table("contractors")
            .select("*")
            .eq("id", contractor_id)
            .single()
            .execute()
        )
        return res.data
    except Exception:
        raise HTTPException(status_code=404, detail="Contractor not found")


# -----------------------------------
# APPROVE / REJECT
# -----------------------------------
@app.get("/contractors/approve/{contractor_id}")
def approve_contractor_get(contractor_id: str):
    try:
        supabase.table("contractors").update({
            "status": "approved",
            "approved": True
        }).eq("id", contractor_id).execute()

        return {
            "message": "approved",
            "id": contractor_id
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Approval failed: {str(e)}"}
        )


@app.post("/contractors/approve/{contractor_id}")
def approve_contractor_post(contractor_id: str):
    try:
        supabase.table("contractors").update({
            "status": "approved",
            "approved": True
        }).eq("id", contractor_id).execute()

        return {
            "message": "approved",
            "id": contractor_id
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Approval failed: {str(e)}"}
        )


@app.post("/contractors/reject/{contractor_id}")
def reject_contractor(contractor_id: str):
    try:
        supabase.table("contractors").delete().eq("id", contractor_id).execute()
        return {"message": "rejected", "id": contractor_id}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Reject failed: {str(e)}"}
        )


# -----------------------------------
# CREATE LEAD
# -----------------------------------
@app.post("/leads")
async def create_lead(request: Request):
    try:
        data = await request.json()

        contractor_id = get_first_present(data, ["contractor_id", "contractorId", "id"])
        name = get_first_present(data, ["name", "full_name", "fullName"])
        email = normalize_email(get_first_present(data, ["email", "homeowner_email", "homeownerEmail"]))
        phone = normalize_phone(get_first_present(data, ["phone", "phone_number", "phoneNumber"]))
        city = get_first_present(data, ["city"])
        state = get_first_present(data, ["state"])
        zip_code = get_first_present(data, ["zip", "zip_code", "zipcode"])
        details = get_first_present(data, ["details", "message", "project_details", "projectDetails", "description"])

        if not contractor_id:
            return JSONResponse(
                status_code=400,
                content={"detail": "Missing contractor_id"}
            )

        if not name:
            return JSONResponse(
                status_code=400,
                content={"detail": "Missing name"}
            )

        if not email and not phone:
            return JSONResponse(
                status_code=400,
                content={"detail": "Email or phone is required"}
            )

        # Confirm contractor exists
        try:
            contractor_check = (
                supabase
                .table("contractors")
                .select("id, approved")
                .eq("id", contractor_id)
                .single()
                .execute()
            )
            contractor = contractor_check.data
        except Exception:
            return JSONResponse(
                status_code=404,
                content={"detail": "Contractor not found"}
            )

        if not contractor:
            return JSONResponse(
                status_code=404,
                content={"detail": "Contractor not found"}
            )

        # Duplicate block
        existing = (
            supabase
            .table("leads")
            .select("*")
            .eq("contractor_id", contractor_id)
            .execute()
        )

        existing_rows = existing.data or []

        for row in existing_rows:
            existing_email = normalize_email(row.get("email"))
            existing_phone = normalize_phone(row.get("phone"))

            email_match = email and existing_email and email == existing_email
            phone_match = phone and existing_phone and phone == existing_phone

            if email_match or phone_match:
                return JSONResponse(
                    status_code=400,
                    content={"detail": "You already submitted a request for this contractor"}
                )

        insert_payload = {
            "contractor_id": contractor_id,
            "name": name,
            "email": email,
            "phone": phone,
            "city": city,
            "state": state,
            "zip": zip_code,
            "details": details,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        insert_res = (
            supabase
            .table("leads")
            .insert(insert_payload)
            .execute()
        )

        inserted = insert_res.data[0] if insert_res.data else None

        return {
            "message": "Lead created",
            "lead": inserted
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Lead creation failed: {str(e)}"}
        )
