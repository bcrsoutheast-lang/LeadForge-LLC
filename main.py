from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()


@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <h1>LeadForge is back up</h1>
    <p>Safe restore test is live.</p>
    <a href="/health">Health</a>
    """


@app.get("/health")
def health():
    return {"status": "ok"}
