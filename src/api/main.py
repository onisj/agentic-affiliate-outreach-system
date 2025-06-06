from fastapi import FastAPI, Depends, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from prometheus_client import Counter, generate_latest, REGISTRY, make_asgi_app
from uuid import uuid4
from datetime import datetime
import pytz
import httpx
import secrets
import logging
from urllib.parse import urlencode
from api.middleware.metrics import metrics_middleware
from fastapi.exception_handlers import RequestValidationError, request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
import os
from pathlib import Path
from sqlalchemy import text

# Local imports
from database.session import get_db
from database.models import Content, AffiliateProspect, ProspectStatus
from api.routers import (prospects, campaigns, health, social, content, 
                        sequences, ab_tests, webhooks)
from api.routers.templates import router as templates_router
from app.tasks.scoring_tasks import score_prospect
from config.settings import settings
from api.endpoints import ab_testing, responses

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress warnings
import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)

# Initialize FastAPI app
app = FastAPI(
    title="Agentic Affiliate Outreach System",
    description="A comprehensive system for managing affiliate outreach campaigns",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize templates with absolute path
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Prometheus metrics
request_counter = Counter('http_requests_total', 'Total HTTP Requests', ['endpoint'])

# Add metrics middleware
app.middleware("http")(metrics_middleware)

# Add Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(prospects.router, prefix="/prospects", tags=["prospects"])
app.include_router(campaigns.router, prefix="/campaigns", tags=["campaigns"])
app.include_router(social.router, prefix="/social", tags=["social"])
app.include_router(content.router)
app.include_router(sequences.router, prefix="/sequences", tags=["sequences"])
app.include_router(ab_tests.router, prefix="/ab-tests", tags=["ab-tests"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
app.include_router(templates_router, prefix="/templates", tags=["templates"])
app.include_router(ab_testing.router)
## app.include_router(message_templates.router)  # Disabled to avoid /templates route conflict
app.include_router(responses.router, prefix="/responses", tags=["responses"])


@app.get("/", tags=["root"])
async def root():
    """Root endpoint for the outreach system."""
    request_counter.labels(endpoint="/").inc()
    return {
        "message": "Welcome to the Agentic Affiliate Outreach System",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/signup", response_class=HTMLResponse, tags=["signup"])
async def get_signup_page(request: Request, db: Session = Depends(get_db)):
    """Render the signup page with content from the database."""
    try:
        request_counter.labels(endpoint="/signup").inc()
        
        content = db.query(Content).filter(
            Content.content_type == "landing_page", 
            Content.name == "default_signup"
        ).first()
        
        context = {"request": request}
        if content:
            context.update(content.data)
        
        return templates.TemplateResponse("prospect_signup.html", context)
    
    except Exception as e:
        logger.error(f"Error rendering signup page: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/signup", tags=["signup"])
async def submit_signup(
    email: str = Form(...),
    first_name: str = Form(None),
    last_name: str = Form(None),
    company: str = Form(None),
    website: str = Form(None),
    db: Session = Depends(get_db)
):
    """Handle prospect signup and trigger scoring."""
    try:
        request_counter.labels(endpoint="/signup").inc()
        
        # Check for existing prospect
        existing = db.query(AffiliateProspect).filter(
            AffiliateProspect.email == email
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create new prospect
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
            status=ProspectStatus.NEW
        )
        
        db.add(prospect)
        db.commit()
        db.refresh(prospect)
        
        # Trigger async scoring task
        try:
            score_prospect.delay(str(prospect.id))
        except Exception as e:
            logger.warning(f"Failed to trigger scoring task: {e}")
        
        return {
            "message": "Signup successful, welcome!",
            "prospect_id": str(prospect.id)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing signup: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/metrics", response_class=PlainTextResponse, tags=["monitoring"])
async def metrics():
    """Expose Prometheus metrics."""
    request_counter.labels(endpoint="/metrics").inc()
    return generate_latest(REGISTRY)


@app.get("/auth/linkedin", tags=["authentication"])
async def linkedin_auth():
    """Initiate LinkedIn OAuth flow."""
    try:
        request_counter.labels(endpoint="/auth/linkedin").inc()
        
        if not all([settings.LINKEDIN_CLIENT_ID, settings.LINKEDIN_REDIRECT_URL]):
            raise HTTPException(
                status_code=500, 
                detail="LinkedIn OAuth not properly configured"
            )
        
        state = secrets.token_urlsafe(32)
        params = {
            "response_type": "code",
            "client_id": settings.LINKEDIN_CLIENT_ID,
            "redirect_uri": settings.LINKEDIN_REDIRECT_URL,
            "state": state,
            "scope": "profile email openid",
        }
        
        auth_url = f"https://www.linkedin.com/oauth/v2/authorization?{urlencode(params)}"
        
        return {
            "auth_url": auth_url,
            "state": state
        }
    
    except Exception as e:
        logger.error(f"Error initiating LinkedIn auth: {e}")
        raise HTTPException(status_code=500, detail="Authentication error")


@app.get("/auth/linkedin/callback", tags=["authentication"])
async def linkedin_callback(
    request: Request, 
    code: str = None,
    state: str = None,
    error: str = None,
    db: Session = Depends(get_db)
):
    """Handle LinkedIn OAuth callback."""
    try:
        request_counter.labels(endpoint="/auth/linkedin/callback").inc()
        
        if error:
            logger.warning(f"LinkedIn OAuth error: {error}")
            raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
        
        if not code or not state:
            raise HTTPException(status_code=400, detail="Missing authorization code or state")
        
        # Exchange code for access token
        async with httpx.AsyncClient(timeout=30.0) as client:
            token_response = await client.post(
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
            
            if token_response.status_code != 200:
                raise HTTPException(
                    status_code=400, 
                    detail="Failed to exchange authorization code"
                )
            
            token_data = token_response.json()
            access_token = token_data.get("access_token")
            
            if not access_token:
                raise HTTPException(status_code=400, detail="No access token received")
            
            return {
                "message": "LinkedIn authentication successful",
                "access_token": access_token
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in LinkedIn callback: {e}")
        raise HTTPException(status_code=500, detail="Authentication callback error")


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Custom 404 handler."""
    return JSONResponse(
        status_code=404,
        content={"detail": exc.detail if hasattr(exc, 'detail') else "Not found"}
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: HTTPException):
    """Custom 500 handler."""
    logger.error(f"Internal server error on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return await request_validation_exception_handler(request, exc)


@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy"}


@app.get("/version")
async def version():
    """Return the API version."""
    return {"version": "1.0.0"}


@app.get("/db-status")
async def db_status(db: Session = Depends(get_db)):
    """Check database connection status."""
    try:
        # Try to execute a simple query (use text for SQLAlchemy 2.x compatibility)
        db.execute(text("SELECT 1"))
        return {"status": "connected"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )