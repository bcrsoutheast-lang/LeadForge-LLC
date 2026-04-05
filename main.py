from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()


@app.get("/")
def home():
    return HTMLResponse("""
    <html>
        <head>
            <title>LeadForge</title>
        </head>
        <body>
            <h1>LeadForge is back</h1>
            <p>Basic app is running.</p>
        </body>
    </html>
    """)


@app.get("/health")
def health():
    return {"status": "ok"}
