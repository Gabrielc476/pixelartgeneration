"""
Upload Schemas - Validação de dados de upload
=============================================
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator


class UploadBase(BaseModel):
    """Base schema para Upload"""
    original_filename: str = Field(..., max_length=255)
    content_type: str = Field(..., max_length=100)


class UploadCreate(UploadBase):
    """Schema para criação de upload"""
    file_size: int = Field(..., gt=0, le=10485760)  # Max 10MB

    @validator('content_type')
    def validate_content_type(cls, v):
        """Valida tipo de conteúdo"""
        allowed_types = [
            'image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp'
        ]
        if v not in allowed_types:
            raise ValueError(f'Content type must be one of: {", ".join(allowed_types)}')
        return v

    @validator('original_filename')
    def validate_filename(cls, v):
        """Valida nome do arquivo"""
        allowed_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.webp']
        if not any(v.lower().endswith(ext) for ext in allowed_extensions):
            raise ValueError(f'File must have one of these extensions: {", ".join(allowed_extensions)}')
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


class UploadAnalysisResponse(UploadResponse):
    """Schema para resposta com análise completa"""
    # AI Analysis results
    detected_style: Optional[str] = None
    suggested_frames: Optional[int] = None
    recommended_width: Optional[int] = None
    recommended_height: Optional[int] = None
    color_count: Optional[int] = None
    has_transparency: bool
    dominant_colors: Optional[List[str]] = None

    # Analysis details
    complexity_score: Optional[float] = None
    animation_potential: Optional[float] = None
    pixel_art_score: Optional[float] = None
    recommended_styles: Optional[List[str]] = None

    @validator('dominant_colors', pre=True)
    def parse_dominant_colors(cls, v):
        """Parse JSON string to list"""
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return []
        return v or []

    @validator('has_transparency', pre=True)
    def parse_has_transparency(cls, v):
        """Convert string to bool"""
        if isinstance(v, str):
            return v.lower() == 'true'
        return bool(v)


class UploadStats(BaseModel):
    """Schema para estatísticas de uploads"""
    total_uploads: int
    analyzed_uploads: int
    failed_analysis: int
    avg_file_size: float
    most_common_formats: List[dict]
    most_detected_styles: List[dict]


class ImageAnalysisRequest(BaseModel):
    """Schema para solicitar análise de imagem"""
    upload_id: UUID
    analyze_style: bool = True
    analyze_colors: bool = True
    analyze_complexity: bool = True
    suggest_animation: bool = True


class ImageAnalysisResult(BaseModel):
    """Schema para resultado de análise"""
    upload_id: UUID

    # Style analysis
    detected_style: str
    style_confidence: float
    alternative_styles: List[str]

    # Animation suggestions
    suggested_frames: int
    recommended_fps: int
    animation_types: List[str]

    # Technical recommendations
    recommended_size: dict
    color_optimization: dict
    processing_hints: List[str]

    # Quality metrics
    pixel_art_score: float
    animation_potential: float
    complexity_score: float


class UploadListResponse(BaseModel):
    """Schema para listagem de uploads"""
    uploads: List[UploadResponse]
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool


class UploadFilter(BaseModel):
    """Schema para filtros de upload"""
    content_type: Optional[List[str]] = None
    analyzed: Optional[bool] = None
    min_size: Optional[int] = None
    max_size: Optional[int] = None
    width_range: Optional[tuple[int, int]] = None
    height_range: Optional[tuple[int, int]] = None
    detected_style: Optional[List[str]] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None