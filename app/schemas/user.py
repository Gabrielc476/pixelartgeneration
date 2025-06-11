# ============================================================================
# 📄 app/schemas/user.py
# ============================================================================

"""
User Schemas - Validação de dados de usuário
============================================
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserBase(BaseModel):
    """Base schema para User"""
    email: EmailStr
    username: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None


class UserCreate(UserBase):
    """Schema para criação de usuário"""
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    preferred_style: str = Field(default="8-bit")
    default_frame_count: int = Field(default=8, ge=1, le=32)
    default_frame_size: str = Field(default="64x64")

    @field_validator('default_frame_size')
    @classmethod
    def validate_frame_size(cls, v):
        """Valida formato do frame size"""
        try:
            width, height = v.split('x')
            w, h = int(width), int(height)
            if not (16 <= w <= 512 and 16 <= h <= 512):
                raise ValueError("Frame size must be between 16x16 and 512x512")
            return v
        except (ValueError, AttributeError):
            raise ValueError("Frame size must be in format 'WIDTHxHEIGHT'")


class UserResponse(UserBase):
    """Schema para resposta de usuário"""
    id: UUID
    is_active: bool
    is_verified: bool
    is_premium: bool

    # Preferences
    preferred_style: str
    default_frame_count: int
    default_frame_size: str

    # Usage Stats
    daily_generations: int
    max_daily_generations: int
    total_generations: int
    can_generate: bool

    # Timestamps
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True