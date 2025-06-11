"""
Job Schemas - Validação de dados de trabalhos
=============================================
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator

from app.models.job import JobStatus, OutputFormat


class JobBase(BaseModel):
    """Base schema para Job"""
    output_format: OutputFormat = Field(..., description="Formato de output: sprite_sheet ou individual_frames")


class JobCreate(JobBase):
    """Schema para criação de job"""
    # Output format é obrigatório
    pass


class JobUpdate(BaseModel):
    """Schema para atualização de job"""
    status: Optional[JobStatus] = None
    progress: Optional[int] = Field(None, ge=0, le=100)
    current_step: Optional[str] = None
    estimated_time: Optional[int] = Field(None, ge=0)
    error_message: Optional[str] = None
    error_code: Optional[str] = None


class JobResponse(JobBase):
    """Schema para resposta de job"""
    id: UUID
    user_id: Optional[UUID] = None
    status: JobStatus
    progress: int
    current_step: Optional[str] = None

    # Timing
    estimated_time: Optional[int] = None
    actual_time: Optional[int] = None
    retry_count: int

    # Error handling
    error_message: Optional[str] = None
    error_code: Optional[str] = None

    # File paths
    working_directory: Optional[str] = None
    preview_gif_path: Optional[str] = None
    thumbnail_path: Optional[str] = None

    # URLs for frontend
    preview_gif_url: Optional[str] = None
    thumbnail_url: Optional[str] = None

    # Timestamps
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    # Computed properties
    is_processing: bool
    is_finished: bool
    can_retry: bool

    class Config:
        from_attributes = True


class JobDetailResponse(JobResponse):
    """Schema detalhado para job com relacionamentos"""
    from .generation import GenerationResponse
    from .sprite_sheet import SpriteSheetResponse
    from .frame import FrameResponse
    from .export import ExportResponse

    generation: Optional[GenerationResponse] = None
    sprite_sheet: Optional[SpriteSheetResponse] = None
    frames: List[FrameResponse] = []
    exports: List[ExportResponse] = []


class JobListResponse(BaseModel):
    """Schema para listagem de jobs"""
    jobs: List[JobResponse]
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool


class JobStats(BaseModel):
    """Schema para estatísticas de jobs"""
    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    processing_jobs: int
    avg_processing_time: float
    sprite_sheet_jobs: int
    individual_frames_jobs: int


class JobProgressUpdate(BaseModel):
    """Schema para atualizações de progresso"""
    job_id: UUID
    status: JobStatus
    progress: int
    current_step: str
    estimated_time_remaining: Optional[int] = None
    message: Optional[str] = None


class JobStatusFilter(BaseModel):
    """Schema para filtros de status"""
    status: Optional[List[JobStatus]] = None
    output_format: Optional[List[OutputFormat]] = None
    user_id: Optional[UUID] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None


class JobCreateRequest(BaseModel):
    """Schema completo para criação de job via API"""
    # Generation data embedded
    generation_type: str = Field(..., regex="^(prompt|image)$")
    prompt: Optional[str] = Field(None, max_length=2000)
    upload_id: Optional[UUID] = None

    # Output format
    output_format: OutputFormat = Field(..., description="sprite_sheet ou individual_frames")

    # Style settings
    style: str = Field(default="8-bit", max_length=100)
    style_strength: int = Field(default=75, ge=0, le=100)

    # Animation settings
    animation_type: str = Field(default="walk_cycle", max_length=50)
    frames: int = Field(default=8, ge=1, le=32)
    fps: int = Field(default=12, ge=1, le=60)
    loop: bool = True

    # Frame settings
    frame_width: int = Field(default=64, ge=16, le=512)
    frame_height: int = Field(default=64, ge=16, le=512)

    # Background
    background_type: str = Field(default="transparent", regex="^(transparent|color|pattern)$")
    background_color: Optional[str] = Field(None, regex="^#[0-9A-Fa-f]{6}$")

    # Advanced settings
    pixel_perfect: bool = True
    motion_intensity: int = Field(default=50, ge=0, le=100)

    @validator('prompt')
    def validate_prompt_or_upload(cls, v, values):
        """Valida que prompt ou upload_id estão presentes"""
        generation_type = values.get('generation_type')
        upload_id = values.get('upload_id')

        if generation_type == 'prompt' and not v:
            raise ValueError('Prompt is required for prompt-based generation')
        if generation_type == 'image' and not upload_id:
            raise ValueError('Upload ID is required for image-based generation')

        return v