#!/usr/bin/env python3
"""
Channel Management Script

Command-line tool for managing all channel integrations in the affiliate outreach system.
"""

import asyncio
import argparse
import json
import sys
import os
from typing import Dict, Any, List
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from config.channels import get_configured_channels, load_channel_settings
from core.application.services.channels.channel_manager import ChannelManager
from core.application.services.channels.base_channel import ChannelType, MessageRequest
from database.session import get_db

class ChannelCLI:
    """Command-line interface for channel management"""
    
    def __init__(self):
        self.manager = None
        self.db = None
    
    async def initialize(self):
        """Initialize the channel manager"""
        try:
            # Get database session
            self.db = next(get_db())
            
            # Create channel manager
            self.manager = ChannelManager(self.db)
            
            # Load and register all configured channels
            configs = get_configured_channels()
            
            for channel_type, config in configs.items():
                success = self.manager.register_channel(channel_type, config)
                if success:
                    print(f"✓ Registered {channel_type.value} channel")
                else:
                    print(f"✗ Failed to register {channel_type.value} channel")
            
            print(f"\nInitialized with {len(self.manager.get_available_channels())} channels")
            
        except Exception as e:
            print(f"Error initializing channel manager: {str(e)}")
            sys.exit(1)
    
    async def list_channels(self):
        """List all available channels"""
        print("\n=== Available Channels ===")
        
        available_channels = self.manager.get_available_channels()
        
        if not available_channels:
            print("No channels configured")
            return
        
        for channel_type in available_channels:
            info = self.manager.get_channel_info(channel_type)
            status = "✓ Enabled" if info.get('enabled') else "✗ Disabled"
            credentials = "✓ Has credentials" if info.get('has_credentials') else "✗ No credentials"
            
            print(f"\n{channel_type.value.upper()}:")
            print(f"  Status: {status}")
            print(f"  Credentials: {credentials}")
            print(f"  Rate Limit: {info.get('rate_limit', 'N/A')}/{info.get('rate_limit_window', 'N/A')}s")
            
            features = info.get('features', {})
            if features:
                print("  Features:")
                for feature, enabled in features.items():
                    feature_status = "✓" if enabled else "✗"
                    print(f"    {feature_status} {feature}")
    
    async def test_connections(self):
        """Test connections to all channels"""
        print("\n=== Testing Channel Connections ===")
        
        results = await self.manager.test_all_connections()
        
        for channel_type, result in results.items():
            if result.get('success'):
                print(f"✓ {channel_type.value}: {result.get('message', 'Connected')}")
            else:
                print(f"✗ {channel_type.value}: {result.get('error', 'Failed')}")
    
    async def send_test_message(self, channel: str, recipient: str, message: str):
        """Send a test message through specified channel"""
        try:
            channel_type = ChannelType(channel.lower())
        except ValueError:
            print(f"Invalid channel: {channel}")
            print(f"Available channels: {[ct.value for ct in self.manager.get_available_channels()]}")
            return
        
        if not self.manager.is_channel_available(channel_type):
            print(f"Channel {channel} is not available or not configured")
            return
        
        print(f"\nSending test message via {channel_type.value}...")
        
        request = MessageRequest(
            recipient_id=recipient,
            content=message,
            subject="Test Message from Affiliate Outreach System",
            message_type="text"
        )
        
        response = await self.manager.send_message(channel_type, request)
        
        if response.success:
            print(f"✓ Message sent successfully")
            print(f"  Message ID: {response.message_id}")
            print(f"  Status: {response.status.value if response.status else 'Unknown'}")
        else:
            print(f"✗ Failed to send message: {response.error}")
    
    async def run_campaign(self, config_file: str):
        """Run a multi-channel campaign from config file"""
        try:
            with open(config_file, 'r') as f:
                campaign_config = json.load(f)
        except FileNotFoundError:
            print(f"Campaign config file not found: {config_file}")
            return
        except json.JSONDecodeError as e:
            print(f"Invalid JSON in config file: {str(e)}")
            return
        
        print(f"\nRunning campaign from {config_file}...")
        
        results = await self.manager.run_campaign(campaign_config)
        
        print(f"\n=== Campaign Results ===")
        print(f"Campaign ID: {results.get('campaign_id')}")
        print(f"Total Recipients: {results.get('total_recipients')}")
        print(f"Channels Used: {', '.join(results.get('channels_used', []))}")
        
        summary = results.get('summary', {})
        print(f"\nSummary:")
        print(f"  Total Sent: {summary.get('total_sent', 0)}")
        print(f"  Total Failed: {summary.get('total_failed', 0)}")
        print(f"  Success Rate: {summary.get('success_rate', 0):.1f}%")
        
        if results.get('completed_at'):
            print(f"  Completed: {results['completed_at']}")
    
    async def discover_prospects(self, keywords: List[str], channels: List[str], 
                               min_followers: int = None, max_followers: int = None):
        """Discover prospects across platforms"""
        print(f"\nDiscovering prospects for keywords: {', '.join(keywords)}")
        print(f"Searching channels: {', '.join(channels)}")
        
        filters = {}
        if min_followers:
            filters['min_followers'] = min_followers
        if max_followers:
            filters['max_followers'] = max_followers
        
        discovery_config = {
            'keywords': keywords,
            'channels': channels,
            'filters': filters
        }
        
        results = await self.manager.discover_prospects(discovery_config)
        
        if not results.get('success', True):
            print(f"Discovery failed: {results.get('error')}")
            return
        
        summary = results.get('discovery_summary', {})
        print(f"\n=== Discovery Results ===")
        print(f"Total Prospects: {summary.get('total_prospects', 0)}")
        print(f"Platforms Searched: {summary.get('platforms_searched', 0)}")
        
        prospects_by_platform = results.get('prospects_by_platform', {})
        for platform, prospects in prospects_by_platform.items():
            print(f"\n{platform.upper()} ({len(prospects)} prospects):")
            for i, prospect in enumerate(prospects[:5]):  # Show first 5
                name = prospect.get('name') or prospect.get('title') or prospect.get('channel_name', 'Unknown')
                followers = prospect.get('follower_count') or prospect.get('subscriber_count') or prospect.get('subscribers', 0)
                print(f"  {i+1}. {name} ({followers:,} followers)")
            
            if len(prospects) > 5:
                print(f"  ... and {len(prospects) - 5} more")
    
    async def analyze_engagement(self, content_ids: Dict[str, str]):
        """Analyze cross-platform engagement"""
        print("\n=== Cross-Platform Engagement Analysis ===")
        
        # Convert string keys to ChannelType
        content_identifiers = {}
        for channel_str, content_id in content_ids.items():
            try:
                channel_type = ChannelType(channel_str.lower())
                content_identifiers[channel_type] = content_id
            except ValueError:
                print(f"Invalid channel: {channel_str}")
                continue
        
        if not content_identifiers:
            print("No valid content identifiers provided")
            return
        
        results = await self.manager.analyze_cross_platform_engagement(content_identifiers)
        
        if not results.get('success', True):
            print(f"Analysis failed: {results.get('error')}")
            return
        
        summary = results.get('cross_platform_summary', {})
        print(f"Total Views: {summary.get('total_views', 0):,}")
        print(f"Total Likes: {summary.get('total_likes', 0):,}")
        print(f"Total Comments: {summary.get('total_comments', 0):,}")
        print(f"Total Shares: {summary.get('total_shares', 0):,}")
        print(f"Overall Engagement Rate: {summary.get('overall_engagement_rate', 0):.2f}%")
        print(f"Best Platform: {summary.get('best_performing_platform', 'N/A')}")
        
        platform_breakdown = results.get('platform_breakdown', {})
        print(f"\nPlatform Breakdown:")
        for platform, metrics in platform_breakdown.items():
            print(f"  {platform.upper()}:")
            print(f"    Views: {metrics.get('views', 0):,}")
            print(f"    Engagement Rate: {metrics.get('engagement_rate', 0):.2f}%")
    
    async def show_settings(self):
        """Show current channel settings"""
        print("\n=== Channel Settings ===")
        
        settings = load_channel_settings()
        
        # Email settings
        print(f"\nEmail Provider: {settings.email_provider.value}")
        if settings.from_email:
            print(f"From Email: {settings.from_email}")
            print(f"From Name: {settings.from_name}")
        
        # Show which channels have credentials
        channels_with_creds = []
        
        if settings.linkedin_access_token:
            channels_with_creds.append("LinkedIn")
        if settings.twitter_bearer_token:
            channels_with_creds.append("Twitter")
        if settings.instagram_access_token:
            channels_with_creds.append("Instagram")
        if settings.facebook_access_token:
            channels_with_creds.append("Facebook")
        if settings.whatsapp_access_token:
            channels_with_creds.append("WhatsApp")
        if settings.youtube_api_key:
            channels_with_creds.append("YouTube")
        if settings.tiktok_access_token:
            channels_with_creds.append("TikTok")
        if settings.telegram_bot_token:
            channels_with_creds.append("Telegram")
        if settings.reddit_client_id:
            channels_with_creds.append("Reddit")
        if settings.discord_bot_token:
            channels_with_creds.append("Discord")
        
        print(f"\nChannels with credentials: {', '.join(channels_with_creds) if channels_with_creds else 'None'}")
        
        print(f"\nRate Limiting:")
        print(f"  Default Rate Limit: {settings.default_rate_limit}")
        print(f"  Default Window: {settings.default_rate_limit_window}s")
        print(f"  Default Timeout: {settings.default_timeout}s")
        print(f"  Default Retry Attempts: {settings.default_retry_attempts}")
        print(f"  Default Retry Delay: {settings.default_retry_delay}s")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Channel Management CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # List channels command
    list_parser = subparsers.add_parser("list", help="List available channels")
    
    # Test connections command
    test_parser = subparsers.add_parser("test", help="Test channel connections")
    
    # Send test message command
    send_parser = subparsers.add_parser("send", help="Send test message")
    send_parser.add_argument("channel", help="Channel to use")
    send_parser.add_argument("recipient", help="Recipient ID/address")
    send_parser.add_argument("message", help="Message content")
    
    # Run campaign command
    campaign_parser = subparsers.add_parser("campaign", help="Run multi-channel campaign")
    campaign_parser.add_argument("config", help="Campaign config JSON file")
    
    # Discover prospects command
    discover_parser = subparsers.add_parser("discover", help="Discover prospects")
    discover_parser.add_argument("--keywords", "-k", nargs="+", required=True, help="Keywords to search for")
    discover_parser.add_argument("--channels", "-c", nargs="+", required=True, help="Channels to search")
    discover_parser.add_argument("--min-followers", "-min", type=int, help="Minimum followers")
    discover_parser.add_argument("--max-followers", "-max", type=int, help="Maximum followers")
    
    # Analyze engagement command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze cross-platform engagement")
    analyze_parser.add_argument("--content", "-c", nargs="+", required=True, 
                              help="Content IDs in format channel:id (e.g., youtube:abc123)")
    
    # Show settings command
    settings_parser = subparsers.add_parser("settings", help="Show channel settings")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Create CLI instance
    cli = ChannelCLI()
    
    # Run appropriate command
    if args.command == "list":
        asyncio.run(cli.initialize_and_run(cli.list_channels))
    elif args.command == "test":
        asyncio.run(cli.initialize_and_run(cli.test_connections))
    elif args.command == "send":
        asyncio.run(cli.initialize_and_run(
            lambda: cli.send_test_message(args.channel, args.recipient, args.message)
        ))
    elif args.command == "campaign":
        asyncio.run(cli.initialize_and_run(
            lambda: cli.run_campaign(args.config)
        ))
    elif args.command == "discover":
        asyncio.run(cli.initialize_and_run(
            lambda: cli.discover_prospects(
                args.keywords, args.channels, args.min_followers, args.max_followers
            )
        ))
    elif args.command == "analyze":
        # Parse content IDs
        content_ids = {}
        for content in args.content:
            parts = content.split(":", 1)
            if len(parts) == 2:
                content_ids[parts[0]] = parts[1]
        
        asyncio.run(cli.initialize_and_run(
            lambda: cli.analyze_engagement(content_ids)
        ))
    elif args.command == "settings":
        asyncio.run(cli.initialize_and_run(cli.show_settings))

    async def initialize_and_run(self, func):
        """Initialize and run a function"""
        await self.initialize()
        await func()
        
        # Close all channels
        if self.manager:
            await self.manager.close_all_channels()

if __name__ == "__main__":
    main()
