import os
from typing import Any, Dict, List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from supabase import Client, create_client


app = FastAPI(title="LeadForge Stable Fallback")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_supabase() -> Client | None:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or os.getenv("SUPABASE_KEY")
        or os.getenv("SUPABASE_ANON_KEY")
    )

    if not supabase_url or not supabase_key:
        return None

    try:
        return create_client(supabase_url, supabase_key)
    except Exception:
        return None


def safe_fetch_table(supabase: Client, table_name: str) -> List[Dict[str, Any]]:
    try:
        response = supabase.table(table_name).select("*").execute()
        return response.data if response.data else []
    except Exception:
        return []


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>LeadForge LLC</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #f7f7f7;
                margin: 0;
                padding: 40px 20px;
                text-align: center;
            }
            .wrap {
                max-width: 700px;
                margin: 0 auto;
                background: white;
                padding: 40px 25px;
                border-radius: 14px;
                box-shadow: 0 4px 18px rgba(0,0,0,0.08);
            }
            h1 {
                margin-bottom: 10px;
            }
            p {
                color: #555;
                margin-bottom: 30px;
            }
            .btn {
                display: inline-block;
                margin: 10px;
                padding: 14px 22px;
                background: #111827;
                color: white;
                text-decoration: none;
                border-radius: 10px;
                font-weight: bold;
            }
            .btn:hover {
                opacity: 0.9;
            }
        </style>
    </head>
    <body>
        <div class="wrap">
            <h1>LeadForge LLC</h1>
            <p>Stable fallback homepage is live.</p>
            <a class="btn" href="/contractor-signup">Contractor Signup</a>
            <a class="btn" href="/admin">Admin</a>
        </div>
    </body>
    </html>
    """


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/contractor-signup", response_class=HTMLResponse)
def contractor_signup_page() -> str:
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Contractor Signup - LeadForge</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #f7f7f7;
                margin: 0;
                padding: 40px 20px;
            }
            .wrap {
                max-width: 700px;
                margin: 0 auto;
                background: white;
                padding: 30px 25px;
                border-radius: 14px;
                box-shadow: 0 4px 18px rgba(0,0,0,0.08);
            }
            a {
                color: #111827;
                text-decoration: none;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="wrap">
            <h1>Contractor Signup</h1>
            <p>This route is live and stable.</p>
            <p>We are rebuilding one piece at a time from the fallback app.</p>
            <p><a href="/">← Back to Homepage</a></p>
        </div>
    </body>
    </html>
    """


@app.get("/admin", response_class=HTMLResponse)
def admin_page() -> HTMLResponse:
    supabase = get_supabase()

    if supabase is None:
        return HTMLResponse(
            """
            <!DOCTYPE html>
            <html>
            <head>
                <title>LeadForge Admin</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        background: #f7f7f7;
                        margin: 0;
                        padding: 40px 20px;
                    }
                    .wrap {
                        max-width: 900px;
                        margin: 0 auto;
                        background: white;
                        padding: 30px 25px;
                        border-radius: 14px;
                        box-shadow: 0 4px 18px rgba(0,0,0,0.08);
                    }
                    .warn {
                        background: #fff8e1;
                        border: 1px solid #f4d06f;
                        color: #6b4f00;
                        padding: 14px;
                        border-radius: 10px;
                        margin-top: 20px;
                    }
                    a {
                        color: #111827;
                        text-decoration: none;
                        font-weight: bold;
                    }
                </style>
            </head>
            <body>
                <div class="wrap">
                    <h1>LeadForge Admin</h1>
                    <div class="warn">
                        Supabase is not connected. Check your Render environment variables:
                        SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_KEY / SUPABASE_ANON_KEY).
                    </div>
                    <p><a href="/">← Back to Homepage</a></p>
                </div>
            </body>
            </html>
            """
        )

    contractors = safe_fetch_table(supabase, "contractors")
    leads = safe_fetch_table(supabase, "leads")

    def build_table(title: str, rows: List[Dict[str, Any]]) -> str:
        if not rows:
            return f"""
            <section class="card">
                <h2>{title}</h2>
                <p>No records found.</p>
            </section>
            """

        columns = sorted({key for row in rows for key in row.keys()})

        header_html = "".join(f"<th>{col}</th>" for col in columns)

        body_parts = []
        for row in rows:
            tds = []
            for col in columns:
                value = row.get(col, "")
                if value is None:
                    value = ""
                tds.append(f"<td>{str(value)}</td>")
            body_parts.append(f"<tr>{''.join(tds)}</tr>")

        body_html = "".join(body_parts)

        return f"""
        <section class="card">
            <h2>{title} ({len(rows)})</h2>
            <div class="table-wrap">
                <table>
                    <thead>
                        <tr>{header_html}</tr>
                    </thead>
                    <tbody>
                        {body_html}
                    </tbody>
                </table>
            </div>
        </section>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>LeadForge Admin</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: Arial, sans-serif;
                background: #f7f7f7;
                margin: 0;
                padding: 30px 15px;
            }}
            .wrap {{
                max-width: 1200px;
                margin: 0 auto;
            }}
            .topbar {{
                background: white;
                padding: 20px;
                border-radius: 14px;
                box-shadow: 0 4px 18px rgba(0,0,0,0.08);
                margin-bottom: 20px;
            }}
            .card {{
                background: white;
                padding: 20px;
                border-radius: 14px;
                box-shadow: 0 4px 18px rgba(0,0,0,0.08);
                margin-bottom: 20px;
            }}
            .table-wrap {{
                overflow-x: auto;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 12px;
            }}
            th, td {{
                border: 1px solid #e5e7eb;
                padding: 10px;
                text-align: left;
                font-size: 14px;
                vertical-align: top;
                white-space: nowrap;
            }}
            th {{
                background: #111827;
                color: white;
            }}
            a {{
                color: #111827;
                text-decoration: none;
                font-weight: bold;
            }}
            .meta {{
                color: #555;
                margin-top: 6px;
            }}
        </style>
    </head>
    <body>
        <div class="wrap">
            <div class="topbar">
                <h1>LeadForge Admin</h1>
                <div class="meta">Stable rebuild step: Supabase-backed admin data</div>
                <p><a href="/">← Back to Homepage</a></p>
            </div>

            {build_table("Contractors", contractors)}
            {build_table("Leads", leads)}
        </div>
    </body>
    </html>
    """

    return HTMLResponse(content=html)


@app.get("/admin/data")
def admin_data() -> JSONResponse:
    supabase = get_supabase()

    if supabase is None:
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": "Supabase is not connected. Check environment variables."
            },
        )

    contractors = safe_fetch_table(supabase, "contractors")
    leads = safe_fetch_table(supabase, "leads")

    return JSONResponse(
        content={
            "ok": True,
            "contractors": contractors,
            "leads": leads,
        }
    )
