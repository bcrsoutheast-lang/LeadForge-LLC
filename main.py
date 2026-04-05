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
            body {
                font-family: Arial, sans-serif;
                background: #f7f7f7;
                margin: 0;
                padding: 0;
                text-align: center;
            }
            .wrap {
                max-width: 800px;
                margin: 80px auto;
                background: white;
                padding: 40px 24px;
                border-radius: 14px;
                box-shadow: 0 8px 30px rgba(0,0,0,0.08);
            }
            h1 {
                margin-top: 0;
                color: #111;
            }
            p {
                color: #444;
                font-size: 18px;
                line-height: 1.5;
            }
            .buttons {
                margin-top: 28px;
                display: flex;
                gap: 14px;
                justify-content: center;
                flex-wrap: wrap;
            }
            a.button {
                display: inline-block;
                padding: 14px 22px;
                border-radius: 10px;
                background: #111;
                color: white;
                text-decoration: none;
                font-weight: bold;
            }
            a.button:hover {
                opacity: 0.9;
            }
        </style>
    </head>
    <body>
        <div class="wrap">
            <h1>LeadForge is back up</h1>
            <p>
                Safe recovery mode is live.
            </p>
            <p>
                We are now rebuilding one route at a time from a stable base.
            </p>

            <div class="buttons">
                <a class="button" href="/contractors">Browse Contractors</a>
                <a class="button" href="/health">Health Check</a>
            </div>
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
        <title>LeadForge Contractors</title>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #f7f7f7;
                margin: 0;
                padding: 0;
            }
            .wrap {
                max-width: 900px;
                margin: 40px auto;
                background: white;
                padding: 32px 24px;
                border-radius: 14px;
                box-shadow: 0 8px 30px rgba(0,0,0,0.08);
            }
            h1 {
                margin-top: 0;
                color: #111;
                text-align: center;
            }
            p.top {
                text-align: center;
                color: #555;
                margin-bottom: 30px;
            }
            .list {
                display: grid;
                gap: 16px;
            }
            .item {
                border: 1px solid #e3e3e3;
                border-radius: 12px;
                padding: 18px;
                background: #fafafa;
            }
            .item h2 {
                margin: 0 0 8px 0;
                font-size: 22px;
                color: #111;
            }
            .item p {
                margin: 6px 0;
                color: #444;
            }
            .back {
                text-align: center;
                margin-top: 28px;
            }
            .back a {
                display: inline-block;
                padding: 12px 18px;
                border-radius: 10px;
                background: #111;
                color: white;
                text-decoration: none;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="wrap">
            <h1>Browse Contractors</h1>
            <p class="top">
                Recovery step 1 complete. This is the simple HTML contractors page.
            </p>

            <div class="list">
                <div class="item">
                    <h2>Sample Contractor 1</h2>
                    <p><strong>Service:</strong> Roofing</p>
                    <p><strong>City:</strong> Birmingham</p>
                    <p><strong>Status:</strong> Demo placeholder</p>
                </div>

                <div class="item">
                    <h2>Sample Contractor 2</h2>
                    <p><strong>Service:</strong> Pressure Washing</p>
                    <p><strong>City:</strong> Hoover</p>
                    <p><strong>Status:</strong> Demo placeholder</p>
                </div>

                <div class="item">
                    <h2>Sample Contractor 3</h2>
                    <p><strong>Service:</strong> Landscaping</p>
                    <p><strong>City:</strong> Vestavia Hills</p>
                    <p><strong>Status:</strong> Demo placeholder</p>
                </div>
            </div>

            <div class="back">
                <a href="/">Back Home</a>
            </div>
        </div>
    </body>
    </html>
    """
