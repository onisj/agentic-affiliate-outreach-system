"""
Data Cleaner

This module implements data cleaning and normalization for scraped data.
"""

from typing import Dict, List, Any, Optional
import logging
import re
from datetime import datetime
import unicodedata
from bs4 import BeautifulSoup
import nltk

from src.services.monitoring.monitoring import MonitoringService

logger = logging.getLogger(__name__)

class DataCleaner:
    """Cleans and normalizes scraped data."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.monitoring = MonitoringService()
        
        # Download required NLTK data
        try:
            nltk.download('punkt')
            nltk.download('stopwords')
            nltk.download('wordnet')
        except Exception as e:
            self.monitoring.log_error(f"Error downloading NLTK data: {str(e)}")
            
    def clean_profile_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean profile data."""
        try:
            cleaned_data = {
                'basic_info': self._clean_basic_info(data.get('basic_info', {})),
                'content': self._clean_content(data.get('content', [])),
                'engagement': self._clean_engagement(data.get('engagement', {})),
                'network': self._clean_network(data.get('network', {}))
            }
            
            return cleaned_data
            
        except Exception as e:
            self.monitoring.log_error(f"Error cleaning profile data: {str(e)}")
            return {}
            
    def _clean_basic_info(self, info: Dict[str, Any]) -> Dict[str, Any]:
        """Clean basic profile information."""
        try:
            cleaned_info = {}
            
            # Clean text fields
            for field in ['name', 'username', 'bio', 'location', 'website']:
                if field in info:
                    cleaned_info[field] = self._clean_text(info[field])
                    
            # Clean numeric fields
            for field in ['followers', 'following', 'posts']:
                if field in info:
                    cleaned_info[field] = self._clean_number(info[field])
                    
            # Clean date fields
            for field in ['join_date', 'last_active']:
                if field in info:
                    cleaned_info[field] = self._clean_date(info[field])
                    
            # Clean URLs
            for field in ['profile_picture', 'banner_image']:
                if field in info:
                    cleaned_info[field] = self._clean_url(info[field])
                    
            return cleaned_info
            
        except Exception as e:
            self.monitoring.log_error(f"Error cleaning basic info: {str(e)}")
            return {}
            
    def _clean_content(self, content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clean content data."""
        try:
            cleaned_content = []
            
            for item in content:
                cleaned_item = {
                    'text': self._clean_text(item.get('text', '')),
                    'media': self._clean_media(item.get('media', [])),
                    'engagement': self._clean_engagement(item.get('engagement', {})),
                    'metadata': self._clean_metadata(item.get('metadata', {}))
                }
                cleaned_content.append(cleaned_item)
                
            return cleaned_content
            
        except Exception as e:
            self.monitoring.log_error(f"Error cleaning content: {str(e)}")
            return []
            
    def _clean_engagement(self, engagement: Dict[str, Any]) -> Dict[str, Any]:
        """Clean engagement data."""
        try:
            cleaned_engagement = {}
            
            # Clean numeric metrics
            for metric in ['likes', 'comments', 'shares', 'views']:
                if metric in engagement:
                    cleaned_engagement[metric] = self._clean_number(engagement[metric])
                    
            # Clean rates and scores
            for metric in ['engagement_rate', 'quality_score']:
                if metric in engagement:
                    cleaned_engagement[metric] = self._clean_score(engagement[metric])
                    
            return cleaned_engagement
            
        except Exception as e:
            self.monitoring.log_error(f"Error cleaning engagement: {str(e)}")
            return {}
            
    def _clean_network(self, network: Dict[str, Any]) -> Dict[str, Any]:
        """Clean network data."""
        try:
            cleaned_network = {}
            
            # Clean connections
            if 'connections' in network:
                cleaned_network['connections'] = [
                    self._clean_connection(conn)
                    for conn in network['connections']
                ]
                
            # Clean metrics
            if 'metrics' in network:
                cleaned_network['metrics'] = self._clean_network_metrics(
                    network['metrics']
                )
                
            return cleaned_network
            
        except Exception as e:
            self.monitoring.log_error(f"Error cleaning network: {str(e)}")
            return {}
            
    def _clean_text(self, text: str) -> str:
        """Clean text content."""
        try:
            if not text:
                return ""
                
            # Convert to string if not already
            text = str(text)
            
            # Remove HTML tags
            text = BeautifulSoup(text, 'html.parser').get_text()
            
            # Normalize unicode
            text = unicodedata.normalize('NFKD', text)
            
            # Remove special characters
            text = re.sub(r'[^\w\s]', ' ', text)
            
            # Remove extra whitespace
            text = ' '.join(text.split())
            
            return text.strip()
            
        except Exception as e:
            self.monitoring.log_error(f"Error cleaning text: {str(e)}")
            return ""
            
    def _clean_number(self, number: Any) -> int:
        """Clean numeric values."""
        try:
            if isinstance(number, (int, float)):
                return int(number)
            elif isinstance(number, str):
                # Remove non-numeric characters
                number = re.sub(r'[^\d]', '', number)
                return int(number) if number else 0
            else:
                return 0
        except:
            return 0
            
    def _clean_date(self, date: Any) -> Optional[str]:
        """Clean date values."""
        try:
            if not date:
                return None
                
            # Try parsing common date formats
            formats = [
                '%Y-%m-%d',
                '%d/%m/%Y',
                '%m/%d/%Y',
                '%B %d, %Y',
                '%d %B %Y'
            ]
            
            for fmt in formats:
                try:
                    parsed_date = datetime.strptime(str(date), fmt)
                    return parsed_date.strftime('%Y-%m-%d')
                except:
                    continue
                    
            return None
            
        except Exception as e:
            self.monitoring.log_error(f"Error cleaning date: {str(e)}")
            return None
            
    def _clean_url(self, url: str) -> Optional[str]:
        """Clean URL values."""
        try:
            if not url:
                return None
                
            # Remove query parameters
            url = url.split('?')[0]
            
            # Remove fragments
            url = url.split('#')[0]
            
            # Ensure proper format
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
                
            return url.rstrip('/')
            
        except Exception as e:
            self.monitoring.log_error(f"Error cleaning URL: {str(e)}")
            return None
            
    def _clean_media(self, media: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clean media data."""
        try:
            cleaned_media = []
            
            for item in media:
                cleaned_item = {
                    'type': item.get('type', 'unknown'),
                    'url': self._clean_url(item.get('url', '')),
                    'metadata': self._clean_metadata(item.get('metadata', {}))
                }
                cleaned_media.append(cleaned_item)
                
            return cleaned_media
            
        except Exception as e:
            self.monitoring.log_error(f"Error cleaning media: {str(e)}")
            return []
            
    def _clean_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Clean metadata."""
        try:
            cleaned_metadata = {}
            
            for key, value in metadata.items():
                if isinstance(value, str):
                    cleaned_metadata[key] = self._clean_text(value)
                elif isinstance(value, (int, float)):
                    cleaned_metadata[key] = self._clean_number(value)
                elif isinstance(value, dict):
                    cleaned_metadata[key] = self._clean_metadata(value)
                elif isinstance(value, list):
                    cleaned_metadata[key] = [
                        self._clean_metadata(item) if isinstance(item, dict)
                        else self._clean_text(item) if isinstance(item, str)
                        else item
                        for item in value
                    ]
                else:
                    cleaned_metadata[key] = value
                    
            return cleaned_metadata
            
        except Exception as e:
            self.monitoring.log_error(f"Error cleaning metadata: {str(e)}")
            return {}
            
    def _clean_connection(self, connection: Dict[str, Any]) -> Dict[str, Any]:
        """Clean connection data."""
        try:
            return {
                'id': connection.get('id', ''),
                'type': connection.get('type', 'unknown'),
                'strength': self._clean_score(connection.get('strength', 0)),
                'metadata': self._clean_metadata(connection.get('metadata', {}))
            }
        except Exception as e:
            self.monitoring.log_error(f"Error cleaning connection: {str(e)}")
            return {}
            
    def _clean_network_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Clean network metrics."""
        try:
            return {
                'size': self._clean_number(metrics.get('size', 0)),
                'density': self._clean_score(metrics.get('density', 0)),
                'centrality': self._clean_score(metrics.get('centrality', 0)),
                'clustering': self._clean_score(metrics.get('clustering', 0))
            }
        except Exception as e:
            self.monitoring.log_error(f"Error cleaning network metrics: {str(e)}")
            return {}
            
    def _clean_score(self, score: Any) -> float:
        """Clean score values."""
        try:
            if isinstance(score, (int, float)):
                return min(max(float(score), 0), 1)
            elif isinstance(score, str):
                # Try to convert percentage to decimal
                if '%' in score:
                    return min(max(float(score.strip('%')) / 100, 0), 1)
                # Try to convert fraction to decimal
                elif '/' in score:
                    num, denom = map(float, score.split('/'))
                    return min(max(num / denom, 0), 1)
                else:
                    return min(max(float(score), 0), 1)
            else:
                return 0.0
        except:
            return 0.0 