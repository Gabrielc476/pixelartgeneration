"""
Preset Schemas - Validação de dados de presets
==============================================
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator

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
    color: Optional[str] = Field(None, regex="^#[0-9A-Fa-f]{6}$")

    # Metadata
    tags: Optional[List[str]] = Field(default_factory=list)
    recommended_for: Optional[List[str]] = Field(default_factory=list)

    @validator('configuration')
    def validate_configuration_by_type(cls, v, values):
        """Valida configuração baseada no tipo de preset"""
        preset_type = values.get('preset_type')

        if preset_type == PresetType.STYLE:
            required_fields = ['style', 'style_strength']
            for field in required_fields:
                if field not in v:
                    raise ValueError(f'Style preset must include {field}')

        elif preset_type == PresetType.ANIMATION:
            required_fields = ['animation_type', 'frames', 'fps']
            for field in required_fields:
                if field not in v:
                    raise ValueError(f'Animation preset must include {field}')

        elif preset_type == PresetType.FRAME_SIZE:
            required_fields = ['frame_width', 'frame_height']
            for field in required_fields:
                if field not in v:
                    raise ValueError(f'Frame size preset must include {field}')

        elif preset_type == PresetType.COMBINED:
            # Preset combinado deve ter ao menos um tipo de configuração
            style_fields = ['style', 'style_strength']
            animation_fields = ['animation_type', 'frames', 'fps']
            size_fields = ['frame_width', 'frame_height']

            has_style = any(field in v for field in style_fields)
            has_animation = any(field in v for field in animation_fields)
            has_size = any(field in v for field in size_fields)

            if not (has_style or has_animation or has_size):
                raise ValueError('Combined preset must include at least one configuration type')

        return v

    @validator('tags', 'recommended_for')
    def validate_string_lists(cls, v):
        """Valida listas de strings"""
        if v and len(v) > 10:
            raise ValueError('Maximum 10 items allowed')
        return v or []


class PresetUpdate(BaseModel):
    """Schema para atualização de preset"""
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    configuration: Optional[dict] = None
    icon: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, regex="^#[0-9A-Fa-f]{6}$")
    is_active: Optional[bool] = None
    tags: Optional[List[str]] = None
    recommended_for: Optional[List[str]] = None


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

    @validator('rating', pre=True)
    def parse_rating(cls, v):
        """Convert string to float"""
        if isinstance(v, str):
            return float(v) if v else 0.0
        return v or 0.0

    @validator('tags', 'recommended_for', pre=True)
    def parse_json_lists(cls, v):
        """Parse JSON string to list"""
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return []
        return v or []


class PresetListResponse(BaseModel):
    """Schema para listagem de presets"""
    presets: List[PresetResponse]
    total: int
    by_type: dict
    by_category: dict
    featured: List[PresetResponse]
    most_used: List[PresetResponse]


class PresetFilter(BaseModel):
    """Schema para filtros de preset"""
    preset_type: Optional[List[PresetType]] = None
    category: Optional[List[PresetCategory]] = None
    is_system: Optional[bool] = None
    is_featured: Optional[bool] = None
    is_active: Optional[bool] = None
    tags: Optional[List[str]] = None
    min_rating: Optional[float] = Field(None, ge=0.0, le=5.0)
    search: Optional[str] = Field(None, max_length=100)


class PresetRating(BaseModel):
    """Schema para avaliação de preset"""
    preset_id: UUID
    rating: float = Field(..., ge=1.0, le=5.0)
    comment: Optional[str] = Field(None, max_length=500)


class PresetUsage(BaseModel):
    """Schema para uso de preset"""
    preset_id: UUID
    job_id: UUID
    configuration_overrides: Optional[dict] = Field(default_factory=dict)


class PresetStats(BaseModel):
    """Schema para estatísticas de presets"""
    total_presets: int
    system_presets: int
    user_presets: int
    by_type: dict
    by_category: dict
    most_used: List[dict]
    highest_rated: List[dict]
    recent_additions: List[dict]


class PresetRecommendation(BaseModel):
    """Schema para recomendação de presets"""
    user_prompt: Optional[str] = None
    upload_analysis: Optional[dict] = None
    target_style: Optional[str] = None
    target_animation: Optional[str] = None

    recommended_presets: List[PresetResponse]
    confidence_scores: List[float]
    reasons: List[str]


class PresetTemplate(BaseModel):
    """Schema para template de preset"""
    name: str
    description: str
    preset_type: PresetType
    category: PresetCategory
    base_configuration: dict
    customizable_fields: List[str]
    field_constraints: dict
    preview_images: List[str]