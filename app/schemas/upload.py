"""
Upload Schemas - Validação de dados de upload
=============================================
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class UploadBase(BaseModel):
    """Base schema para Upload"""
    original_filename: str = Field(..., max_length=255)
    content_type: str = Field(..., max_length=100)


class UploadCreate(UploadBase):
    """Schema para criação de upload"""
    file_size: int = Field(..., gt=0, le=10485760)  # Max 10MB

    @field_validator('content_type')
    @classmethod
    def validate_content_type(cls, v):
        """Valida tipo de conteúdo"""
        allowed_types = [
            'image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp'
        ]
        if v not in allowed_types:
            raise ValueError(f'Content type must be one of: {", ".join(allowed_types)}')
        return v


class UploadResponse(UploadBase):
    """Schema para resposta de upload"""
    id: UUID
    user_id: Optional[UUID] = None
    filename: str
    file_size: int
    file_path: str

    # Image properties
    width: Optional[int] = None
    height: Optional[int] = None
    format: Optional[str] = None

    # Analysis status
    analysis_completed: bool
    analysis_error: Optional[str] = None

    # Usage
    usage_count: int

    # Timestamps
    created_at: datetime
    analyzed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    # Computed properties
    file_size_mb: float
    is_analyzed: bool
    aspect_ratio: float
    resolution_string: str

    # URLs
    file_url: Optional[str] = None
    thumbnail_url: Optional[str] = None

    class Config:
        from_attributes = True

    @field_validator('analysis_completed', mode='before')
    @classmethod
    def parse_analysis_completed(cls, v):
        """Convert string to bool"""
        if isinstance(v, str):
            return v.lower() == 'true'
        return bool(v)


class UploadAnalysisResponse(BaseModel):
    """Schema para análise de upload"""
    upload_id: UUID
    detected_style: Optional[str] = None
    suggested_frames: Optional[int] = None
    recommended_size: Optional[dict] = None
    animation_potential: Optional[float] = None
    complexity_score: Optional[float] = None