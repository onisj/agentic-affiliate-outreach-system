"""
API Key Management Endpoints

This module provides endpoints for managing API keys with enhanced security features.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, validator
from datetime import datetime, timedelta
import secrets
import hashlib
import ipaddress
import re

from database.models import User, APIKey, APIKeyUsage
from api.dependencies.auth import get_current_user
from src.services.monitoring.monitoring import MonitoringService

router = APIRouter()

class APIKeyCreate(BaseModel):
    name: str
    description: Optional[str]
    expires_at: Optional[datetime]
    permissions: List[str]
    ip_whitelist: Optional[List[str]] = None
    rate_limit: Optional[Dict[str, int]] = None
    max_requests_per_day: Optional[int] = None
    
    @validator('ip_whitelist')
    def validate_ip_whitelist(cls, v):
        if v:
            for ip in v:
                try:
                    ipaddress.ip_network(ip)
                except ValueError:
                    raise ValueError(f"Invalid IP address or network: {ip}")
        return v
    
    @validator('rate_limit')
    def validate_rate_limit(cls, v):
        if v:
            for key, value in v.items():
                if not isinstance(value, int) or value <= 0:
                    raise ValueError(f"Invalid rate limit value for {key}")
        return v

class APIKeyResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    key_prefix: str
    created_at: datetime
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    permissions: List[str]
    is_active: bool
    ip_whitelist: Optional[List[str]]
    rate_limit: Optional[Dict[str, int]]
    max_requests_per_day: Optional[int]
    usage_count: int
    last_ip: Optional[str]

class APIKeyUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    expires_at: Optional[datetime]
    permissions: Optional[List[str]]
    is_active: Optional[bool]
    ip_whitelist: Optional[List[str]]
    rate_limit: Optional[Dict[str, int]]
    max_requests_per_day: Optional[int]

class APIKeyUsageStats(BaseModel):
    total_requests: int
    requests_by_endpoint: Dict[str, int]
    requests_by_ip: Dict[str, int]
    requests_by_date: Dict[str, int]
    average_response_time: float
    error_rate: float

def generate_api_key() -> tuple[str, str]:
    """Generate a new API key and its prefix"""
    key = secrets.token_urlsafe(32)
    prefix = key[:8]
    return key, prefix

def hash_api_key(key: str) -> str:
    """Hash an API key for storage"""
    return hashlib.sha256(key.encode()).hexdigest()

def validate_ip_whitelist(ip: str, whitelist: List[str]) -> bool:
    """Validate if an IP is in the whitelist"""
    if not whitelist:
        return True
    try:
        ip_obj = ipaddress.ip_address(ip)
        return any(ip_obj in ipaddress.ip_network(allowed) for allowed in whitelist)
    except ValueError:
        return False

@router.post("", response_model=APIKeyResponse)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new API key with enhanced security features"""
    try:
        key, prefix = generate_api_key()
        hashed_key = hash_api_key(key)
        
        api_key = await APIKey.create(
            user_id=current_user.id,
            name=key_data.name,
            description=key_data.description,
            key_hash=hashed_key,
            key_prefix=prefix,
            expires_at=key_data.expires_at,
            permissions=key_data.permissions,
            ip_whitelist=key_data.ip_whitelist,
            rate_limit=key_data.rate_limit,
            max_requests_per_day=key_data.max_requests_per_day
        )
        
        # Return the full key only once during creation
        response = api_key.dict()
        response["key"] = key
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_user)
):
    """List all API keys for the current user"""
    try:
        api_keys = await APIKey.get_by_user_id(current_user.id)
        return api_keys
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{key_id}", response_model=APIKeyResponse)
async def get_api_key(
    key_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get details of a specific API key"""
    try:
        api_key = await APIKey.get_by_id(key_id)
        if not api_key or api_key.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        return api_key
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/{key_id}", response_model=APIKeyResponse)
async def update_api_key(
    key_id: int,
    key_update: APIKeyUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update an API key"""
    try:
        api_key = await APIKey.get_by_id(key_id)
        if not api_key or api_key.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        update_data = key_update.dict(exclude_unset=True)
        updated_key = await api_key.update(**update_data)
        return updated_key
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: int,
    current_user: User = Depends(get_current_user)
):
    """Delete an API key"""
    try:
        api_key = await APIKey.get_by_id(key_id)
        if not api_key or api_key.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        await api_key.delete()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/{key_id}/rotate")
async def rotate_api_key(
    key_id: int,
    current_user: User = Depends(get_current_user)
):
    """Rotate an API key"""
    try:
        api_key = await APIKey.get_by_id(key_id)
        if not api_key or api_key.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        new_key, new_prefix = generate_api_key()
        hashed_key = hash_api_key(new_key)
        
        await api_key.update(
            key_hash=hashed_key,
            key_prefix=new_prefix,
            last_rotated_at=datetime.utcnow()
        )
        
        return {"key": new_key}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{key_id}/usage", response_model=APIKeyUsageStats)
async def get_key_usage_stats(
    key_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user)
):
    """Get API key usage statistics"""
    try:
        api_key = await APIKey.get_by_id(key_id)
        if not api_key or api_key.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        stats = await APIKeyUsage.get_stats(
            key_id=key_id,
            start_date=start_date,
            end_date=end_date
        )
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/{key_id}/block-ip")
async def block_ip(
    key_id: int,
    ip: str,
    current_user: User = Depends(get_current_user)
):
    """Block an IP address from using the API key"""
    try:
        api_key = await APIKey.get_by_id(key_id)
        if not api_key or api_key.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        await api_key.add_blocked_ip(ip)
        return {"message": f"IP {ip} has been blocked"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/{key_id}/unblock-ip")
async def unblock_ip(
    key_id: int,
    ip: str,
    current_user: User = Depends(get_current_user)
):
    """Unblock an IP address from using the API key"""
    try:
        api_key = await APIKey.get_by_id(key_id)
        if not api_key or api_key.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        await api_key.remove_blocked_ip(ip)
        return {"message": f"IP {ip} has been unblocked"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{key_id}/blocked-ips")
async def get_blocked_ips(
    key_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get list of blocked IP addresses for an API key"""
    try:
        api_key = await APIKey.get_by_id(key_id)
        if not api_key or api_key.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        blocked_ips = await api_key.get_blocked_ips()
        return {"blocked_ips": blocked_ips}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 