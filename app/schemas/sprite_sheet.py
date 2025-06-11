# ============================================================================
# 📄 app/schemas/sprite_sheet.py
# ============================================================================

"""
SpriteSheet Schemas - Validação de dados de sprite sheets
========================================================
"""

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class SpriteSheetBase(BaseModel):
    """Base schema para SpriteSheet"""
    frame_count: int = Field(..., ge=1, le=32)
    layout_type: str = Field(default="horizontal", pattern="^(horizontal|vertical|grid|packed)$")
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

    @field_validator('frame_positions', mode='before')
    @classmethod
    def parse_frame_positions(cls, v):
        """Parse JSON string to list"""
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return []
        return v or []

    @field_validator('loop', 'has_transparency', 'is_optimized', 'c2pa_embedded', mode='before')
    @classmethod
    def parse_bool_fields(cls, v):
        """Convert string to bool"""
        if isinstance(v, str):
            return v.lower() == 'true'
        return bool(v)

    @field_validator('compression_ratio', mode='before')
    @classmethod
    def parse_compression_ratio(cls, v):
        """Convert string to float"""
        if isinstance(v, str) and v:
            return float(v)
        return v