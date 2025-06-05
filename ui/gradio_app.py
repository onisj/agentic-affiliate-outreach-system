import gradio as gr
import requests
import json
import logging
from typing import Dict, Any, Optional, Tuple
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
import time
import os
from datetime import datetime, timedelta
from typing import List
from services.lead_discovery import LeadDiscoveryService
from services.email_service import EmailService
from services.social_service import SocialService
from services.monitoring_service import MonitoringService
from services.scoring_service import ScoringService
from database.models import ProspectStatus, MessageType, MessageStatus
from database.session import get_db
from sqlalchemy.orm import Session
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
API_BASE_URL = "http://localhost:8000"
HEALTH_PORT = 7861
GRADIO_PORT = 7860

class APIClient:
    """Centralized API client for all backend interactions."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 10
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with error handling."""
        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {method} {endpoint} - {str(e)}")
            return {"error": f"API request failed: {str(e)}"}
        except json.JSONDecodeError:
            return {"error": "Invalid JSON response from API"}
    
    def get_prospects(self) -> Dict[str, Any]:
        """Fetch all prospects."""
        return self._make_request("GET", "/prospects/")
    
    def create_prospect(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new prospect."""
        return self._make_request("POST", "/prospects/", json=data)
    
    def get_campaigns(self) -> Dict[str, Any]:
        """Fetch all campaigns."""
        return self._make_request("GET", "/campaigns/")
    
    def create_campaign(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new campaign."""
        return self._make_request("POST", "/campaigns/", json=data)
    
    def start_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """Start a campaign."""
        return self._make_request("POST", f"/campaigns/{campaign_id}/start")
    
    def create_content(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new content."""
        return self._make_request("POST", "/content/", json=data)
    
    def create_template(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new template."""
        return self._make_request("POST", "/templates/", json=data)
    
    def create_sequence(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new sequence."""
        return self._make_request("POST", "/sequences/", json=data)
    
    def send_social_message(self, platform: str, prospect_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send a social media message."""
        return self._make_request("POST", f"/social/{platform}/{prospect_id}", json=data)
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health."""
        return self._make_request("GET", "/health/")

# Initialize API client
api_client = APIClient(API_BASE_URL)

class HealthCheckServer:
    """Health check server for container orchestration."""
    
    def __init__(self, port: int):
        self.port = port
        self.server = None
    
    def start(self):
        """Start the health check server in a background thread."""
        health_thread = Thread(target=self._run_server, daemon=True)
        health_thread.start()
        logger.info(f"Health check server started on port {self.port}")
    
    def _run_server(self):
        """Run the health check server."""
        try:
            self.server = HTTPServer(('0.0.0.0', self.port), HealthHandler)
            self.server.serve_forever()
        except Exception as e:
            logger.error(f"Health server error: {e}")
    
    def check_health(self) -> Dict[str, Any]:
        """Perform health check."""
        try:
            api_health = api_client.health_check()
            api_healthy = "error" not in api_health
            
            return {
                "status": "healthy" if api_healthy else "unhealthy",
                "service": "gradio",
                "api_connection": "connected" if api_healthy else "disconnected",
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "service": "gradio",
                "error": str(e),
                "timestamp": time.time()
            }

class HealthHandler(BaseHTTPRequestHandler):
    """HTTP handler for health check requests."""
    
    def do_GET(self):
        if self.path == '/health':
            health_data = health_server.check_health()
            status_code = 200 if health_data["status"] == "healthy" else 503
            
            self.send_response(status_code)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(health_data).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Suppress default logging
        pass

# Initialize health server
health_server = HealthCheckServer(HEALTH_PORT)

# Gradio interface functions
def format_response(response: Dict[str, Any]) -> str:
    """Format API response for display."""
    if "error" in response:
        return f"❌ Error: {response['error']}"
    return f"✅ Success: {json.dumps(response, indent=2)}"

def create_prospect_ui(email: str, first_name: str, last_name: str, 
                      company: str, website: str) -> str:
    """Create prospect through UI."""
    if not email:
        return "❌ Email is required"
    
    data = {
        "email": email,
        "first_name": first_name or None,
        "last_name": last_name or None,
        "company": company or None,
        "website": website or None,
        "lead_source": "gradio_ui",
        "consent_given": True
    }
    
    response = api_client.create_prospect(data)
    return format_response(response)

def refresh_prospects() -> str:
    """Refresh prospects list."""
    response = api_client.get_prospects()
    return format_response(response)

def create_content_ui(name: str, content_type: str, title: str, 
                     headline: str, description: str, cta: str) -> str:
    """Create content through UI."""
    if not all([name, content_type]):
        return "❌ Name and content type are required"
    
    data = {
        "name": name,
        "content_type": content_type,
        "data": {
            "title": title,
            "headline": headline,
            "description": description,
            "cta": cta
        }
    }
    
    response = api_client.create_content(data)
    return format_response(response)

def create_template_ui(name: str, subject: str, content: str, message_type: str) -> str:
    """Create template through UI."""
    if not all([name, subject, content, message_type]):
        return "❌ All fields are required"
    
    data = {
        "name": name,
        "subject": subject,
        "content": content,
        "message_type": message_type
    }
    
    response = api_client.create_template(data)
    return format_response(response)

def create_sequence_ui(campaign_id: str, step_number: int, template_id: str, 
                      delay_days: int, condition: str) -> str:
    """Create sequence through UI."""
    if not all([campaign_id, template_id]):
        return "❌ Campaign ID and Template ID are required"
    
    try:
        condition_data = json.loads(condition) if condition else {}
    except json.JSONDecodeError:
        return "❌ Invalid JSON in condition field"
    
    data = {
        "campaign_id": campaign_id,
        "step_number": int(step_number),
        "template_id": template_id,
        "delay_days": int(delay_days),
        "condition": condition_data
    }
    
    response = api_client.create_sequence(data)
    return format_response(response)

def start_campaign_ui(campaign_id: str) -> str:
    """Start campaign through UI."""
    if not campaign_id:
        return "❌ Campaign ID is required"
    
    response = api_client.start_campaign(campaign_id)
    return format_response(response)

def send_social_message_ui(prospect_id: str, template_id: str, platform: str) -> str:
    """Send social message through UI."""
    if not all([prospect_id, template_id, platform]):
        return "❌ All fields are required"
    
    data = {"template_id": template_id}
    response = api_client.send_social_message(platform, prospect_id, data)
    return format_response(response)

class AffiliateOutreachUI:
    def __init__(self):
        self.lead_discovery = LeadDiscoveryService()
        self.email_service = EmailService()
        self.social_service = SocialService()
        self.monitoring_service = MonitoringService()
        self.scoring_service = ScoringService()
        self.db = next(get_db())

    def discover_prospects(
        self,
        platform: str,
        keywords: str,
        min_followers: int,
        max_prospects: int
    ) -> Dict[str, Any]:
        """Discover prospects on specified platform."""
        try:
            keywords_list = [k.strip() for k in keywords.split(',')]
            results = self.lead_discovery.discover_prospects(
                platform=platform,
                keywords=keywords_list,
                min_followers=min_followers,
                max_prospects=max_prospects,
                db=self.db
            )
            return {
                "status": "success",
                "message": f"Found {len(results.get('prospects', []))} prospects",
                "data": results
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def send_outreach(
        self,
        prospect_ids: List[str],
        message_type: str,
        template_id: str,
        schedule_time: str = None
    ) -> Dict[str, Any]:
        """Send outreach messages to selected prospects."""
        try:
            if message_type == "email":
                service = self.email_service
            else:
                service = self.social_service

            results = []
            for prospect_id in prospect_ids:
                result = service.send_message(
                    prospect_id=prospect_id,
                    template_id=template_id,
                    schedule_time=schedule_time,
                    db=self.db
                )
                results.append(result)

            return {
                "status": "success",
                "message": f"Sent {len(results)} messages",
                "data": results
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_prospect_metrics(self) -> Dict[str, Any]:
        """Get metrics about prospects and outreach."""
        try:
            total_prospects = self.db.query(AffiliateProspect).count()
            active_prospects = self.db.query(AffiliateProspect).filter(
                AffiliateProspect.status == ProspectStatus.ACTIVE
            ).count()
            total_messages = self.db.query(MessageLog).count()
            successful_messages = self.db.query(MessageLog).filter(
                MessageLog.status == MessageStatus.SENT
            ).count()

            return {
                "status": "success",
                "data": {
                    "total_prospects": total_prospects,
                    "active_prospects": active_prospects,
                    "total_messages": total_messages,
                    "successful_messages": successful_messages
                }
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_prospect_list(
        self,
        status: str = None,
        platform: str = None,
        min_score: float = None
    ) -> pd.DataFrame:
        """Get list of prospects with filters."""
        try:
            query = self.db.query(AffiliateProspect)
            
            if status:
                query = query.filter(AffiliateProspect.status == status)
            if platform:
                query = query.filter(AffiliateProspect.platform == platform)
            if min_score:
                query = query.filter(AffiliateProspect.qualification_score >= min_score)

            prospects = query.all()
            data = []
            for p in prospects:
                data.append({
                    "ID": str(p.id),
                    "Name": f"{p.first_name} {p.last_name}",
                    "Email": p.email,
                    "Platform": p.platform,
                    "Status": p.status,
                    "Score": p.qualification_score,
                    "Last Contact": p.last_contact_date
                })
            return pd.DataFrame(data)
        except Exception as e:
            return pd.DataFrame()

    def create_dashboard(self) -> gr.Blocks:
        """Create the main dashboard interface."""
        with gr.Blocks(title="Affiliate Outreach System") as dashboard:
            gr.Markdown("# Affiliate Outreach System Dashboard")
            
            with gr.Tab("Prospect Discovery"):
                with gr.Row():
                    with gr.Column():
                        platform = gr.Dropdown(
                            choices=["twitter", "linkedin", "instagram"],
                            label="Platform"
                        )
                        keywords = gr.Textbox(
                            label="Keywords (comma-separated)",
                            placeholder="affiliate, marketing, digital"
                        )
                        min_followers = gr.Number(
                            label="Minimum Followers",
                            value=1000
                        )
                        max_prospects = gr.Number(
                            label="Maximum Prospects",
                            value=100
                        )
                        discover_btn = gr.Button("Discover Prospects")
                    
                    with gr.Column():
                        discovery_output = gr.JSON(label="Discovery Results")
                        discovery_metrics = gr.JSON(label="Metrics")

            with gr.Tab("Outreach Management"):
                with gr.Row():
                    with gr.Column():
                        prospect_list = gr.Dataframe(
                            headers=["ID", "Name", "Email", "Platform", "Status", "Score", "Last Contact"],
                            label="Prospects"
                        )
                        refresh_btn = gr.Button("Refresh List")
                    
                    with gr.Column():
                        message_type = gr.Dropdown(
                            choices=["email", "twitter", "linkedin"],
                            label="Message Type"
                        )
                        template_id = gr.Textbox(
                            label="Template ID"
                        )
                        schedule_time = gr.Textbox(
                            label="Schedule Time (optional)",
                            placeholder="YYYY-MM-DD HH:MM"
                        )
                        send_btn = gr.Button("Send Messages")

            with gr.Tab("Monitoring"):
                with gr.Row():
                    with gr.Column():
                        metrics_plot = gr.Plot(label="Outreach Metrics")
                        refresh_metrics_btn = gr.Button("Refresh Metrics")
                    
                    with gr.Column():
                        alerts_list = gr.JSON(label="Active Alerts")
                        system_status = gr.JSON(label="System Status")

            # Event handlers
            discover_btn.click(
                fn=self.discover_prospects,
                inputs=[platform, keywords, min_followers, max_prospects],
                outputs=[discovery_output]
            )

            refresh_btn.click(
                fn=self.get_prospect_list,
                outputs=[prospect_list]
            )

            send_btn.click(
                fn=self.send_outreach,
                inputs=[prospect_list, message_type, template_id, schedule_time],
                outputs=[discovery_output]
            )

            refresh_metrics_btn.click(
                fn=self.get_prospect_metrics,
                outputs=[metrics_plot, alerts_list, system_status]
            )

        return dashboard

def create_gradio_app():
    """Create and configure the Gradio application."""
    
    ui = AffiliateOutreachUI()
    dashboard = ui.create_dashboard()
    
    return dashboard

def main():
    """Main function to start the application."""
    try:
        # Start health check server
        health_server.start()
        
        # Create and launch Gradio app
        demo = create_gradio_app()
        
        logger.info(f"Starting Gradio application on port {GRADIO_PORT}")
        demo.launch(
            server_name="0.0.0.0",
            server_port=GRADIO_PORT,
            show_error=True,
            show_tips=True
        )
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise

if __name__ == "__main__":
    main()