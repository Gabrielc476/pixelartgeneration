# ============================================================================
# 📄 app/schemas/frame.py
# ============================================================================

"""
Frame Schemas - Validação de dados de frames individuais
=======================================================
"""

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class FrameBase(BaseModel):
    """Base schema para Frame"""
    frame_number: int = Field(..., ge=1, le=32)
    duration: int = Field(default=100, ge=16, le=5000)  # ms


class FrameResponse(FrameBase):
    """Schema para resposta de frame"""
    id: UUID
    job_id: UUID

    # File information
    filename: str
    file_path: str
    file_size: int

    # Frame properties
    width: int
    height: int

    # Animation properties
    timing_offset: int  # ms
    delay_after: int  # ms

    # Visual properties
    format: str
    has_transparency: bool
    color_count: Optional[int] = None

    # Processing information
    generated_prompt: Optional[str] = None
    generation_seed: Optional[int] = None
    processing_time: Optional[int] = None  # ms

    # Quality metrics
    sharpness_score: Optional[float] = None
    consistency_score: Optional[float] = None
    motion_score: Optional[float] = None

    # Optimization
    is_optimized: bool
    original_size: Optional[int] = None
    compression_ratio: Optional[float] = None

    # Metadata
    c2pa_embedded: bool
    generated_with: str
    gpt4o_image_id: Optional[str] = None

    # Computed properties
    file_size_kb: float
    resolution_string: str
    duration_seconds: float
    timing_offset_seconds: float
    formatted_filename: str
    quality_metrics: dict

    # URLs
    file_url: Optional[str] = None
    thumbnail_url: Optional[str] = None

    class Config:
        from_attributes = True

    @field_validator('has_transparency', 'is_optimized', 'c2pa_embedded', mode='before')
    @classmethod
    def parse_bool_fields(cls, v):
        """Convert string to bool"""
        if isinstance(v, str):
            return v.lower() == 'true'
        return bool(v)

    @field_validator('sharpness_score', 'consistency_score', 'motion_score', 'compression_ratio', mode='before')
    @classmethod
    def parse_float_fields(cls, v):
        """Convert string to float"""
        if isinstance(v, str) and v:
            return float(v)
        return v


class FrameListResponse(BaseModel):
    """Schema para listagem de frames"""
    frames: List[FrameResponse]
    total: int
    animation_preview_url: Optional[str] = None
    zip_download_url: Optional[str] = None
    total_size: int
    avg_quality: float