import re
from typing import Dict, Any
from urllib.parse import urlparse
import dns.resolver
import requests
from config.settings import settings

class DataValidator:
    """Utility class for validating prospect data."""
    
    @staticmethod
    def validate_email(email: str) -> Dict[str, Any]:
        """Validate email address."""
        result = {
            "is_valid": False,
            "domain_valid": False,
            "format_valid": False,
            "errors": []
        }
        
        # Basic format validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            result["errors"].append("Invalid email format")
            return result
        
        result["format_valid"] = True
        
        # Domain validation
        domain = email.split('@')[1]
        try:
            dns.resolver.resolve(domain, 'MX')
            result["domain_valid"] = True
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, Exception) as e:
            result["errors"].append(f"Domain {domain} does not exist or has no MX record: {str(e)}")
        
        result["is_valid"] = result["format_valid"] and result["domain_valid"]
        return result
    
    @staticmethod
    def validate_website(website: str) -> Dict[str, Any]:
        """Validate website URL."""
        result = {
            "is_valid": False,
            "is_reachable": False,
            "status_code": None,
            "errors": []
        }
        
        if not website:
            result["errors"].append("Invalid URL format")
            return result
        
        # Add protocol if missing
        if not website.startswith(('http://', 'https://')):
            website = f"https://{website}"
        
        # Parse URL
        try:
            parsed = urlparse(website)
            if not parsed.netloc or '.' not in parsed.netloc:
                result["errors"].append("Invalid URL format")
                return result
            
            # Check if reachable
            try:
                response = requests.head(website, timeout=10, allow_redirects=True)
                result["is_reachable"] = response.status_code == 200
                result["status_code"] = response.status_code
                result["is_valid"] = result["is_reachable"]
            except requests.RequestException as e:
                result["errors"].append(f"Website unreachable: {str(e)}")
        
        except Exception as e:
            result["errors"].append("Invalid URL format")
        
        return result
    
    @staticmethod
    def validate_social_profile(platform: str, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Validate social media profile data."""
        result = {
            "is_valid": False,
            "errors": []
        }
        
        if platform not in ["twitter", "linkedin"]:
            result["errors"].append(f"Unsupported platform: {platform}")
            return result
        
        if platform == "twitter":
            if not profile.get("username"):
                result["errors"].append("Twitter username missing")
            else:
                try:
                    headers = {"Authorization": f"Bearer {settings.TWITTER_BEARER_TOKEN}"}
                    response = requests.get(
                        f"https://api.twitter.com/2/users/by/username/{profile['username']}",
                        headers=headers,
                        timeout=10
                    )
                    if response.status_code == 200:
                        result["is_valid"] = True
                    else:
                        result["errors"].append("Invalid Twitter username")
                except Exception as e:
                    result["errors"].append(f"Error validating Twitter profile: {str(e)}")
        
        elif platform == "linkedin":
            if not profile.get("urn"):
                result["errors"].append("LinkedIn URN missing")
            else:
                result["is_valid"] = True  # Assume valid URN (API validation requires authentication)
        
        return result