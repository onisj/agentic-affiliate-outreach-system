"""
Multi-Channel Outreach Services

This package provides unified interfaces for all supported outreach channels
including social media platforms, messaging services, and email providers.
"""

from .base_channel import BaseChannelService, ChannelType, MessageStatus
from .instagram_service import InstagramService
from .facebook_service import FacebookService
from .whatsapp_service import WhatsAppService
from .youtube_service import YouTubeService
from .tiktok_service import TikTokService
from .telegram_service import TelegramService
from .reddit_service import RedditService
from .discord_service import DiscordService
from .email_enhanced import EnhancedEmailService

__all__ = [
    'BaseChannelService',
    'ChannelType',
    'MessageStatus',
    'InstagramService',
    'FacebookService',
    'WhatsAppService',
    'YouTubeService',
    'TikTokService',
    'TelegramService',
    'RedditService',
    'DiscordService',
    'EnhancedEmailService',
]
