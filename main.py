from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
import stripe
import os

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="secret")

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID")
BASE_URL = os.getenv("BASE_URL")

stripe.api_key = STRIPE_SECRET_KEY

# ==============================
# MOCK DATA (your existing still works)
# ==============================

leads = {}
contractors = {}

# ==============================
# HELPERS
# ==============================

def layout(body):
    return HTMLResponse(f"""
    <html>
    <body style="background:#0b0b0b;color:white;font-family:Arial;padding:20px;">
    {body}

<script>
function copyFromButton(button) {{
  const text = button.getAttribute('data-copy') || '';
  if (!text) return;

  navigator.clipboard.writeText(text).then(function () {{
    const original = button.innerText;
    button.innerText = 'Copied';
    setTimeout(function () {{
      button.innerText = original;
    }}, 1200);
  }});
}}
</script>

    </body>
    </html>
    """)

# ==============================
# HOME
# ==============================

@app.get("/")
def home():
    return layout("<h1>VaultForge Live</h1>")

# ==============================
# ADMIN (FIXED UI)
# ==============================

@app.get("/admin")
def admin():

    html = "<h1>Admin</h1>"

    for cid, contractor in contractors.items():

        token_link = f"/contractor/{cid}?token={contractor['token']}"

        html += f"""
        <div style="border:1px solid #333;padding:15px;margin-bottom:20px;">
            <h2>{contractor['name']}</h2>

            <div>
                <b>Dashboard Link:</b><br>
                <div style="background:#111;padding:10px;">
                {BASE_URL}{token_link}
                </div>

                <button onclick="copyFromButton(this)" data-copy="{BASE_URL}{token_link}">
                    Copy Link
                </button>
            </div>
        """

        contractor_leads = [l for l in leads.values() if l["contractor_id"] == cid]

        for lead in contractor_leads:
            short = f"{lead['name']} | {lead['phone']} | {lead['service']}"

            html += f"""
            <div style="margin-top:10px;padding:10px;background:#111;">
                {short}

                <button onclick="copyFromButton(this)" data-copy="{short}">
                    Copy Lead
                </button>
            </div>
            """

        html += "</div>"

    return layout(html)

# ==============================
# CONTRACTOR DASHBOARD (TOKEN)
# ==============================

@app.get("/contractor/{cid}")
def contractor_dashboard(cid: str, token: str = ""):

    contractor = contractors.get(cid)

    if not contractor or contractor["token"] != token:
        return layout("<h2>Access Denied</h2>")

    html = f"<h1>{contractor['name']} Dashboard</h1>"

    contractor_leads = [l for l in leads.values() if l["contractor_id"] == cid]

    for lead in contractor_leads:
        if not lead.get("unlocked"):
            html += f"""
            <div style="margin-bottom:15px;">
                <b>Locked Lead</b>
                <br>
                <a href="/unlock/{lead['id']}?token={token}">Unlock $10</a>
            </div>
            """
        else:
            html += f"""
            <div style="margin-bottom:15px;">
                <b>{lead['name']}</b><br>
                {lead['phone']}<br>
                {lead['email']}
            </div>
            """

    return layout(html)

# ==============================
# STRIPE CHECKOUT
# ==============================

@app.get("/unlock/{lead_id}")
def unlock(lead_id: str, token: str):

    lead = leads.get(lead_id)
    contractor_id = lead["contractor_id"]

    success_url = f"{BASE_URL}/stripe-success?session_id={{CHECKOUT_SESSION_ID}}&lead_id={lead_id}&contractor_id={contractor_id}&token={token}"

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        line_items=[{"price": STRIPE_PRICE_ID, "quantity": 1}],
        success_url=success_url,
        cancel_url=f"{BASE_URL}/contractor/{contractor_id}?token={token}"
    )

    return RedirectResponse(session.url)

# ==============================
# STRIPE SUCCESS (FINAL FIX)
# ==============================

@app.get("/stripe-success")
def stripe_success(session_id: str, lead_id: str, contractor_id: str, token: str):

    session = stripe.checkout.Session.retrieve(session_id)

    if session.payment_status == "paid":

        leads[lead_id]["unlocked"] = True

        return RedirectResponse(f"/contractor/{contractor_id}?token={token}")

    return layout("<h2>Payment Error</h2>")

# ==============================
# TEST DATA (SAFE)
# ==============================

contractors["1"] = {
    "name": "Test Contractor",
    "token": "abc123"
}

leads["1"] = {
    "id": "1",
    "contractor_id": "1",
    "name": "John Smith",
    "phone": "555-1234",
    "email": "john@email.com",
    "service": "Roofing",
    "unlocked": False
}
