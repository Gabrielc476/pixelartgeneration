"""
Export Schemas - Validação de dados de exportação
=================================================
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator

from app.models.export import ExportFormat, ExportStatus


class ExportBase(BaseModel):
    """Base schema para Export"""
    format: ExportFormat = Field(..., description="Formato de exportação")
    export_type: str = Field(..., regex="^(sprite_sheet|individual_frames|preview|metadata)$")


class ExportCreate(ExportBase):
    """Schema para criação de export"""
    settings: Optional[dict] = Field(default_factory=dict)
    max_downloads: int = Field(default=100, ge=1, le=1000)

    @validator('settings')
    def validate_settings_by_format(cls, v, values):
        """Valida configurações baseadas no formato"""
        format_type = values.get('format')
        export_type = values.get('export_type')

        if format_type == ExportFormat.ASE:
            # Validações específicas para Aseprite
            if 'fps' in v and not (1 <= v['fps'] <= 60):
                raise ValueError('FPS must be between 1 and 60 for ASE format')

        elif format_type == ExportFormat.ZIP and export_type == 'individual_frames':
            # Validações para ZIP de frames
            if 'naming_pattern' in v and '{number' not in v['naming_pattern']:
                raise ValueError('Naming pattern must include {number} placeholder')

        return v


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


class ExportProgress(BaseModel):
    """Schema para progresso de exportação"""
    export_id: UUID
    status: ExportStatus
    progress: int
    current_step: str
    estimated_time_remaining: Optional[int] = None
    file_size_estimate: Optional[int] = None


class ExportDownload(BaseModel):
    """Schema para download de export"""
    export_id: UUID
    download_url: str
    filename: str
    file_size: int
    content_type: str
    expires_in: int  # seconds


class ExportSettings(BaseModel):
    """Schema para configurações gerais de export"""

    # PNG Settings
    png_compression: int = Field(default=6, ge=0, le=9)
    png_optimize: bool = True

    # ASE Settings
    ase_fps: int = Field(default=12, ge=1, le=60)
    ase_loop: bool = True
    ase_include_layers: bool = True

    # GIF Settings
    gif_fps: int = Field(default=12, ge=1, le=30)
    gif_loop: bool = True
    gif_optimize: bool = True
    gif_colors: int = Field(default=256, ge=2, le=256)

    # ZIP Settings
    zip_compression: int = Field(default=6, ge=0, le=9)
    zip_include_metadata: bool = True

    # General
    include_c2pa: bool = True
    quality_level: str = Field(default="high", regex="^(low|medium|high|lossless)$")


class SpriteSheetExportRequest(BaseModel):
    """Schema para solicitação de export de sprite sheet"""
    format: ExportFormat
    layout: str = Field(default="horizontal", regex="^(horizontal|vertical|grid)$")
    spacing: int = Field(default=0, ge=0, le=50)
    include_metadata: bool = True
    optimize: bool = True

    # ASE specific
    fps: Optional[int] = Field(None, ge=1, le=60)
    loop: Optional[bool] = None

    # PNG specific
    compression: Optional[int] = Field(None, ge=0, le=9)


class IndividualFramesExportRequest(BaseModel):
    """Schema para solicitação de export de frames individuais"""
    format: ExportFormat
    naming_pattern: str = Field(default="frame_{number:03d}.png")
    include_metadata: bool = True
    create_zip: bool = True
    optimize: bool = True

    # ASE specific (for importing sequence)
    fps: Optional[int] = Field(None, ge=1, le=60)
    auto_import_sequence: bool = True

    @validator('naming_pattern')
    def validate_naming_pattern(cls, v):
        """Valida padrão de nomenclatura"""
        if '{number' not in v:
            raise ValueError('Naming pattern must include {number} placeholder')
        return v


class ExportJob(BaseModel):
    """Schema para job de exportação"""
    job_id: UUID
    export_requests: List[ExportCreate]
    priority: str = Field(default="normal", regex="^(low|normal|high|urgent)$")
    notify_on_completion: bool = True


class ExportStats(BaseModel):
    """Schema para estatísticas de exports"""
    total_exports: int
    by_format: dict
    by_status: dict
    avg_file_size: dict  # por formato
    avg_processing_time: dict  # por formato
    download_stats: dict
    popular_settings: dict


class ExportBatch(BaseModel):
    """Schema para exportação em lote"""
    job_ids: List[UUID]
    format: ExportFormat
    export_type: str
    settings: dict = Field(default_factory=dict)

    @validator('job_ids')
    def validate_job_ids(cls, v):
        """Valida IDs dos jobs"""
        if not v:
            raise ValueError('At least one job ID is required')
        if len(v) > 50:
            raise ValueError('Maximum 50 jobs per batch')
        return list(set(v))  # Remove duplicates