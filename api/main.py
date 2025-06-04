from fastapi import FastAPI, Depends, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database.session import get_db
from database.models import Content, AffiliateProspect, ProspectStatus
from api.routers import prospects, campaigns, health, social, content, sequences, ab_tests, webhooks
from api.routers.templates import router as templates_router
from prometheus_client import Counter, generate_latest, REGISTRY
from uuid import uuid4
from datetime import datetime
import pytz
from tasks.scoring_tasks import score_prospect
from config.settings import settings
from urllib.parse import urlencode
import httpx
import secrets
import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)


app = FastAPI(title="Agentic Affiliate Outreach System")

# Templates for signup page
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(prospects.router)
app.include_router(templates_router)
app.include_router(campaigns.router)
app.include_router(health.router)
app.include_router(social.router)
app.include_router(content.router)
app.include_router(sequences.router)
app.include_router(ab_tests.router)
app.include_router(webhooks.router)

request_counter = Counter('http_requests_total', 'Total HTTP Requests', ['endpoint'])

@app.get("/")
def read_root():
    """Root endpoint for the outreach system."""
    return {"message": "Welcome to the Agentic Affiliate Outreach System"}

@app.get("/signup", response_class=HTMLResponse)
async def get_signup_page(request: Request, db: Session = Depends(get_db)):
    """Render the signup page with content from the database."""
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
    """Handle prospect signup and trigger scoring."""
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
        consent_timestamp=datetime.now(pytz.UTC),
        status=ProspectStatus.NEW  # Updated to use ENUM
    )
    
    db.add(prospect)
    db.commit()
    db.refresh(prospect)
    
    # Trigger scoring task
    score_prospect.delay(str(prospect.id))
    
    return {"message": "Signup successful, welcome!"}

@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """Expose Prometheus metrics."""
    request_counter.labels(endpoint="/metrics").inc()
    return generate_latest(REGISTRY)

@app.get("/auth/linkedin")
async def linkedin_auth():
    """Initiate LinkedIn OAuth flow."""
    state = secrets.token_urlsafe(16)
    params = {
        "response_type": "code",
        "client_id": settings.LINKEDIN_CLIENT_ID,
        "redirect_uri": settings.LINKEDIN_REDIRECT_URL,
        "state": state,
        "scope": "profile email openid",
    }
    auth_url = f"https://www.linkedin.com/oauth/v2/authorization?{urlencode(params)}"
    return {"auth_url": auth_url, "state": state}

@app.get("/auth/linkedin/callback")
async def linkedin_callback(request: Request, state: str, db: Session = Depends(get_db)):
    """Handle LinkedIn OAuth callback."""
    code = request.query_params.get("code")
    if request.query_params.get("state") != state:
        raise HTTPException(status_code=401, detail="Invalid state parameter")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://www.linkedin.com/oauth/v2/accessToken",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": settings.LINKEDIN_REDIRECT_URL,
                    "client_id": settings.LINKEDIN_CLIENT_ID,
                    "client_secret": settings.LINKEDIN_CLIENT_SECRET,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            token_data = response.json()
            return {"access_token": token_data["access_token"]}
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=400, detail=f"LinkedIn auth failed: {str(e)}")