#!/usr/bin/env python3
"""
Twitter Connection Manager Script

This script demonstrates how to:
1. Manage Twitter followers and following
2. Track connection status
3. Generate connection reports
4. Export connection data
"""

import json
import csv
from typing import Dict, Any, List
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

from utils.base_script import BaseScript
from services.twitter import TwitterService
from database.session import get_db
from database.models import ConnectionLog, ConnectionStatus

class TwitterConnectionManager(BaseScript):
    def __init__(self):
        super().__init__("twitter_connection_manager")
        self.twitter_service = TwitterService()
        self.db = next(get_db())

    def get_followers(self, cursor: str = None) -> Dict[str, Any]:
        """Fetch Twitter followers with pagination."""
        self.logger.info("Fetching Twitter followers")
        result = self.twitter_service.get_followers(cursor)
        
        if not result["success"]:
            self.logger.error(f"Failed to fetch followers: {result['error']}")
            return None
            
        return result["data"]

    def get_following(self, cursor: str = None) -> Dict[str, Any]:
        """Fetch Twitter following with pagination."""
        self.logger.info("Fetching Twitter following")
        result = self.twitter_service.get_following(cursor)
        
        if not result["success"]:
            self.logger.error(f"Failed to fetch following: {result['error']}")
            return None
            
        return result["data"]

    def follow_user(self, user_id: str) -> Dict[str, Any]:
        """Follow a Twitter user."""
        self.logger.info(f"Following user: {user_id}")
        result = self.twitter_service.follow_user(user_id)
        
        if result["success"]:
            # Log the connection
            connection = ConnectionLog(
                platform="twitter",
                external_user_id=user_id,
                status=ConnectionStatus.PENDING.value,
                action="follow",
                created_at=datetime.now()
            )
            self.db.add(connection)
            self.db.commit()
            
        return result

    def unfollow_user(self, user_id: str) -> Dict[str, Any]:
        """Unfollow a Twitter user."""
        self.logger.info(f"Unfollowing user: {user_id}")
        result = self.twitter_service.unfollow_user(user_id)
        
        if result["success"]:
            # Update connection status
            connection = self.db.query(ConnectionLog).filter(
                ConnectionLog.platform == "twitter",
                ConnectionLog.external_user_id == user_id
            ).first()
            
            if connection:
                connection.status = ConnectionStatus.UNFOLLOWED.value
                connection.updated_at = datetime.now()
                self.db.commit()
            
        return result

    def get_connection_status(self, user_id: str) -> Dict[str, Any]:
        """Get connection status with a user."""
        self.logger.info(f"Checking connection status for user: {user_id}")
        
        # Check database first
        connection = self.db.query(ConnectionLog).filter(
            ConnectionLog.platform == "twitter",
            ConnectionLog.external_user_id == user_id
        ).first()
        
        if connection:
            return {
                "status": connection.status,
                "action": connection.action,
                "created_at": connection.created_at.isoformat(),
                "updated_at": connection.updated_at.isoformat() if connection.updated_at else None
            }
        
        # Check Twitter API
        result = self.twitter_service.get_connection_status(user_id)
        if result["success"]:
            # Log the connection
            connection = ConnectionLog(
                platform="twitter",
                external_user_id=user_id,
                status=result["status"],
                action="check",
                created_at=datetime.now()
            )
            self.db.add(connection)
            self.db.commit()
            
        return result

    def generate_connection_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate a report of connection activities."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get connection logs
        connections = self.db.query(ConnectionLog).filter(
            ConnectionLog.platform == "twitter",
            ConnectionLog.created_at >= start_date
        ).all()
        
        # Calculate metrics
        total_follows = len([c for c in connections if c.action == "follow"])
        successful_follows = len([c for c in connections if c.action == "follow" and c.status == ConnectionStatus.CONNECTED.value])
        total_unfollows = len([c for c in connections if c.action == "unfollow"])
        
        # Get current followers and following
        followers_data = self.get_followers()
        following_data = self.get_following()
        
        current_followers = len(followers_data["users"]) if followers_data else 0
        current_following = len(following_data["users"]) if following_data else 0
        
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_follows": total_follows,
            "successful_follows": successful_follows,
            "follow_success_rate": (successful_follows / total_follows * 100) if total_follows > 0 else 0,
            "total_unfollows": total_unfollows,
            "current_followers": current_followers,
            "current_following": current_following,
            "net_growth": current_followers - (current_following - total_unfollows)
        }

    def export_connection_data(self, data: Dict[str, Any], filename: str):
        """Export connection data to JSON."""
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        self.logger.info(f"Data exported to {filename}")

    def generate_connection_metrics(self, days: int = 30) -> pd.DataFrame:
        """Generate metrics over time."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Create date range
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Initialize DataFrame
        df = pd.DataFrame(index=date_range, columns=['follows', 'unfollows', 'net_growth'])
        df = df.fillna(0)
        
        # Get connection logs
        connections = self.db.query(ConnectionLog).filter(
            ConnectionLog.platform == "twitter",
            ConnectionLog.created_at >= start_date
        ).all()
        
        # Aggregate data by date
        for connection in connections:
            date = connection.created_at.date()
            if start_date.date() <= date <= end_date.date():
                if connection.action == "follow":
                    df.loc[date, 'follows'] += 1
                    if connection.status == ConnectionStatus.CONNECTED.value:
                        df.loc[date, 'net_growth'] += 1
                elif connection.action == "unfollow":
                    df.loc[date, 'unfollows'] += 1
                    df.loc[date, 'net_growth'] -= 1
        
        return df

    def run(self):
        """Main execution method."""
        try:
            # Generate connection report
            report = self.generate_connection_report()
            
            # Export report
            self.export_connection_data(report, "twitter_connection_report.json")
            
            # Generate and save metrics
            metrics = self.generate_connection_metrics()
            metrics.to_csv("twitter_connection_metrics.csv")
            
            # Print summary
            self.logger.info("\nConnection Management Summary:")
            self.logger.info(f"Total Follows: {report['total_follows']}")
            self.logger.info(f"Follow Success Rate: {report['follow_success_rate']:.2f}%")
            self.logger.info(f"Current Followers: {report['current_followers']}")
            self.logger.info(f"Current Following: {report['current_following']}")
            self.logger.info(f"Net Growth: {report['net_growth']}")
            
        except Exception as e:
            self.logger.error(f"Error managing connections: {str(e)}")

def main():
    script = TwitterConnectionManager()
    script.main()

if __name__ == "__main__":
    main() 