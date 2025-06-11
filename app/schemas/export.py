# ============================================================================
# 📄 app/schemas/export.py
# ============================================================================

"""
Export Schemas - Validação de dados de exportação
=================================================
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.export import ExportFormat, ExportStatus


class ExportBase(BaseModel):
    """Base schema para Export"""
    format: ExportFormat = Field(..., description="Formato de exportação")
    export_type: str = Field(..., pattern="^(sprite_sheet|individual_frames|preview|metadata)$")


class ExportCreate(ExportBase):
    """Schema para criação de export"""
    settings: Optional[dict] = Field(default_factory=dict)
    max_downloads: int = Field(default=100, ge=1, le=1000)


class ExportResponse(ExportBase):
    """Schema para resposta de export"""
    id: UUID
    job_id: UUID

    # File information
    filename: str
    file_path: str
    file_size: Optional[int] = None

    # Settings
    settings: dict

    # Status
    status: ExportStatus
    progress: int

    # Download information
    download_url: Optional[str] = None
    download_count: int
    max_downloads: int
    remaining_downloads: int

    # Error handling
    error_message: Optional[str] = None
    retry_count: int

    # Timestamps
    created_at: datetime
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    last_downloaded: Optional[datetime] = None

    # Computed properties
    file_size_mb: float
    is_expired: bool
    can_download: bool

    class Config:
        from_attributes = True


class ExportListResponse(BaseModel):
    """Schema para listagem de exports"""
    exports: List[ExportResponse]
    total: int
    by_format: dict
    by_status: dict