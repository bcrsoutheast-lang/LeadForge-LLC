from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>LeadForge</title>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <style>
            body { font-family: Arial; background:#f7f7f7; text-align:center; }
            .wrap { max-width:800px; margin:80px auto; background:white; padding:40px; border-radius:14px; }
            a.button { display:inline-block; margin:10px; padding:14px 22px; background:#111; color:white; text-decoration:none; border-radius:10px; }
        </style>
    </head>
    <body>
        <div class="wrap">
            <h1>LeadForge is back up</h1>
            <a class="button" href="/contractors">Browse Contractors</a>
            <a class="button" href="/health">Health</a>
        </div>
    </body>
    </html>
    """


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/contractors", response_class=HTMLResponse)
def contractors():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Browse Contractors</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                font-family: Arial;
                background:#f4f4f4;
                margin:0;
                padding:0;
            }

            .header {
                text-align:center;
                padding:30px 20px 10px;
            }

            .header h1 {
                margin:0;
            }

            .grid {
                display:grid;
                grid-template-columns: repeat(auto-fit, minmax(260px,1fr));
                gap:20px;
                padding:30px;
                max-width:1100px;
                margin:auto;
            }

            .card {
                background:white;
                border-radius:14px;
                padding:20px;
                box-shadow:0 6px 20px rgba(0,0,0,0.08);
                transition:0.2s;
            }

            .card:hover {
                transform: translateY(-4px);
            }

            .name {
                font-size:20px;
                font-weight:bold;
                margin-bottom:10px;
            }

            .info {
                color:#555;
                margin:6px 0;
            }

            .btn {
                margin-top:14px;
                display:inline-block;
                padding:10px 16px;
                background:#111;
                color:white;
                text-decoration:none;
                border-radius:8px;
                font-size:14px;
            }

            .back {
                text-align:center;
                margin-bottom:40px;
            }

            .back a {
                padding:12px 18px;
                background:#111;
                color:white;
                text-decoration:none;
                border-radius:10px;
            }
        </style>
    </head>

    <body>

        <div class="header">
            <h1>Browse Contractors</h1>
            <p>Select a contractor to request a quote</p>
        </div>

        <div class="grid">

            <div class="card">
                <div class="name">Elite Roofing Co</div>
                <div class="info">Service: Roofing</div>
                <div class="info">City: Birmingham</div>
                <a class="btn" href="#">Request Quote</a>
            </div>

            <div class="card">
                <div class="name">FreshWash Exterior</div>
                <div class="info">Service: Pressure Washing</div>
                <div class="info">City: Hoover</div>
                <a class="btn" href="#">Request Quote</a>
            </div>

            <div class="card">
                <div class="name">GreenScape Pros</div>
                <div class="info">Service: Landscaping</div>
                <div class="info">City: Vestavia Hills</div>
                <a class="btn" href="#">Request Quote</a>
            </div>

        </div>

        <div class="back">
            <a href="/">Back Home</a>
        </div>

    </body>
    </html>
    """
