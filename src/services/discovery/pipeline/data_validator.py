"""
Data Validator

This module implements data validation for scraped data.
"""

from typing import Dict, List, Any
import logging
import re
from jsonschema import validate, ValidationError
from src.services.monitoring.monitoring import MonitoringService

logger = logging.getLogger(__name__)

class DataValidator:
    """Validates scraped data against schemas."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.monitoring = MonitoringService()
        
        # Define validation schemas
        self.schemas = {
            'profile': self._get_profile_schema(),
            'content': self._get_content_schema(),
            'engagement': self._get_engagement_schema(),
            'network': self._get_network_schema()
        }
        
    def validate_profile_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate profile data against schemas."""
        try:
            validation_results = {
                'basic_info': self._validate_basic_info(data.get('basic_info', {})),
                'content': self._validate_content(data.get('content', [])),
                'engagement': self._validate_engagement(data.get('engagement', {})),
                'network': self._validate_network(data.get('network', {}))
            }
            
            return validation_results
            
        except Exception as e:
            self.monitoring.log_error(f"Error validating profile data: {str(e)}")
            return {}
            
    def _validate_basic_info(self, info: Dict[str, Any]) -> Dict[str, Any]:
        """Validate basic profile information."""
        try:
            # Validate against schema
            validate(instance=info, schema=self.schemas['profile'])
            
            # Additional validations
            validation_results = {
                'is_valid': True,
                'errors': [],
                'warnings': []
            }
            
            # Validate required fields
            required_fields = ['username', 'name', 'bio']
            for field in required_fields:
                if field not in info or not info[field]:
                    validation_results['is_valid'] = False
                    validation_results['errors'].append(f"Missing required field: {field}")
                    
            # Validate field formats
            if 'email' in info and not self._validate_email(info['email']):
                validation_results['is_valid'] = False
                validation_results['errors'].append("Invalid email format")
                
            if 'website' in info and not self._validate_url(info['website']):
                validation_results['is_valid'] = False
                validation_results['errors'].append("Invalid website URL")
                
            # Validate field lengths
            if 'bio' in info and len(info['bio']) > 1000:
                validation_results['warnings'].append("Bio exceeds recommended length")
                
            return validation_results
            
        except ValidationError as e:
            return {
                'is_valid': False,
                'errors': [str(e)],
                'warnings': []
            }
        except Exception as e:
            self.monitoring.log_error(f"Error validating basic info: {str(e)}")
            return {'is_valid': False, 'errors': [str(e)], 'warnings': []}
            
    def _validate_content(self, content: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate content data."""
        try:
            validation_results = {
                'is_valid': True,
                'errors': [],
                'warnings': []
            }
            
            for item in content:
                try:
                    # Validate against schema
                    validate(instance=item, schema=self.schemas['content'])
                    
                    # Additional validations
                    if 'text' in item and len(item['text']) > 5000:
                        validation_results['warnings'].append(
                            "Content text exceeds recommended length"
                        )
                        
                    if 'media' in item:
                        for media in item['media']:
                            if not self._validate_media(media):
                                validation_results['is_valid'] = False
                                validation_results['errors'].append(
                                    "Invalid media format"
                                )
                                
                except ValidationError as e:
                    validation_results['is_valid'] = False
                    validation_results['errors'].append(str(e))
                    
            return validation_results
            
        except Exception as e:
            self.monitoring.log_error(f"Error validating content: {str(e)}")
            return {'is_valid': False, 'errors': [str(e)], 'warnings': []}
            
    def _validate_engagement(self, engagement: Dict[str, Any]) -> Dict[str, Any]:
        """Validate engagement data."""
        try:
            # Validate against schema
            validate(instance=engagement, schema=self.schemas['engagement'])
            
            validation_results = {
                'is_valid': True,
                'errors': [],
                'warnings': []
            }
            
            # Validate numeric fields
            numeric_fields = ['likes', 'comments', 'shares', 'views']
            for field in numeric_fields:
                if field in engagement:
                    if not isinstance(engagement[field], (int, float)):
                        validation_results['is_valid'] = False
                        validation_results['errors'].append(
                            f"Invalid {field} value: must be numeric"
                        )
                    elif engagement[field] < 0:
                        validation_results['is_valid'] = False
                        validation_results['errors'].append(
                            f"Invalid {field} value: must be non-negative"
                        )
                        
            # Validate rates
            if 'engagement_rate' in engagement:
                rate = engagement['engagement_rate']
                if not isinstance(rate, (int, float)) or rate < 0 or rate > 1:
                    validation_results['is_valid'] = False
                    validation_results['errors'].append(
                        "Invalid engagement rate: must be between 0 and 1"
                    )
                    
            return validation_results
            
        except ValidationError as e:
            return {
                'is_valid': False,
                'errors': [str(e)],
                'warnings': []
            }
        except Exception as e:
            self.monitoring.log_error(f"Error validating engagement: {str(e)}")
            return {'is_valid': False, 'errors': [str(e)], 'warnings': []}
            
    def _validate_network(self, network: Dict[str, Any]) -> Dict[str, Any]:
        """Validate network data."""
        try:
            # Validate against schema
            validate(instance=network, schema=self.schemas['network'])
            
            validation_results = {
                'is_valid': True,
                'errors': [],
                'warnings': []
            }
            
            # Validate connections
            if 'connections' in network:
                for connection in network['connections']:
                    if not self._validate_connection(connection):
                        validation_results['is_valid'] = False
                        validation_results['errors'].append(
                            "Invalid connection format"
                        )
                        
            # Validate metrics
            if 'metrics' in network:
                metrics = network['metrics']
                if not self._validate_metrics(metrics):
                    validation_results['is_valid'] = False
                    validation_results['errors'].append(
                        "Invalid metrics format"
                    )
                    
            return validation_results
            
        except ValidationError as e:
            return {
                'is_valid': False,
                'errors': [str(e)],
                'warnings': []
            }
        except Exception as e:
            self.monitoring.log_error(f"Error validating network: {str(e)}")
            return {'is_valid': False, 'errors': [str(e)], 'warnings': []}
            
    def _validate_email(self, email: str) -> bool:
        """Validate email format."""
        try:
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            return bool(re.match(pattern, email))
        except:
            return False
            
    def _validate_url(self, url: str) -> bool:
        """Validate URL format."""
        try:
            pattern = r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
            return bool(re.match(pattern, url))
        except:
            return False
            
    def _validate_media(self, media: Dict[str, Any]) -> bool:
        """Validate media format."""
        try:
            required_fields = ['type', 'url']
            return all(field in media for field in required_fields)
        except:
            return False
            
    def _validate_connection(self, connection: Dict[str, Any]) -> bool:
        """Validate connection format."""
        try:
            required_fields = ['id', 'type']
            return all(field in connection for field in required_fields)
        except:
            return False
            
    def _validate_metrics(self, metrics: Dict[str, Any]) -> bool:
        """Validate metrics format."""
        try:
            required_fields = ['size', 'density']
            return all(field in metrics for field in required_fields)
        except:
            return False
            
    def _get_profile_schema(self) -> Dict[str, Any]:
        """Get profile validation schema."""
        return {
            'type': 'object',
            'properties': {
                'username': {'type': 'string'},
                'name': {'type': 'string'},
                'bio': {'type': 'string'},
                'email': {'type': 'string'},
                'website': {'type': 'string'},
                'location': {'type': 'string'},
                'profile_picture': {'type': 'string'},
                'banner_image': {'type': 'string'},
                'join_date': {'type': 'string'},
                'last_active': {'type': 'string'}
            },
            'required': ['username', 'name']
        }
        
    def _get_content_schema(self) -> Dict[str, Any]:
        """Get content validation schema."""
        return {
            'type': 'object',
            'properties': {
                'id': {'type': 'string'},
                'type': {'type': 'string'},
                'text': {'type': 'string'},
                'media': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'type': {'type': 'string'},
                            'url': {'type': 'string'}
                        },
                        'required': ['type', 'url']
                    }
                },
                'timestamp': {'type': 'string'},
                'engagement': {
                    'type': 'object',
                    'properties': {
                        'likes': {'type': 'number'},
                        'comments': {'type': 'number'},
                        'shares': {'type': 'number'},
                        'views': {'type': 'number'}
                    }
                }
            },
            'required': ['id', 'type']
        }
        
    def _get_engagement_schema(self) -> Dict[str, Any]:
        """Get engagement validation schema."""
        return {
            'type': 'object',
            'properties': {
                'likes': {'type': 'number'},
                'comments': {'type': 'number'},
                'shares': {'type': 'number'},
                'views': {'type': 'number'},
                'engagement_rate': {'type': 'number'},
                'quality_score': {'type': 'number'}
            }
        }
        
    def _get_network_schema(self) -> Dict[str, Any]:
        """Get network validation schema."""
        return {
            'type': 'object',
            'properties': {
                'connections': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'string'},
                            'type': {'type': 'string'},
                            'strength': {'type': 'number'}
                        },
                        'required': ['id', 'type']
                    }
                },
                'metrics': {
                    'type': 'object',
                    'properties': {
                        'size': {'type': 'number'},
                        'density': {'type': 'number'},
                        'centrality': {'type': 'number'},
                        'clustering': {'type': 'number'}
                    },
                    'required': ['size', 'density']
                }
            }
        } 