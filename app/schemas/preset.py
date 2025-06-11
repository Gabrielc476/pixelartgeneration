# ============================================================================
# 📄 app/schemas/preset.py
# ============================================================================

"""
Preset Schemas - Validação de dados de presets
==============================================
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.preset import PresetType, PresetCategory


class PresetBase(BaseModel):
    """Base schema para Preset"""
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    preset_type: PresetType
    category: PresetCategory = PresetCategory.CUSTOM


class PresetCreate(PresetBase):
    """Schema para criação de preset"""
    configuration: dict = Field(..., description="Configurações do preset em JSON")

    # Display
    icon: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")

    # Metadata
    tags: Optional[List[str]] = Field(default_factory=list)
    recommended_for: Optional[List[str]] = Field(default_factory=list)


class PresetResponse(PresetBase):
    """Schema para resposta de preset"""
    id: UUID
    configuration: dict

    # Display
    thumbnail_path: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    display_name: str

    # System vs User
    is_system: bool
    is_featured: bool
    is_active: bool

    # Usage statistics
    usage_count: int
    rating: float
    rating_count: int

    # Versioning
    version: str
    parent_preset_id: Optional[UUID] = None

    # Metadata
    tags: List[str]
    recommended_for: List[str]

    # Timestamps
    created_at: datetime
    updated_at: datetime

    # URLs
    thumbnail_url: Optional[str] = None

    class Config:
        from_attributes = True


class PresetListResponse(BaseModel):
    """Schema para listagem de presets"""
    presets: List[PresetResponse]
    total: int
    by_type: dict
    by_category: dict
    featured: List[PresetResponse]
    most_used: List[PresetResponse]
