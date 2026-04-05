from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()


@app.get("/")
def home():
    return HTMLResponse("""
    <html>
        <head>
            <title>LeadForge</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 40px 20px;
                    background: #f7f7f7;
                    color: #111;
                    text-align: center;
                }
                .wrap {
                    max-width: 700px;
                    margin: 0 auto;
                }
                h1 {
                    font-size: 48px;
                    margin-bottom: 16px;
                }
                p {
                    font-size: 22px;
                    color: #555;
                    line-height: 1.4;
                    margin-bottom: 32px;
                }
                a.button {
                    display: inline-block;
                    padding: 16px 28px;
                    margin: 8px;
                    text-decoration: none;
                    border-radius: 10px;
                    font-size: 18px;
                    font-weight: bold;
                }
                a.primary {
                    background: #111;
                    color: white;
                }
                a.secondary {
                    background: white;
                    color: #111;
                    border: 2px solid #111;
                }
            </style>
        </head>
        <body>
            <div class="wrap">
                <h1>LeadForge</h1>
                <p>Homeowners choose. Contractors win.</p>
                <a class="button primary" href="/contractor-signup">Contractor Signup</a>
                <a class="button secondary" href="/admin">Admin</a>
            </div>
        </body>
    </html>
    """)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/contractor-signup")
def contractor_signup():
    return HTMLResponse("""
    <html>
        <head>
            <title>Contractor Signup</title>
        </head>
        <body>
            <h1>Contractor Signup</h1>
            <p>Form connected to backend.</p>
            <a href="/">Back</a>
        </body>
    </html>
    """)


@app.get("/admin")
def admin():
    return HTMLResponse("""
    <html>
        <head>
            <title>Admin</title>
        </head>
        <body>
            <h1>Admin</h1>
            <p>Admin route is live.</p>
            <a href="/">Back</a>
        </body>
    </html>
    """)
