from fastapi import FastAPI, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from sqlalchemy.orm import Session
from api.routers import prospects, templates, campaigns, health, social, content, sequences
from database.models import AffiliateProspect, Content
from database.session import get_db
from tasks.scoring_tasks import score_prospect
from uuid import uuid4
from datetime import datetime
from prometheus_client import Counter, generate_latest, REGISTRY
from fastapi.responses import PlainTextResponse

app = FastAPI(title="Agentic Affiliate Outreach System", version="1.0.0")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(prospects.router)
app.include_router(templates.router)
app.include_router(campaigns.router)
app.include_router(health.router)
app.include_router(social.router)
app.include_router(content.router)
app.include_router(sequences.router)


request_counter = Counter('http_requests_total', 'Total HTTP Requests', ['endpoint'])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Agentic Affiliate Outreach System"}

@app.get("/signup", response_class=HTMLResponse)
async def get_signup_page(request: Request, db: Session = Depends(get_db)):
    content = db.query(Content).filter(Content.content_type == "landing_page", Content.name == "default_signup").first()
    context = {"request": request}
    if content:
        context.update(content.data)
    return templates.TemplateResponse("signup.html", context)

@app.post("/signup")
async def submit_signup(
    email: str = Form(...),
    first_name: str = Form(None),
    last_name: str = Form(None),
    company: str = Form(None),
    website: str = Form(None),
    db: Session = Depends(get_db)
):
    existing = db.query(AffiliateProspect).filter(AffiliateProspect.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    prospect = AffiliateProspect(
        id=uuid4(),
        email=email,
        first_name=first_name,
        last_name=last_name,
        company=company,
        website=website,
        lead_source="signup_form",
        consent_given=True,
        consent_timestamp=datetime.utcnow(),
        status="new"
    )
    
    db.add(prospect)
    db.commit()
    db.refresh(prospect)
    
    # Trigger scoring
    score_prospect.delay(str(prospect.id))
    
    return {"message": "Signup successful, welcome!"}

@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    request_counter.labels(endpoint="/metrics").inc()
    return generate_latest(REGISTRY)