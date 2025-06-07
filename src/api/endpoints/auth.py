"""
Authentication Endpoints

This module provides endpoints for user authentication and authorization.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr

from database.models import User
from services.auth import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    verify_password
)
from config.settings import get_settings

router = APIRouter()
settings = get_settings()

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    is_active: bool
    created_at: datetime

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Get access token for authentication"""
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate):
    """Register a new user"""
    # Check if user already exists
    existing_user = await User.get_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user = await User.create(
        email=user_data.email,
        password=hashed_password,
        full_name=user_data.full_name
    )
    
    return user

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user's information"""
    return current_user

@router.post("/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user)
):
    """Change user's password"""
    if not verify_password(current_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    hashed_password = get_password_hash(new_password)
    await current_user.update(password=hashed_password)
    return {"message": "Password updated successfully"}

@router.post("/reset-password")
async def request_password_reset(email: EmailStr):
    """Request password reset"""
    user = await User.get_by_email(email)
    if user:
        # TODO: Implement password reset email sending
        pass
    return {"message": "If the email exists, a password reset link has been sent"}

@router.post("/verify-email/{token}")
async def verify_email(token: str):
    """Verify user's email address"""
    # TODO: Implement email verification
    return {"message": "Email verification not implemented yet"} 