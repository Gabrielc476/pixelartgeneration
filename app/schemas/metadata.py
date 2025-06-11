"""
Metadata Schemas - Validação de dados de metadados
==================================================
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator

from app.models.metadata import MetadataType


class MetadataBase(BaseModel):
    """Base schema para Metadata"""
    metadata_type: MetadataType
    target_entity: str = Field(..., regex="^(job|sprite_sheet|frame|export)$")
    target_id: Optional[UUID] = None


class MetadataCreate(MetadataBase):
    """Schema para criação de metadata"""
    # Content Authenticity (C2PA)
    c2pa_manifest: Optional[Dict[str, Any]] = None
    generator: str = Field(default="GPT-4o Images")
    created_with: str = Field(default="Sora Pixel Art Generator")
    provenance: str = Field(default="AI Generated Content")
    model_version: Optional[str] = None

    # Generation Metadata
    generation_prompt: Optional[str] = None
    generation_settings: Optional[Dict[str, Any]] = None
    seed_used: Optional[str] = None
    processing_time: Optional[float] = None

    # Animation Metadata
    animation_info: Optional[Dict[str, Any]] = None
    frame_timings: Optional[List[Dict[str, Any]]] = None
    loop_info: Optional[Dict[str, Any]] = None

    # Quality Metrics
    quality_scores: Optional[Dict[str, float]] = None
    consistency_metrics: Optional[Dict[str, float]] = None
    optimization_info: Optional[Dict[str, Any]] = None

    # Export Metadata
    export_settings: Optional[Dict[str, Any]] = None
    file_info: Optional[Dict[str, Any]] = None
    compression_info: Optional[Dict[str, Any]] = None

    # Technical Information
    software_version: str = Field(default="1.0.0")
    api_version: Optional[str] = None
    platform_info: Optional[Dict[str, Any]] = None

    # Compliance and Legal
    copyright_info: Optional[str] = None
    license_info: Optional[str] = None
    usage_rights: Optional[str] = None


class MetadataResponse(MetadataBase):
    """Schema para resposta de metadata"""
    id: UUID
    job_id: UUID

    # Content Authenticity (C2PA)
    c2pa_manifest: Optional[Dict[str, Any]] = None
    generator: str
    created_with: str
    provenance: str
    model_version: Optional[str] = None

    # Generation Metadata
    generation_prompt: Optional[str] = None
    generation_settings: Optional[Dict[str, Any]] = None
    seed_used: Optional[str] = None
    processing_time: Optional[float] = None

    # Animation Metadata
    animation_info: Optional[Dict[str, Any]] = None
    frame_timings: Optional[List[Dict[str, Any]]] = None
    loop_info: Optional[Dict[str, Any]] = None

    # Quality Metrics
    quality_scores: Optional[Dict[str, float]] = None
    consistency_metrics: Optional[Dict[str, float]] = None
    optimization_info: Optional[Dict[str, Any]] = None

    # Export Metadata
    export_settings: Optional[Dict[str, Any]] = None
    file_info: Optional[Dict[str, Any]] = None
    compression_info: Optional[Dict[str, Any]] = None

    # Technical Information
    software_version: str
    api_version: Optional[str] = None
    platform_info: Optional[Dict[str, Any]] = None

    # Compliance and Legal
    copyright_info: Optional[str] = None
    license_info: Optional[str] = None
    usage_rights: Optional[str] = None

    # Timestamps
    created_at: datetime

    # Computed properties
    processing_time_seconds: float
    c2pa_info: Dict[str, Any]
    is_ai_generated: bool

    class Config:
        from_attributes = True

    @validator('processing_time', pre=True)
    def parse_processing_time(cls, v):
        """Convert string to float"""
        if isinstance(v, str) and v:
            return float(v)
        return v or 0.0

    @validator('c2pa_manifest', 'generation_settings', 'animation_info', 'frame_timings',
               'loop_info', 'quality_scores', 'consistency_metrics', 'optimization_info',
               'export_settings', 'file_info', 'compression_info', 'platform_info', pre=True)
    def parse_json_fields(cls, v):
        """Parse JSON string to dict/list"""
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v


class C2PAMetadata(BaseModel):
    """Schema específico para metadados C2PA"""
    generator: str = "GPT-4o Images"
    created_with: str = "Sora Pixel Art Generator"
    provenance: str = "AI Generated Content"
    model_version: Optional[str] = None
    timestamp: datetime
    manifest_signature: Optional[str] = None
    claim_signature: Optional[str] = None

    # Additional C2PA fields
    assertion_store: Optional[Dict[str, Any]] = None
    ingredient_list: Optional[List[Dict[str, Any]]] = None
    hard_bindings: Optional[List[str]] = None
    soft_bindings: Optional[List[str]] = None


class AnimationMetadata(BaseModel):
    """Schema para metadados de animação"""
    frame_count: int = Field(..., ge=1, le=32)
    fps: int = Field(..., ge=1, le=60)
    total_duration_ms: int
    loop: bool = True

    # Frame timing details
    frame_durations: List[int]  # ms por frame
    frame_offsets: List[int]  # offset acumulado

    # Animation properties
    animation_type: str
    motion_intensity: float = Field(..., ge=0.0, le=1.0)
    smoothness_score: float = Field(..., ge=0.0, le=1.0)

    # Transition analysis
    transition_quality: List[float]  # qualidade entre frames consecutivos
    motion_vectors: Optional[List[Dict[str, float]]] = None


class QualityMetadata(BaseModel):
    """Schema para metadados de qualidade"""
    overall_score: float = Field(..., ge=0.0, le=1.0)

    # Individual metrics
    sharpness: float = Field(..., ge=0.0, le=1.0)
    consistency: float = Field(..., ge=0.0, le=1.0)
    motion_quality: float = Field(..., ge=0.0, le=1.0)
    color_harmony: float = Field(..., ge=0.0, le=1.0)

    # Technical metrics
    compression_efficiency: float = Field(..., ge=0.0, le=1.0)
    pixel_perfect_score: float = Field(..., ge=0.0, le=1.0)
    edge_definition: float = Field(..., ge=0.0, le=1.0)

    # Analysis details
    noise_level: float = Field(..., ge=0.0, le=1.0)
    artifact_count: int = Field(..., ge=0)
    color_bleeding: float = Field(..., ge=0.0, le=1.0)

    # Recommendations
    quality_issues: List[str] = []
    optimization_suggestions: List[str] = []


class ProcessingMetadata(BaseModel):
    """Schema para metadados de processamento"""
    processing_time_ms: int
    memory_usage_mb: float
    cpu_usage_percent: float

    # Processing steps
    steps_completed: List[str]
    step_timings: Dict[str, int]  # ms por step

    # Resource usage
    peak_memory_mb: float
    total_cpu_time_ms: int
    io_operations: int

    # GPT-4o specific
    api_calls_made: int
    tokens_used: Optional[int] = None
    rate_limit_hits: int = 0

    # Error tracking
    warnings_generated: List[str] = []
    errors_recovered: List[str] = []
    retry_attempts: int = 0


class ExportMetadata(BaseModel):
    """Schema para metadados de exportação"""
    export_format: str
    export_type: str  # sprite_sheet, individual_frames, etc.

    # File information
    original_size_bytes: int
    compressed_size_bytes: int
    compression_ratio: float

    # Export settings used
    settings_applied: Dict[str, Any]
    optimizations_applied: List[str]

    # Quality preservation
    quality_retained: float = Field(..., ge=0.0, le=1.0)
    data_loss_percent: float = Field(..., ge=0.0, le=100.0)

    # Performance metrics
    export_time_ms: int
    export_throughput_mbps: float


class MetadataBundle(BaseModel):
    """Schema para bundle completo de metadados"""
    job_id: UUID

    # Different metadata types
    c2pa: Optional[C2PAMetadata] = None
    animation: Optional[AnimationMetadata] = None
    quality: Optional[QualityMetadata] = None
    processing: Optional[ProcessingMetadata] = None
    export: Optional[ExportMetadata] = None

    # Summary
    created_at: datetime
    bundle_version: str = "1.0"
    checksum: Optional[str] = None


class MetadataExportRequest(BaseModel):
    """Schema para solicitação de export de metadados"""
    job_id: UUID
    include_types: List[MetadataType] = Field(default_factory=lambda: list(MetadataType))
    format: str = Field(default="json", regex="^(json|xml|yaml)$")
    include_c2pa_manifest: bool = True
    include_technical_details: bool = True


class MetadataImportRequest(BaseModel):
    """Schema para importação de metadados"""
    job_id: UUID
    metadata_file: str  # path ou content
    format: str = Field(..., regex="^(json|xml|yaml)$")
    overwrite_existing: bool = False
    validate_signatures: bool = True


class MetadataSearchRequest(BaseModel):
    """Schema para busca de metadados"""
    job_ids: Optional[List[UUID]] = None
    metadata_types: Optional[List[MetadataType]] = None

    # Search filters
    generator: Optional[str] = None
    model_version: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None

    # Quality filters
    min_quality_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    max_processing_time: Optional[int] = None  # ms

    # C2PA filters
    has_c2pa: Optional[bool] = None
    provenance: Optional[str] = None