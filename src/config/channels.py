"""
Channel Configuration

Configuration settings for all supported channels in the affiliate outreach system.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from core.application.services.channels.base_channel import ChannelType, ChannelConfig

class ChannelProvider(Enum):
    """Email providers"""
    SMTP = "smtp"
    SENDGRID = "sendgrid"
    MAILGUN = "mailgun"
    SES = "ses"

@dataclass
class ChannelSettings:
    """Settings for channel configurations"""
    
    # Email settings
    email_provider: ChannelProvider = ChannelProvider.SMTP
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True
    from_email: Optional[str] = None
    from_name: str = "Affiliate Outreach"
    
    # SendGrid
    sendgrid_api_key: Optional[str] = None
    
    # Mailgun
    mailgun_api_key: Optional[str] = None
    mailgun_domain: Optional[str] = None
    
    # Amazon SES
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-1"
    
    # LinkedIn
    linkedin_client_id: Optional[str] = None
    linkedin_client_secret: Optional[str] = None
    linkedin_access_token: Optional[str] = None
    linkedin_refresh_token: Optional[str] = None
    
    # Twitter/X
    twitter_api_key: Optional[str] = None
    twitter_api_secret: Optional[str] = None
    twitter_access_token: Optional[str] = None
    twitter_access_token_secret: Optional[str] = None
    twitter_bearer_token: Optional[str] = None
    
    # Instagram
    instagram_access_token: Optional[str] = None
    instagram_app_id: Optional[str] = None
    instagram_app_secret: Optional[str] = None
    
    # Facebook
    facebook_access_token: Optional[str] = None
    facebook_app_id: Optional[str] = None
    facebook_app_secret: Optional[str] = None
    facebook_page_id: Optional[str] = None
    
    # WhatsApp Business
    whatsapp_access_token: Optional[str] = None
    whatsapp_phone_number_id: Optional[str] = None
    whatsapp_business_account_id: Optional[str] = None
    
    # YouTube
    youtube_api_key: Optional[str] = None
    youtube_client_id: Optional[str] = None
    youtube_client_secret: Optional[str] = None
    
    # TikTok
    tiktok_access_token: Optional[str] = None
    tiktok_client_key: Optional[str] = None
    tiktok_client_secret: Optional[str] = None
    
    # Telegram
    telegram_bot_token: Optional[str] = None
    telegram_bot_username: Optional[str] = None
    
    # Reddit
    reddit_client_id: Optional[str] = None
    reddit_client_secret: Optional[str] = None
    reddit_username: Optional[str] = None
    reddit_password: Optional[str] = None
    
    # Discord
    discord_bot_token: Optional[str] = None
    discord_client_id: Optional[str] = None
    discord_client_secret: Optional[str] = None
    
    # Rate limiting defaults
    default_rate_limit: int = 100
    default_rate_limit_window: int = 3600
    default_timeout: int = 30
    default_retry_attempts: int = 3
    default_retry_delay: int = 1

def load_channel_settings() -> ChannelSettings:
    """Load channel settings from environment variables"""
    return ChannelSettings(
        # Email settings
        email_provider=ChannelProvider(os.getenv('EMAIL_PROVIDER', 'smtp')),
        smtp_host=os.getenv('SMTP_HOST'),
        smtp_port=int(os.getenv('SMTP_PORT', '587')),
        smtp_username=os.getenv('SMTP_USERNAME'),
        smtp_password=os.getenv('SMTP_PASSWORD'),
        smtp_use_tls=os.getenv('SMTP_USE_TLS', 'true').lower() == 'true',
        from_email=os.getenv('FROM_EMAIL'),
        from_name=os.getenv('FROM_NAME', 'Affiliate Outreach'),
        
        # SendGrid
        sendgrid_api_key=os.getenv('SENDGRID_API_KEY'),
        
        # Mailgun
        mailgun_api_key=os.getenv('MAILGUN_API_KEY'),
        mailgun_domain=os.getenv('MAILGUN_DOMAIN'),
        
        # Amazon SES
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        aws_region=os.getenv('AWS_REGION', 'us-east-1'),
        
        # LinkedIn
        linkedin_client_id=os.getenv('LINKEDIN_CLIENT_ID'),
        linkedin_client_secret=os.getenv('LINKEDIN_CLIENT_SECRET'),
        linkedin_access_token=os.getenv('LINKEDIN_ACCESS_TOKEN'),
        linkedin_refresh_token=os.getenv('LINKEDIN_REFRESH_TOKEN'),
        
        # Twitter/X
        twitter_api_key=os.getenv('TWITTER_API_KEY'),
        twitter_api_secret=os.getenv('TWITTER_API_SECRET'),
        twitter_access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
        twitter_access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET'),
        twitter_bearer_token=os.getenv('TWITTER_BEARER_TOKEN'),
        
        # Instagram
        instagram_access_token=os.getenv('INSTAGRAM_ACCESS_TOKEN'),
        instagram_app_id=os.getenv('INSTAGRAM_APP_ID'),
        instagram_app_secret=os.getenv('INSTAGRAM_APP_SECRET'),
        
        # Facebook
        facebook_access_token=os.getenv('FACEBOOK_ACCESS_TOKEN'),
        facebook_app_id=os.getenv('FACEBOOK_APP_ID'),
        facebook_app_secret=os.getenv('FACEBOOK_APP_SECRET'),
        facebook_page_id=os.getenv('FACEBOOK_PAGE_ID'),
        
        # WhatsApp Business
        whatsapp_access_token=os.getenv('WHATSAPP_ACCESS_TOKEN'),
        whatsapp_phone_number_id=os.getenv('WHATSAPP_PHONE_NUMBER_ID'),
        whatsapp_business_account_id=os.getenv('WHATSAPP_BUSINESS_ACCOUNT_ID'),
        
        # YouTube
        youtube_api_key=os.getenv('YOUTUBE_API_KEY'),
        youtube_client_id=os.getenv('YOUTUBE_CLIENT_ID'),
        youtube_client_secret=os.getenv('YOUTUBE_CLIENT_SECRET'),
        
        # TikTok
        tiktok_access_token=os.getenv('TIKTOK_ACCESS_TOKEN'),
        tiktok_client_key=os.getenv('TIKTOK_CLIENT_KEY'),
        tiktok_client_secret=os.getenv('TIKTOK_CLIENT_SECRET'),
        
        # Telegram
        telegram_bot_token=os.getenv('TELEGRAM_BOT_TOKEN'),
        telegram_bot_username=os.getenv('TELEGRAM_BOT_USERNAME'),
        
        # Reddit
        reddit_client_id=os.getenv('REDDIT_CLIENT_ID'),
        reddit_client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
        reddit_username=os.getenv('REDDIT_USERNAME'),
        reddit_password=os.getenv('REDDIT_PASSWORD'),
        
        # Discord
        discord_bot_token=os.getenv('DISCORD_BOT_TOKEN'),
        discord_client_id=os.getenv('DISCORD_CLIENT_ID'),
        discord_client_secret=os.getenv('DISCORD_CLIENT_SECRET'),
        
        # Rate limiting
        default_rate_limit=int(os.getenv('DEFAULT_RATE_LIMIT', '100')),
        default_rate_limit_window=int(os.getenv('DEFAULT_RATE_LIMIT_WINDOW', '3600')),
        default_timeout=int(os.getenv('DEFAULT_TIMEOUT', '30')),
        default_retry_attempts=int(os.getenv('DEFAULT_RETRY_ATTEMPTS', '3')),
        default_retry_delay=int(os.getenv('DEFAULT_RETRY_DELAY', '1')),
    )

def create_channel_configs(settings: ChannelSettings) -> Dict[ChannelType, ChannelConfig]:
    """Create channel configurations from settings"""
    configs = {}
    
    # Email configuration
    if settings.from_email:
        email_metadata = {
            'provider': settings.email_provider.value,
            'from_email': settings.from_email,
            'from_name': settings.from_name,
        }
        
        if settings.email_provider == ChannelProvider.SMTP:
            email_metadata.update({
                'smtp_host': settings.smtp_host,
                'smtp_port': settings.smtp_port,
                'smtp_username': settings.smtp_username,
                'smtp_password': settings.smtp_password,
                'smtp_use_tls': settings.smtp_use_tls,
            })
            api_key = None
        elif settings.email_provider == ChannelProvider.SENDGRID:
            api_key = settings.sendgrid_api_key
        elif settings.email_provider == ChannelProvider.MAILGUN:
            api_key = settings.mailgun_api_key
            email_metadata['mailgun_domain'] = settings.mailgun_domain
        elif settings.email_provider == ChannelProvider.SES:
            api_key = settings.aws_access_key_id
            email_metadata.update({
                'aws_secret_access_key': settings.aws_secret_access_key,
                'aws_region': settings.aws_region,
            })
        else:
            api_key = None
        
        configs[ChannelType.EMAIL] = ChannelConfig(
            api_key=api_key,
            rate_limit=settings.default_rate_limit,
            rate_limit_window=settings.default_rate_limit_window,
            timeout=settings.default_timeout,
            retry_attempts=settings.default_retry_attempts,
            retry_delay=settings.default_retry_delay,
            enabled=True,
            metadata=email_metadata
        )
    
    # LinkedIn configuration
    if settings.linkedin_access_token:
        configs[ChannelType.LINKEDIN] = ChannelConfig(
            api_key=settings.linkedin_client_id,
            api_secret=settings.linkedin_client_secret,
            access_token=settings.linkedin_access_token,
            refresh_token=settings.linkedin_refresh_token,
            rate_limit=settings.default_rate_limit,
            rate_limit_window=settings.default_rate_limit_window,
            timeout=settings.default_timeout,
            retry_attempts=settings.default_retry_attempts,
            retry_delay=settings.default_retry_delay,
            enabled=True
        )
    
    # Twitter configuration
    if settings.twitter_bearer_token:
        configs[ChannelType.TWITTER] = ChannelConfig(
            api_key=settings.twitter_api_key,
            api_secret=settings.twitter_api_secret,
            access_token=settings.twitter_access_token,
            rate_limit=settings.default_rate_limit,
            rate_limit_window=settings.default_rate_limit_window,
            timeout=settings.default_timeout,
            retry_attempts=settings.default_retry_attempts,
            retry_delay=settings.default_retry_delay,
            enabled=True,
            metadata={
                'access_token_secret': settings.twitter_access_token_secret,
                'bearer_token': settings.twitter_bearer_token
            }
        )
    
    # Instagram configuration
    if settings.instagram_access_token:
        configs[ChannelType.INSTAGRAM] = ChannelConfig(
            access_token=settings.instagram_access_token,
            rate_limit=settings.default_rate_limit,
            rate_limit_window=settings.default_rate_limit_window,
            timeout=settings.default_timeout,
            retry_attempts=settings.default_retry_attempts,
            retry_delay=settings.default_retry_delay,
            enabled=True,
            metadata={
                'app_id': settings.instagram_app_id,
                'app_secret': settings.instagram_app_secret
            }
        )
    
    # Facebook configuration
    if settings.facebook_access_token and settings.facebook_page_id:
        configs[ChannelType.FACEBOOK] = ChannelConfig(
            access_token=settings.facebook_access_token,
            rate_limit=settings.default_rate_limit,
            rate_limit_window=settings.default_rate_limit_window,
            timeout=settings.default_timeout,
            retry_attempts=settings.default_retry_attempts,
            retry_delay=settings.default_retry_delay,
            enabled=True,
            metadata={
                'page_id': settings.facebook_page_id,
                'app_id': settings.facebook_app_id,
                'app_secret': settings.facebook_app_secret
            }
        )
    
    # WhatsApp configuration
    if settings.whatsapp_access_token and settings.whatsapp_phone_number_id:
        configs[ChannelType.WHATSAPP] = ChannelConfig(
            access_token=settings.whatsapp_access_token,
            rate_limit=settings.default_rate_limit,
            rate_limit_window=settings.default_rate_limit_window,
            timeout=settings.default_timeout,
            retry_attempts=settings.default_retry_attempts,
            retry_delay=settings.default_retry_delay,
            enabled=True,
            metadata={
                'phone_number_id': settings.whatsapp_phone_number_id,
                'business_account_id': settings.whatsapp_business_account_id
            }
        )
    
    # YouTube configuration
    if settings.youtube_api_key:
        configs[ChannelType.YOUTUBE] = ChannelConfig(
            api_key=settings.youtube_api_key,
            rate_limit=settings.default_rate_limit,
            rate_limit_window=settings.default_rate_limit_window,
            timeout=settings.default_timeout,
            retry_attempts=settings.default_retry_attempts,
            retry_delay=settings.default_retry_delay,
            enabled=True,
            metadata={
                'client_id': settings.youtube_client_id,
                'client_secret': settings.youtube_client_secret
            }
        )
    
    # TikTok configuration
    if settings.tiktok_access_token:
        configs[ChannelType.TIKTOK] = ChannelConfig(
            access_token=settings.tiktok_access_token,
            rate_limit=settings.default_rate_limit,
            rate_limit_window=settings.default_rate_limit_window,
            timeout=settings.default_timeout,
            retry_attempts=settings.default_retry_attempts,
            retry_delay=settings.default_retry_delay,
            enabled=True,
            metadata={
                'client_key': settings.tiktok_client_key,
                'client_secret': settings.tiktok_client_secret
            }
        )
    
    # Telegram configuration
    if settings.telegram_bot_token:
        configs[ChannelType.TELEGRAM] = ChannelConfig(
            api_key=settings.telegram_bot_token,
            rate_limit=settings.default_rate_limit,
            rate_limit_window=settings.default_rate_limit_window,
            timeout=settings.default_timeout,
            retry_attempts=settings.default_retry_attempts,
            retry_delay=settings.default_retry_delay,
            enabled=True,
            metadata={
                'bot_username': settings.telegram_bot_username
            }
        )
    
    # Reddit configuration
    if settings.reddit_client_id and settings.reddit_username:
        configs[ChannelType.REDDIT] = ChannelConfig(
            api_key=settings.reddit_client_id,
            api_secret=settings.reddit_client_secret,
            rate_limit=settings.default_rate_limit,
            rate_limit_window=settings.default_rate_limit_window,
            timeout=settings.default_timeout,
            retry_attempts=settings.default_retry_attempts,
            retry_delay=settings.default_retry_delay,
            enabled=True,
            metadata={
                'username': settings.reddit_username,
                'password': settings.reddit_password
            }
        )
    
    # Discord configuration
    if settings.discord_bot_token:
        configs[ChannelType.DISCORD] = ChannelConfig(
            api_key=settings.discord_bot_token,
            rate_limit=settings.default_rate_limit,
            rate_limit_window=settings.default_rate_limit_window,
            timeout=settings.default_timeout,
            retry_attempts=settings.default_retry_attempts,
            retry_delay=settings.default_retry_delay,
            enabled=True,
            metadata={
                'client_id': settings.discord_client_id,
                'client_secret': settings.discord_client_secret
            }
        )
    
    return configs

def get_configured_channels() -> Dict[ChannelType, ChannelConfig]:
    """Get all configured channels"""
    settings = load_channel_settings()
    return create_channel_configs(settings)
