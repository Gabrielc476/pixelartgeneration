# ============================================================================
# 📄 app/schemas/metadata.py
# ============================================================================

"""
Metadata Schemas - Validação de dados de metadados
==================================================
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.metadata import MetadataType


class MetadataBase(BaseModel):
    """Base schema para Metadata"""
    metadata_type: MetadataType
    target_entity: str = Field(..., pattern="^(job|sprite_sheet|frame|export)$")
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

    @field_validator('processing_time', mode='before')
    @classmethod
    def parse_processing_time(cls, v):
        """Convert string to float"""
        if isinstance(v, str) and v:
            return float(v)
        return v or 0.0