<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>LeadForge | Exclusive Homeowner Requests</title>
  <style>
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      font-family: Arial, Helvetica, sans-serif;
      background: linear-gradient(180deg, #0f172a 0%, #111827 100%);
      color: #ffffff;
      line-height: 1.5;
    }

    a {
      text-decoration: none;
    }

    .wrap {
      width: 100%;
      max-width: 1200px;
      margin: 0 auto;
      padding: 24px;
    }

    .topbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 18px 0;
    }

    .brand {
      font-size: 28px;
      font-weight: 800;
      letter-spacing: 0.5px;
    }

    .brand span {
      color: #38bdf8;
    }

    .nav-links {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
    }

    .nav-links a {
      color: #ffffff;
      padding: 10px 16px;
      border: 1px solid rgba(255,255,255,0.15);
      border-radius: 999px;
      font-size: 14px;
      transition: 0.2s ease;
    }

    .nav-links a:hover {
      background: rgba(255,255,255,0.08);
    }

    .hero {
      display: grid;
      grid-template-columns: 1.1fr 0.9fr;
      gap: 32px;
      align-items: center;
      min-height: 78vh;
      padding: 40px 0 60px;
    }

    .hero-copy h1 {
      font-size: 54px;
      line-height: 1.05;
      margin-bottom: 18px;
      font-weight: 800;
    }

    .hero-copy p {
      font-size: 20px;
      color: #cbd5e1;
      margin-bottom: 28px;
      max-width: 700px;
    }

    .cta-row {
      display: flex;
      gap: 16px;
      flex-wrap: wrap;
      margin-bottom: 18px;
    }

    .btn {
      display: inline-block;
      padding: 16px 24px;
      border-radius: 14px;
      font-weight: 700;
      font-size: 16px;
      transition: 0.2s ease;
    }

    .btn-primary {
      background: #38bdf8;
      color: #0f172a;
    }

    .btn-primary:hover {
      transform: translateY(-1px);
      background: #67d3fb;
    }

    .btn-secondary {
      background: transparent;
      color: #ffffff;
      border: 1px solid rgba(255,255,255,0.18);
    }

    .btn-secondary:hover {
      background: rgba(255,255,255,0.08);
    }

    .micro {
      color: #94a3b8;
      font-size: 14px;
      margin-top: 10px;
    }

    .hero-card {
      background: rgba(255,255,255,0.06);
      border: 1px solid rgba(255,255,255,0.10);
      border-radius: 24px;
      padding: 28px;
      backdrop-filter: blur(8px);
      box-shadow: 0 20px 60px rgba(0,0,0,0.25);
    }

    .hero-card h3 {
      font-size: 24px;
      margin-bottom: 18px;
    }

    .flow {
      display: grid;
      gap: 14px;
    }

    .flow-item {
      background: rgba(255,255,255,0.05);
      border-radius: 16px;
      padding: 16px;
      border: 1px solid rgba(255,255,255,0.08);
    }

    .flow-item strong {
      display: block;
      font-size: 15px;
      margin-bottom: 4px;
      color: #7dd3fc;
    }

    .flow-item span {
      color: #e2e8f0;
      font-size: 15px;
    }

    .section {
      padding: 30px 0 70px;
    }

    .section h2 {
      font-size: 34px;
      margin-bottom: 14px;
    }

    .section-sub {
      color: #cbd5e1;
      font-size: 18px;
      margin-bottom: 28px;
      max-width: 800px;
    }

    .grid-3 {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 20px;
    }

    .card {
      background: rgba(255,255,255,0.05);
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 20px;
      padding: 24px;
    }

    .card h3 {
      font-size: 22px;
      margin-bottom: 10px;
    }

    .card p {
      color: #cbd5e1;
      font-size: 16px;
    }

    .footer {
      border-top: 1px solid rgba(255,255,255,0.10);
      margin-top: 20px;
      padding: 24px 0 40px;
      color: #94a3b8;
      font-size: 14px;
      text-align: center;
    }

    @media (max-width: 900px) {
      .hero {
        grid-template-columns: 1fr;
        min-height: auto;
      }

      .hero-copy h1 {
        font-size: 40px;
      }

      .grid-3 {
        grid-template-columns: 1fr;
      }

      .topbar {
        flex-direction: column;
        align-items: flex-start;
        gap: 14px;
      }
    }

    @media (max-width: 520px) {
      .hero-copy h1 {
        font-size: 34px;
      }

      .hero-copy p {
        font-size: 18px;
      }

      .btn {
        width: 100%;
        text-align: center;
      }

      .cta-row {
        flex-direction: column;
      }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <header class="topbar">
      <div class="brand">Lead<span>Forge</span></div>
      <nav class="nav-links">
        <a href="/contractor-signup">For Contractors</a>
        <a href="https://lead-forge-frontend-git-main-bcrsoutheast-langs-projects.vercel.app/homeowner2.html">For Homeowners</a>
        <a href="/admin">Admin</a>
      </nav>
    </header>

    <section class="hero">
      <div class="hero-copy">
        <h1>Exclusive homeowner requests for serious contractors.</h1>
        <p>
          LeadForge helps homeowners browse vetted contractors and submit a request directly.
          Contractors join free, get access to real opportunities, and unlock homeowner details
          only when they want to pursue the job.
        </p>

        <div class="cta-row">
          <a class="btn btn-primary" href="https://lead-forge-frontend-git-main-bcrsoutheast-langs-projects.vercel.app/homeowner2.html">
            I Need a Contractor
          </a>
          <a class="btn btn-secondary" href="/contractor-signup">
            I’m a Contractor
          </a>
        </div>

        <div class="micro">
          Browse → Choose → Submit request → Contractor unlocks opportunity
        </div>
      </div>

      <div class="hero-card">
        <h3>How LeadForge works</h3>
        <div class="flow">
          <div class="flow-item">
            <strong>1. Homeowner chooses a contractor</strong>
            <span>Homeowners select the contractor they want instead of sending the job to everyone.</span>
          </div>
          <div class="flow-item">
            <strong>2. Request is submitted</strong>
            <span>The lead goes into the system and appears in admin for review and tracking.</span>
          </div>
          <div class="flow-item">
            <strong>3. Contractor unlocks the opportunity</strong>
            <span>Contractors pay a $10 unlock fee to reveal full homeowner contact details.</span>
          </div>
          <div class="flow-item">
            <strong>4. Exclusive connection</strong>
            <span>The contractor gets direct access to the homeowner request and can follow up fast.</span>
          </div>
        </div>
      </div>
    </section>

    <section class="section">
      <h2>Built for quality over noise</h2>
      <p class="section-sub">
        LeadForge is designed to avoid junk leads, random bidding chaos, and shared homeowner requests.
        The goal is simple: cleaner intent, clearer opportunity, better experience.
      </p>

      <div class="grid-3">
        <div class="card">
          <h3>For Homeowners</h3>
          <p>
            Browse vetted contractor options and choose who you want to hear from before sending your request.
          </p>
        </div>

        <div class="card">
          <h3>For Contractors</h3>
          <p>
            Join free, get considered for real homeowner opportunities, and unlock details only when it makes sense.
          </p>
        </div>

        <div class="card">
          <h3>For Growth</h3>
          <p>
            Simple admin controls, working payment flow, and a clean path to scaling categories and cities later.
          </p>
        </div>
      </div>
    </section>

    <footer class="footer">
      LeadForge • Exclusive homeowner requests • Built for contractors who want real opportunities
    </footer>
  </div>
</body>
</html>
