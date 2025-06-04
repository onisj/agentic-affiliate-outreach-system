import gradio as gr
import requests
from typing import Dict, Any
from config.settings import settings
import logging
import json
from uuid import uuid4

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_BASE_URL = "http://localhost:8000"

def get_prospects() -> Dict[str, Any]:
    try:
        response = requests.get(f"{API_BASE_URL}/prospects/")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching prospects: {str(e)}")
        return {"error": str(e)}

def create_prospect(email: str, first_name: str, last_name: str, company: str, website: str) -> Dict[str, Any]:
    try:
        payload = {
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "company": company,
            "website": website,
            "lead_source": "manual",
            "consent_given": True
        }
        response = requests.post(f"{API_BASE_URL}/prospects/", json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error creating prospect: {str(e)}")
        return {"error": str(e)}

def create_content(name: str, content_type: str, title: str, headline: str, description: str, cta: str) -> Dict[str, Any]:
    try:
        payload = {
            "name": name,
            "content_type": content_type,
            "data": {
                "title": title,
                "headline": headline,
                "description": description,
                "cta": cta
            }
        }
        response = requests.post(f"{API_BASE_URL}/content/", json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error creating content: {str(e)}")
        return {"error": str(e)}

def create_template(name: str, subject: str, content: str, message_type: str) -> Dict[str, Any]:
    try:
        payload = {
            "name": name,
            "subject": subject,
            "content": content,
            "message_type": message_type
        }
        response = requests.post(f"{API_BASE_URL}/templates/", json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error creating template: {str(e)}")
        return {"error": str(e)}

def create_sequence(campaign_id: str, step_number: int, template_id: str, delay_days: int, condition: str) -> Dict[str, Any]:
    try:
        payload = {
            "campaign_id": campaign_id,
            "step_number": step_number,
            "template_id": template_id,
            "delay_days": delay_days,
            "condition": json.loads(condition) if condition else {}
        }
        response = requests.post(f"{API_BASE_URL}/sequences/", json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error creating sequence: {str(e)}")
        return {"error": str(e)}

def start_campaign(campaign_id: str) -> Dict[str, Any]:
    try:
        response = requests.post(f"{API_BASE_URL}/campaigns/{campaign_id}/start")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error starting campaign: {str(e)}")
        return {"error": str(e)}

def send_social_message(prospect_id: str, template_id: str, platform: str) -> Dict[str, Any]:
    try:
        endpoint = f"{API_BASE_URL}/social/{platform}/{prospect_id}"
        payload = {"template_id": template_id}
        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error sending social message: {str(e)}")
        return {"error": str(e)}

with gr.Blocks() as demo:
    gr.Markdown("# Agentic Affiliate Outreach System (Phases 2 & 3)")
    
    with gr.Tab("Prospects"):
        with gr.Row():
            email = gr.Textbox(label="Email")
            first_name = gr.Textbox(label="First Name")
            last_name = gr.Textbox(label="Last Name")
            company = gr.Textbox(label="Company")
            website = gr.Textbox(label="Website")
        create_btn = gr.Button("Create Prospect")
        create_output = gr.JSON()
        gr.Markdown("## Prospect List")
        prospect_list = gr.JSON()
        refresh_prospects = gr.Button("Refresh Prospects")
    
    with gr.Tab("Landing Page Content"):
        with gr.Row():
            content_name = gr.Textbox(label="Content Name", value="default_signup")
            content_type = gr.Textbox(label="Content Type", value="landing_page")
            content_title = gr.Textbox(label="Title")
            content_headline = gr.Textbox(label="Headline")
            content_description = gr.Textbox(label="Description")
            content_cta = gr.Textbox(label="CTA")
        content_btn = gr.Button("Create Content")
        content_output = gr.JSON()
    
    with gr.Tab("Templates"):
        with gr.Row():
            template_name = gr.Textbox(label="Template Name")
            template_subject = gr.Textbox(label="Subject")
            template_content = gr.Textbox(label="Content", lines=5)
            template_type = gr.Dropdown(["email", "linkedin", "twitter"], label="Message Type")
        template_btn = gr.Button("Create Template")
        template_output = gr.JSON()
    
    with gr.Tab("Sequences"):
        with gr.Row():
            seq_campaign_id = gr.Textbox(label="Campaign ID")
            seq_step_number = gr.Number(label="Step Number")
            seq_template_id = gr.Textbox(label="Template ID")
            seq_delay_days = gr.Number(label="Delay Days")
            seq_condition = gr.Textbox(label="Condition (JSON)")
        seq_btn = gr.Button("Create Sequence")
        seq_output = gr.JSON()
    
    with gr.Tab("Campaigns"):
        campaign_id = gr.Textbox(label="Campaign ID")
        start_campaign_btn = gr.Button("Start Campaign")
        campaign_output = gr.JSON()
    
    with gr.Tab("Social Outreach"):
        social_prospect_id = gr.Textbox(label="Prospect ID")
        social_template_id = gr.Textbox(label="Template ID")
        social_platform = gr.Dropdown(["twitter", "linkedin"], label="Platform")
        social_send_btn = gr.Button("Send Social Message")
        social_output = gr.JSON()
    
    create_btn.click(create_prospect, inputs=[email, first_name, last_name, company, website], outputs=create_output)
    refresh_prospects.click(get_prospects, outputs=prospect_list)
    content_btn.click(create_content, inputs=[content_name, content_type, content_title, content_headline, content_description, content_cta], outputs=content_output)
    template_btn.click(create_template, inputs=[template_name, template_subject, template_content, template_type], outputs=template_output)
    seq_btn.click(create_sequence, inputs=[seq_campaign_id, seq_step_number, seq_template_id, seq_delay_days, seq_condition], outputs=seq_output)
    start_campaign_btn.click(start_campaign, inputs=[campaign_id], outputs=campaign_output)
    social_send_btn.click(send_social_message, inputs=[social_prospect_id, social_template_id, social_platform], outputs=social_output)

demo.launch(server_name="0.0.0.0", server_port=7860)