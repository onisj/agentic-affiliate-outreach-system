"""
User Management Endpoints

This module provides endpoints for managing users and their settings.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr
from datetime import datetime

from database.models import User, UserSettings, UserProfile
from api.dependencies.auth import get_current_user, get_password_hash, verify_password

router = APIRouter()

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    company: Optional[str]
    role: Optional[str]

class UserUpdate(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    company: Optional[str]
    role: Optional[str]
    is_active: Optional[bool]

class UserSettingsUpdate(BaseModel):
    notification_preferences: Optional[Dict[str, bool]]
    default_campaign_settings: Optional[Dict[str, Any]]
    api_rate_limits: Optional[Dict[str, int]]
    timezone: Optional[str]
    language: Optional[str]

class UserProfileResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    company: Optional[str]
    role: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    settings: Optional[Dict[str, Any]]

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

@router.post("", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    """Create a new user"""
    try:
        # Check if user already exists
        existing_user = await User.get_by_email(user.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user
        user_data = user.dict()
        user_data["password"] = get_password_hash(user.password)
        new_user = await User.create(**user_data)
        
        # Create default settings
        await UserSettings.create(user_id=new_user.id)
        
        return new_user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current user's profile"""
    try:
        settings = await UserSettings.get_by_user_id(current_user.id)
        return {
            **current_user.dict(),
            "settings": settings.dict() if settings else None
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/me", response_model=UserProfileResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update current user's profile"""
    try:
        update_data = user_update.dict(exclude_unset=True)
        updated_user = await current_user.update(**update_data)
        return updated_user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/me/settings", response_model=UserProfileResponse)
async def update_user_settings(
    settings_update: UserSettingsUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update user settings"""
    try:
        settings = await UserSettings.get_by_user_id(current_user.id)
        if not settings:
            settings = await UserSettings.create(user_id=current_user.id)
        
        update_data = settings_update.dict(exclude_unset=True)
        updated_settings = await settings.update(**update_data)
        
        return {
            **current_user.dict(),
            "settings": updated_settings.dict()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/me/password")
async def change_password(
    password_change: PasswordChange,
    current_user: User = Depends(get_current_user)
):
    """Change user password"""
    try:
        if not verify_password(password_change.current_password, current_user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        new_password_hash = get_password_hash(password_change.new_password)
        await current_user.update(password=new_password_hash)
        
        return {"message": "Password updated successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/me/api-keys")
async def get_api_keys(
    current_user: User = Depends(get_current_user)
):
    """Get user's API keys"""
    try:
        # TODO: Implement API key management
        return {"message": "API key management not implemented yet"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/me/api-keys")
async def create_api_key(
    current_user: User = Depends(get_current_user)
):
    """Create a new API key"""
    try:
        # TODO: Implement API key generation
        return {"message": "API key generation not implemented yet"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/me/api-keys/{key_id}")
async def delete_api_key(
    key_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete an API key"""
    try:
        # TODO: Implement API key deletion
        return {"message": "API key deletion not implemented yet"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 