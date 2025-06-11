"""
User Schemas - Validação de dados de usuário
============================================
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, validator


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

    @validator('default_frame_size')
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


class UserUpdate(BaseModel):
    """Schema para atualização de usuário"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    display_name: Optional[str] = Field(None, max_length=100)
    avatar_url: Optional[str] = None
    preferred_style: Optional[str] = None
    default_frame_count: Optional[int] = Field(None, ge=1, le=32)
    default_frame_size: Optional[str] = None

    @validator('default_frame_size')
    def validate_frame_size(cls, v):
        """Valida formato do frame size"""
        if v is None:
            return v
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

    @validator('daily_generations', 'max_daily_generations', 'total_generations', pre=True)
    def convert_string_to_int(cls, v):
        """Converte strings para int"""
        if isinstance(v, str):
            return int(v)
        return v


class UserStats(BaseModel):
    """Schema para estatísticas do usuário"""
    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    total_frames_generated: int
    total_sprite_sheets: int
    favorite_styles: list[str]
    avg_processing_time: float


class UserPreferences(BaseModel):
    """Schema para preferências do usuário"""
    preferred_style: str
    default_frame_count: int = Field(ge=1, le=32)
    default_frame_size: str
    default_animation_type: str = "walk_cycle"
    default_fps: int = Field(default=12, ge=1, le=60)
    auto_optimize: bool = True
    embed_c2pa: bool = True

    @validator('default_frame_size')
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