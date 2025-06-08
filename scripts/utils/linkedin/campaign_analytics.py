#!/usr/bin/env python3
"""
LinkedIn Campaign Analytics Script

This script demonstrates how to:
1. Track message performance
2. Calculate engagement metrics
3. Generate campaign reports
4. Export analytics data
"""

import sys
import json
import csv
from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from services.social_service import SocialService
from database.session import get_db
from database.models import MessageLog, MessageType, MessageStatus
from config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CampaignAnalytics:
    def __init__(self):
        self.social_service = SocialService()
        self.db = next(get_db())

    def get_campaign_messages(self, campaign_id: str) -> List[Dict[str, Any]]:
        """Fetch all messages for a campaign."""
        logger.info(f"Fetching messages for campaign: {campaign_id}")
        messages = self.db.query(MessageLog).filter(
            MessageLog.campaign_id == campaign_id,
            MessageLog.message_type == MessageType.LINKEDIN.value
        ).all()
        
        return [
            {
                "id": msg.id,
                "prospect_id": msg.prospect_id,
                "content": msg.content,
                "sent_at": msg.sent_at.isoformat(),
                "status": msg.status,
                "external_message_id": msg.external_message_id
            }
            for msg in messages
        ]

    def get_message_analytics(self, message_id: str) -> Dict[str, Any]:
        """Fetch analytics for a specific message."""
        logger.info(f"Fetching analytics for message: {message_id}")
        result = self.social_service.get_linkedin_analytics(message_id)
        
        if not result["success"]:
            logger.error(f"Failed to fetch analytics: {result['error']}")
            return None
            
        return result["analytics"]

    def calculate_engagement_metrics(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate engagement metrics for a set of messages."""
        total_messages = len(messages)
        total_views = 0
        total_clicks = 0
        total_responses = 0
        successful_messages = 0
        
        for message in messages:
            if message["status"] == MessageStatus.SENT.value:
                successful_messages += 1
                
                analytics = self.get_message_analytics(message["external_message_id"])
                if analytics:
                    total_views += analytics.get("views", 0)
                    total_clicks += analytics.get("clicks", 0)
                    total_responses += analytics.get("responses", 0)
        
        return {
            "total_messages": total_messages,
            "successful_messages": successful_messages,
            "delivery_rate": (successful_messages / total_messages * 100) if total_messages > 0 else 0,
            "total_views": total_views,
            "total_clicks": total_clicks,
            "total_responses": total_responses,
            "view_rate": (total_views / successful_messages * 100) if successful_messages > 0 else 0,
            "click_rate": (total_clicks / total_views * 100) if total_views > 0 else 0,
            "response_rate": (total_responses / total_views * 100) if total_views > 0 else 0
        }

    def generate_time_series(self, messages: List[Dict[str, Any]], days: int = 30) -> pd.DataFrame:
        """Generate time series data for message performance."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Create date range
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Initialize DataFrame
        df = pd.DataFrame(index=date_range, columns=['messages', 'views', 'clicks', 'responses'])
        df = df.fillna(0)
        
        # Aggregate data by date
        for message in messages:
            sent_date = datetime.fromisoformat(message["sent_at"]).date()
            if start_date.date() <= sent_date <= end_date.date():
                df.loc[sent_date, 'messages'] += 1
                
                analytics = self.get_message_analytics(message["external_message_id"])
                if analytics:
                    df.loc[sent_date, 'views'] += analytics.get("views", 0)
                    df.loc[sent_date, 'clicks'] += analytics.get("clicks", 0)
                    df.loc[sent_date, 'responses'] += analytics.get("responses", 0)
        
        return df

    def plot_metrics(self, df: pd.DataFrame, output_file: str):
        """Plot engagement metrics over time."""
        plt.figure(figsize=(12, 6))
        
        # Plot metrics
        plt.plot(df.index, df['views'], label='Views', marker='o')
        plt.plot(df.index, df['clicks'], label='Clicks', marker='s')
        plt.plot(df.index, df['responses'], label='Responses', marker='^')
        
        # Customize plot
        plt.title('LinkedIn Campaign Performance Over Time')
        plt.xlabel('Date')
        plt.ylabel('Count')
        plt.legend()
        plt.grid(True)
        plt.xticks(rotation=45)
        
        # Save plot
        plt.tight_layout()
        plt.savefig(output_file)
        plt.close()
        
        logger.info(f"Plot saved to {output_file}")

    def export_to_csv(self, data: Dict[str, Any], filename: str):
        """Export analytics data to CSV."""
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Metric', 'Value'])
            for key, value in data.items():
                writer.writerow([key, value])
        
        logger.info(f"Data exported to {filename}")

def main():
    # Example usage
    analytics = CampaignAnalytics()
    
    # Example campaign ID (replace with actual campaign ID)
    campaign_id = "your-campaign-id"
    
    try:
        # Get campaign messages
        messages = analytics.get_campaign_messages(campaign_id)
        
        # Calculate engagement metrics
        metrics = analytics.calculate_engagement_metrics(messages)
        
        # Generate time series data
        time_series = analytics.generate_time_series(messages)
        
        # Plot metrics
        analytics.plot_metrics(time_series, f"campaign_analytics_{campaign_id}.png")
        
        # Export data
        analytics.export_to_csv(metrics, f"campaign_metrics_{campaign_id}.csv")
        
        # Print summary
        logger.info("\nCampaign Analytics Summary:")
        logger.info(f"Total Messages: {metrics['total_messages']}")
        logger.info(f"Delivery Rate: {metrics['delivery_rate']:.2f}%")
        logger.info(f"View Rate: {metrics['view_rate']:.2f}%")
        logger.info(f"Click Rate: {metrics['click_rate']:.2f}%")
        logger.info(f"Response Rate: {metrics['response_rate']:.2f}%")
        
    except Exception as e:
        logger.error(f"Error analyzing campaign: {str(e)}")

if __name__ == "__main__":
    main() 