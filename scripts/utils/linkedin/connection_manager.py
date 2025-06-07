#!/usr/bin/env python3
"""
LinkedIn Connection Manager Script

This script demonstrates how to:
1. Send connection invitations
2. Track connection status
3. Generate connection reports
4. Export connection data
"""

import sys
import json
import csv
from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging
from pathlib import Path
import pandas as pd

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from app.services.social_service import SocialService
from database.session import get_db
from database.models import MessageLog, MessageType, MessageStatus
from config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.social_service = SocialService()
        self.db = next(get_db())

    def get_connections(self, start: int = 0, count: int = 50) -> Dict[str, Any]:
        """Fetch LinkedIn connections with pagination."""
        logger.info(f"Fetching connections (start: {start}, count: {count})")
        result = self.social_service.get_linkedin_connections(start, count)
        
        if not result["success"]:
            logger.error(f"Failed to fetch connections: {result['error']}")
            return None
            
        return result["connections"]

    def get_all_connections(self) -> List[Dict[str, Any]]:
        """Fetch all LinkedIn connections."""
        all_connections = []
        start = 0
        count = 50
        
        while True:
            connections = self.get_connections(start, count)
            if not connections:
                break
                
            all_connections.extend(connections.get("elements", []))
            
            if len(connections.get("elements", [])) < count:
                break
                
            start += count
        
        return all_connections

    def send_connection_invitation(self, prospect_id: str, urn: str, message: str) -> Dict[str, Any]:
        """Send a LinkedIn connection invitation."""
        logger.info(f"Sending connection invitation to {urn}")
        result = self.social_service.send_linkedin_invitation(prospect_id, urn, message)
        
        if not result["success"]:
            logger.error(f"Failed to send invitation: {result['error']}")
            return None
            
        return result

    def get_invitation_status(self, prospect_id: str) -> Dict[str, Any]:
        """Get status of connection invitations for a prospect."""
        logger.info(f"Checking invitation status for prospect: {prospect_id}")
        invitations = self.db.query(MessageLog).filter(
            MessageLog.prospect_id == prospect_id,
            MessageLog.message_type == MessageType.LINKEDIN_INVITATION.value
        ).order_by(MessageLog.sent_at.desc()).all()
        
        return [
            {
                "id": inv.id,
                "sent_at": inv.sent_at.isoformat(),
                "status": inv.status,
                "external_message_id": inv.external_message_id
            }
            for inv in invitations
        ]

    def generate_connection_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate a report of connection activities."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get all invitations in the date range
        invitations = self.db.query(MessageLog).filter(
            MessageLog.message_type == MessageType.LINKEDIN_INVITATION.value,
            MessageLog.sent_at >= start_date,
            MessageLog.sent_at <= end_date
        ).all()
        
        # Get current connections
        current_connections = self.get_all_connections()
        
        # Calculate metrics
        total_invitations = len(invitations)
        successful_invitations = sum(1 for inv in invitations if inv.status == MessageStatus.SENT.value)
        current_connection_count = len(current_connections)
        
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "invitations": {
                "total": total_invitations,
                "successful": successful_invitations,
                "success_rate": (successful_invitations / total_invitations * 100) if total_invitations > 0 else 0
            },
            "connections": {
                "current": current_connection_count,
                "growth": current_connection_count - (current_connection_count - successful_invitations),
                "growth_rate": (successful_invitations / current_connection_count * 100) if current_connection_count > 0 else 0
            }
        }

    def export_connection_data(self, data: Dict[str, Any], filename: str):
        """Export connection data to JSON."""
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Data exported to {filename}")

    def generate_connection_metrics(self, days: int = 30) -> pd.DataFrame:
        """Generate connection metrics over time."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Create date range
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Initialize DataFrame
        df = pd.DataFrame(index=date_range, columns=['invitations', 'connections'])
        df = df.fillna(0)
        
        # Get all invitations
        invitations = self.db.query(MessageLog).filter(
            MessageLog.message_type == MessageType.LINKEDIN_INVITATION.value,
            MessageLog.sent_at >= start_date,
            MessageLog.sent_at <= end_date
        ).all()
        
        # Aggregate data by date
        for invitation in invitations:
            sent_date = invitation.sent_at.date()
            df.loc[sent_date, 'invitations'] += 1
            
            if invitation.status == MessageStatus.SENT.value:
                df.loc[sent_date, 'connections'] += 1
        
        # Calculate cumulative connections
        df['cumulative_connections'] = df['connections'].cumsum()
        
        return df

def main():
    # Example usage
    manager = ConnectionManager()
    
    try:
        # Get all connections
        connections = manager.get_all_connections()
        logger.info(f"Total connections: {len(connections)}")
        
        # Generate connection report
        report = manager.generate_connection_report()
        
        # Export report
        manager.export_connection_data(report, "connection_report.json")
        
        # Generate and save metrics
        metrics = manager.generate_connection_metrics()
        metrics.to_csv("connection_metrics.csv")
        
        # Print summary
        logger.info("\nConnection Report Summary:")
        logger.info(f"Total Invitations: {report['invitations']['total']}")
        logger.info(f"Success Rate: {report['invitations']['success_rate']:.2f}%")
        logger.info(f"Current Connections: {report['connections']['current']}")
        logger.info(f"Growth Rate: {report['connections']['growth_rate']:.2f}%")
        
    except Exception as e:
        logger.error(f"Error managing connections: {str(e)}")

if __name__ == "__main__":
    main() 