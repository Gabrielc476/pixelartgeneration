"""
Frame Schemas - Validação de dados de frames individuais
=======================================================
"""

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator


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

    @validator('has_transparency', 'is_optimized', 'c2pa_embedded', pre=True)
    def parse_bool_fields(cls, v):
        """Convert string to bool"""
        if isinstance(v, str):
            return v.lower() == 'true'
        return bool(v)

    @validator('sharpness_score', 'consistency_score', 'motion_score', 'compression_ratio', pre=True)
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


class FrameCreate(FrameBase):
    """Schema para criação de frame"""
    filename: str
    file_path: str
    file_size: int
    width: int
    height: int

    # Optional processing info
    generated_prompt: Optional[str] = None
    generation_seed: Optional[int] = None
    processing_time: Optional[int] = None
    gpt4o_image_id: Optional[str] = None


class FrameUpdate(BaseModel):
    """Schema para atualização de frame"""
    duration: Optional[int] = Field(None, ge=16, le=5000)
    timing_offset: Optional[int] = Field(None, ge=0)
    delay_after: Optional[int] = Field(None, ge=0)

    # Quality metrics
    sharpness_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    consistency_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    motion_score: Optional[float] = Field(None, ge=0.0, le=1.0)


class FrameExportConfig(BaseModel):
    """Schema para configuração de exportação de frames"""
    naming_pattern: str = Field(default="frame_{number:03d}.png")
    include_metadata: bool = True
    optimize: bool = True
    create_zip: bool = True
    include_preview_gif: bool = True

    @validator('naming_pattern')
    def validate_naming_pattern(cls, v):
        """Valida padrão de nomenclatura"""
        if '{number' not in v:
            raise ValueError('Naming pattern must include {number} placeholder')
        return v


class FrameMetadata(BaseModel):
    """Schema para metadados do frame"""
    filename: str
    frame_number: int
    duration: int
    timestamp: int
    size: dict
    quality_metrics: dict
    c2pa_signature: Optional[str] = None


class FrameQualityAnalysis(BaseModel):
    """Schema para análise de qualidade do frame"""
    frame_number: int
    sharpness: float
    consistency: float
    motion_quality: float
    color_distribution: dict
    edge_quality: float
    noise_level: float
    overall_score: float
    recommendations: List[str]


class FrameComparison(BaseModel):
    """Schema para comparação entre frames"""
    frame1_number: int
    frame2_number: int
    similarity_score: float
    motion_vector: dict
    color_difference: float
    shape_changes: List[str]
    transition_quality: float


class FrameBatch(BaseModel):
    """Schema para operações em lote nos frames"""
    frame_numbers: List[int]
    operation: str = Field(..., regex="^(update_duration|optimize|regenerate|delete)$")
    parameters: dict = {}

    @validator('frame_numbers')
    def validate_frame_numbers(cls, v):
        """Valida números dos frames"""
        if not v:
            raise ValueError('At least one frame number is required')
        if any(num < 1 or num > 32 for num in v):
            raise ValueError('Frame numbers must be between 1 and 32')
        return list(set(v))  # Remove duplicates


class FrameSequence(BaseModel):
    """Schema para sequência de frames"""
    frames: List[FrameResponse]
    total_duration: int
    loop_duration: int
    fps: int
    smooth_transitions: bool
    sequence_quality: float