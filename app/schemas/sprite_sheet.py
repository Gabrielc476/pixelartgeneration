"""
SpriteSheet Schemas - Validação de dados de sprite sheets
========================================================
"""

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator


class SpriteSheetBase(BaseModel):
    """Base schema para SpriteSheet"""
    frame_count: int = Field(..., ge=1, le=32)
    layout_type: str = Field(default="horizontal", regex="^(horizontal|vertical|grid|packed)$")
    spacing: int = Field(default=0, ge=0, le=50)
    padding: int = Field(default=0, ge=0, le=50)


class SpriteSheetResponse(SpriteSheetBase):
    """Schema para resposta de sprite sheet"""
    id: UUID
    job_id: UUID

    # File information
    file_path: str
    filename: str
    file_size: int

    # Sprite sheet properties
    sheet_width: int
    sheet_height: int

    # Layout configuration
    columns: Optional[int] = None
    rows: Optional[int] = None

    # Frame properties
    frame_width: int
    frame_height: int

    # Animation properties
    fps: int
    loop: bool
    total_duration: int  # ms

    # File format
    format: str
    has_transparency: bool
    color_depth: int

    # Optimization
    is_optimized: bool
    original_size: Optional[int] = None
    compression_ratio: Optional[float] = None

    # Frame mapping
    frame_positions: Optional[List[dict]] = None

    # Metadata
    c2pa_embedded: bool
    generated_with: str

    # Computed properties
    file_size_mb: float
    resolution_string: str
    frame_size_string: str
    duration_seconds: float
    layout_info: dict

    # URLs
    file_url: Optional[str] = None
    preview_url: Optional[str] = None
    thumbnail_url: Optional[str] = None

    class Config:
        from_attributes = True

    @validator('frame_positions', pre=True)
    def parse_frame_positions(cls, v):
        """Parse JSON string to list"""
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return []
        return v or []

    @validator('loop', 'has_transparency', 'is_optimized', 'c2pa_embedded', pre=True)
    def parse_bool_fields(cls, v):
        """Convert string to bool"""
        if isinstance(v, str):
            return v.lower() == 'true'
        return bool(v)

    @validator('compression_ratio', pre=True)
    def parse_compression_ratio(cls, v):
        """Convert string to float"""
        if isinstance(v, str) and v:
            return float(v)
        return v


class SpriteSheetExportConfig(BaseModel):
    """Schema para configuração de exportação de sprite sheet"""
    layout_type: str = Field(default="horizontal", regex="^(horizontal|vertical|grid|packed)$")
    columns: Optional[int] = Field(None, ge=1, le=16)
    rows: Optional[int] = Field(None, ge=1, le=16)
    spacing: int = Field(default=0, ge=0, le=50)
    padding: int = Field(default=0, ge=0, le=50)
    optimize: bool = True
    include_metadata: bool = True

    @validator('columns')
    def validate_columns_for_grid(cls, v, values):
        """Valida colunas para layout grid"""
        layout_type = values.get('layout_type')
        if layout_type == 'grid' and not v:
            raise ValueError('Columns is required for grid layout')
        return v


class SpriteSheetMetadata(BaseModel):
    """Schema para metadados do sprite sheet"""
    format: str
    frame_count: int
    frame_size: dict
    layout: dict
    animation: dict
    frames: List[dict]
    c2pa_metadata: Optional[dict] = None


class SpriteSheetPreview(BaseModel):
    """Schema para preview do sprite sheet"""
    layout_preview_url: str
    animation_preview_url: str
    frame_details: List[dict]
    layout_info: dict
    file_size_estimate: int


class SpriteSheetOptimization(BaseModel):
    """Schema para otimização do sprite sheet"""
    original_size: int
    optimized_size: int
    compression_ratio: float
    optimization_applied: List[str]
    quality_score: float


class SpriteSheetAnalysis(BaseModel):
    """Schema para análise do sprite sheet"""
    frame_consistency: float
    color_efficiency: float
    layout_efficiency: float
    animation_quality: float
    optimization_suggestions: List[str]