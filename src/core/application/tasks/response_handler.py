"""
Response Handler Task

This module implements the response handling task for processing prospect responses.
"""

from services.outreach.response_tracking import ResponseTrackingService

def handle_prospect_response(message_id: str, response_type: str, content: str, db):
    response_service = ResponseTrackingService(db)
    response_service.track_response(message_id, response_type, content) 