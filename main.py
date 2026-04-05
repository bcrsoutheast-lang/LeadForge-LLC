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
                background: #f4f4f4;
                margin: 0;
                padding: 0;
            }

            .wrap {
                max-width: 900px;
                margin: 80px auto;
                background: white;
                padding: 40px 24px;
                border-radius: 14px;
                box-shadow: 0 8px 30px rgba(0,0,0,0.08);
                text-align: center;
            }

            h1 {
                margin-top: 0;
                color: #111;
            }

            p {
                color: #555;
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
            <p>Safe rebuild mode is live.</p>
            <p>We are restoring one route at a time from a stable base.</p>

            <div class="buttons">
                <a class="button" href="/contractors">Browse Contractors</a>
                <a class="button" href="/contractor-signup">Join as a Contractor</a>
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
        <title>Browse Contractors</title>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #f4f4f4;
                margin: 0;
                padding: 0;
            }

            .header {
                text-align: center;
                padding: 30px 20px 10px;
            }

            .header h1 {
                margin: 0;
                color: #111;
            }

            .header p {
                color: #555;
            }

            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
                gap: 20px;
                padding: 30px;
                max-width: 1100px;
                margin: auto;
            }

            .card {
                background: white;
                border-radius: 14px;
                padding: 20px;
                box-shadow: 0 6px 20px rgba(0,0,0,0.08);
                transition: 0.2s;
            }

            .card:hover {
                transform: translateY(-4px);
            }

            .name {
                font-size: 20px;
                font-weight: bold;
                margin-bottom: 10px;
                color: #111;
            }

            .info {
                color: #555;
                margin: 6px 0;
            }

            .btn {
                margin-top: 14px;
                display: inline-block;
                padding: 10px 16px;
                background: #111;
                color: white;
                text-decoration: none;
                border-radius: 8px;
                font-size: 14px;
            }

            .back {
                text-align: center;
                margin-bottom: 40px;
            }

            .back a {
                padding: 12px 18px;
                background: #111;
                color: white;
                text-decoration: none;
                border-radius: 10px;
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


@app.get("/contractor-signup", response_class=HTMLResponse)
def contractor_signup():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Contractor Signup</title>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #f4f4f4;
                margin: 0;
                padding: 0;
            }

            .wrap {
                max-width: 760px;
                margin: 40px auto;
                background: white;
                padding: 32px 24px;
                border-radius: 14px;
                box-shadow: 0 8px 30px rgba(0,0,0,0.08);
            }

            h1 {
                margin-top: 0;
                text-align: center;
                color: #111;
            }

            .sub {
                text-align: center;
                color: #555;
                margin-bottom: 26px;
            }

            form {
                display: grid;
                gap: 16px;
            }

            label {
                font-weight: bold;
                color: #222;
                display: block;
                margin-bottom: 6px;
            }

            input, select, textarea {
                width: 100%;
                padding: 12px;
                border: 1px solid #d5d5d5;
                border-radius: 10px;
                font-size: 16px;
                box-sizing: border-box;
            }

            textarea {
                min-height: 110px;
                resize: vertical;
            }

            .btn {
                margin-top: 8px;
                border: none;
                background: #111;
                color: white;
                padding: 14px 18px;
                border-radius: 10px;
                font-size: 16px;
                font-weight: bold;
                cursor: pointer;
            }

            .btn:hover {
                opacity: 0.92;
            }

            .note {
                margin-top: 18px;
                padding: 14px;
                background: #f8f8f8;
                border: 1px solid #ececec;
                border-radius: 10px;
                color: #555;
                font-size: 14px;
                line-height: 1.5;
            }

            .back {
                text-align: center;
                margin-top: 24px;
            }

            .back a {
                display: inline-block;
                padding: 12px 18px;
                background: #111;
                color: white;
                text-decoration: none;
                border-radius: 10px;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="wrap">
            <h1>Join LeadForge</h1>
            <p class="sub">Contractor signup form restored. This step is UI only and not connected to the database yet.</p>

            <form>
                <div>
                    <label for="business_name">Business Name</label>
                    <input type="text" id="business_name" name="business_name" placeholder="Your business name" />
                </div>

                <div>
                    <label for="contact_name">Contact Name</label>
                    <input type="text" id="contact_name" name="contact_name" placeholder="Your full name" />
                </div>

                <div>
                    <label for="email">Email</label>
                    <input type="email" id="email" name="email" placeholder="you@example.com" />
                </div>

                <div>
                    <label for="phone">Phone</label>
                    <input type="text" id="phone" name="phone" placeholder="Your phone number" />
                </div>

                <div>
                    <label for="service">Primary Service</label>
                    <select id="service" name="service">
                        <option value="">Select a service</option>
                        <option>Roofing</option>
                        <option>Pressure Washing</option>
                        <option>Landscaping</option>
                        <option>Painting</option>
                        <option>Plumbing</option>
                        <option>Electrical</option>
                        <option>HVAC</option>
                        <option>Remodeling</option>
                    </select>
                </div>

                <div>
                    <label for="city">City</label>
                    <input type="text" id="city" name="city" placeholder="Your city" />
                </div>

                <div>
                    <label for="state">State</label>
                    <input type="text" id="state" name="state" placeholder="Your state" />
                </div>

                <div>
                    <label for="bio">Business Description</label>
                    <textarea id="bio" name="bio" placeholder="Tell homeowners about your company and services"></textarea>
                </div>

                <button type="button" class="btn">Submit Application</button>
            </form>

            <div class="note">
                This form is restored for layout testing only. Submit is intentionally inactive right now so we can keep the rebuild safe before reconnecting data.
            </div>

            <div class="back">
                <a href="/">Back Home</a>
            </div>
        </div>
    </body>
    </html>
    """
