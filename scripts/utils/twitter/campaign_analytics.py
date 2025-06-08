#!/usr/bin/env python3
"""
Twitter Campaign Analytics Script

This script demonstrates how to:
1. Track message performance
2. Calculate engagement metrics
3. Generate campaign reports
4. Export analytics data
"""

import json
import csv
from typing import Dict, Any, List
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

from utils.base_script import BaseScript
from services.twitter import TwitterService
from database.session import get_db
from database.models import MessageLog, MessageType, MessageStatus

class TwitterCampaignAnalytics(BaseScript):
    def __init__(self):
        super().__init__("twitter_campaign_analytics")
        self.twitter_service = TwitterService()
        self.db = next(get_db())

    def get_campaign_messages(self, campaign_id: str) -> List[Dict[str, Any]]:
        """Fetch all messages for a campaign."""
        self.logger.info(f"Fetching messages for campaign: {campaign_id}")
        messages = self.db.query(MessageLog).filter(
            MessageLog.campaign_id == campaign_id,
            MessageLog.message_type == MessageType.TWITTER.value
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
        self.logger.info(f"Fetching analytics for message: {message_id}")
        result = self.twitter_service.get_message_analytics(message_id)
        
        if not result["success"]:
            self.logger.error(f"Failed to fetch analytics: {result['error']}")
            return None
            
        return result["analytics"]

    def calculate_engagement_metrics(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate engagement metrics for a set of messages."""
        total_messages = len(messages)
        total_views = 0
        total_replies = 0
        total_retweets = 0
        successful_messages = 0
        
        for message in messages:
            if message["status"] == MessageStatus.SENT.value:
                successful_messages += 1
                
                analytics = self.get_message_analytics(message["external_message_id"])
                if analytics:
                    total_views += analytics.get("views", 0)
                    total_replies += analytics.get("replies", 0)
                    total_retweets += analytics.get("retweets", 0)
        
        return {
            "total_messages": total_messages,
            "successful_messages": successful_messages,
            "delivery_rate": (successful_messages / total_messages * 100) if total_messages > 0 else 0,
            "total_views": total_views,
            "total_replies": total_replies,
            "total_retweets": total_retweets,
            "view_rate": (total_views / successful_messages * 100) if successful_messages > 0 else 0,
            "reply_rate": (total_replies / total_views * 100) if total_views > 0 else 0,
            "retweet_rate": (total_retweets / total_views * 100) if total_views > 0 else 0
        }

    def generate_time_series(self, messages: List[Dict[str, Any]], days: int = 30) -> pd.DataFrame:
        """Generate time series data for message performance."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Create date range
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Initialize DataFrame
        df = pd.DataFrame(index=date_range, columns=['messages', 'views', 'replies', 'retweets'])
        df = df.fillna(0)
        
        # Aggregate data by date
        for message in messages:
            sent_date = datetime.fromisoformat(message["sent_at"]).date()
            if start_date.date() <= sent_date <= end_date.date():
                df.loc[sent_date, 'messages'] += 1
                
                analytics = self.get_message_analytics(message["external_message_id"])
                if analytics:
                    df.loc[sent_date, 'views'] += analytics.get("views", 0)
                    df.loc[sent_date, 'replies'] += analytics.get("replies", 0)
                    df.loc[sent_date, 'retweets'] += analytics.get("retweets", 0)
        
        return df

    def plot_metrics(self, df: pd.DataFrame, output_file: str):
        """Plot engagement metrics over time."""
        plt.figure(figsize=(12, 6))
        
        # Plot metrics
        plt.plot(df.index, df['views'], label='Views', marker='o')
        plt.plot(df.index, df['replies'], label='Replies', marker='s')
        plt.plot(df.index, df['retweets'], label='Retweets', marker='^')
        
        # Customize plot
        plt.title('Twitter Campaign Performance Over Time')
        plt.xlabel('Date')
        plt.ylabel('Count')
        plt.legend()
        plt.grid(True)
        plt.xticks(rotation=45)
        
        # Save plot
        plt.tight_layout()
        plt.savefig(output_file)
        plt.close()
        
        self.logger.info(f"Plot saved to {output_file}")

    def export_to_csv(self, data: Dict[str, Any], filename: str):
        """Export analytics data to CSV."""
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Metric', 'Value'])
            for key, value in data.items():
                writer.writerow([key, value])
        
        self.logger.info(f"Data exported to {filename}")

    def run(self):
        """Main execution method."""
        # Example campaign ID (replace with actual campaign ID)
        campaign_id = "your-campaign-id"
        
        try:
            # Get campaign messages
            messages = self.get_campaign_messages(campaign_id)
            
            # Calculate engagement metrics
            metrics = self.calculate_engagement_metrics(messages)
            
            # Generate time series data
            time_series = self.generate_time_series(messages)
            
            # Plot metrics
            self.plot_metrics(time_series, f"campaign_analytics_{campaign_id}.png")
            
            # Export data
            self.export_to_csv(metrics, f"campaign_metrics_{campaign_id}.csv")
            
            # Print summary
            self.logger.info("\nCampaign Analytics Summary:")
            self.logger.info(f"Total Messages: {metrics['total_messages']}")
            self.logger.info(f"Delivery Rate: {metrics['delivery_rate']:.2f}%")
            self.logger.info(f"View Rate: {metrics['view_rate']:.2f}%")
            self.logger.info(f"Reply Rate: {metrics['reply_rate']:.2f}%")
            self.logger.info(f"Retweet Rate: {metrics['retweet_rate']:.2f}%")
            
        except Exception as e:
            self.logger.error(f"Error analyzing campaign: {str(e)}")

def main():
    script = TwitterCampaignAnalytics()
    script.main()

if __name__ == "__main__":
    main() 