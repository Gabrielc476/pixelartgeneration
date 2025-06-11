"""
Generation Schemas - Validação de dados de geração
==================================================
"""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator


class GenerationBase(BaseModel):
    """Base schema para Generation"""
    generation_type: str = Field(..., regex="^(prompt|image)$")
    prompt: Optional[str] = Field(None, max_length=2000)
    negative_prompt: Optional[str] = Field(None, max_length=1000)

    # Style
    style: str = Field(default="8-bit", max_length=100)
    style_strength: int = Field(default=75, ge=0, le=100)

    # Animation
    animation_type: str = Field(default="walk_cycle", max_length=50)
    frames: int = Field(default=8, ge=1, le=32)
    fps: int = Field(default=12, ge=1, le=60)
    loop: bool = True

    # Frame size
    frame_width: int = Field(default=64, ge=16, le=512)
    frame_height: int = Field(default=64, ge=16, le=512)

    # Background
    background_type: str = Field(default="transparent", regex="^(transparent|color|pattern)$")
    background_color: Optional[str] = Field(None, regex="^#[0-9A-Fa-f]{6}$")


class GenerationCreate(GenerationBase):
    """Schema para criação de geração"""
    upload_id: Optional[UUID] = None

    # GPT-4o settings
    model_version: str = Field(default="gpt-4o")
    seed: Optional[int] = Field(None, ge=0, le=2147483647)
    guidance_scale: int = Field(default=7, ge=1, le=20)

    # Advanced settings
    pixel_perfect: bool = True
    anti_aliasing: bool = False
    color_palette_limit: Optional[int] = Field(None, ge=2, le=256)

    # Processing hints
    motion_intensity: int = Field(default=50, ge=0, le=100)
    frame_consistency: int = Field(default=80, ge=0, le=100)
    detail_level: int = Field(default=70, ge=0, le=100)

    @validator('prompt')
    def validate_prompt_for_type(cls, v, values):
        """Valida prompt baseado no tipo"""
        generation_type = values.get('generation_type')
        if generation_type == 'prompt' and not v:
            raise ValueError('Prompt is required for prompt-based generation')
        return v

    @validator('background_color')
    def validate_background_color(cls, v, values):
        """Valida cor de fundo baseada no tipo"""
        background_type = values.get('background_type')
        if background_type == 'color' and not v:
            raise ValueError('Background color is required when background_type is color')
        return v


class GenerationResponse(GenerationBase):
    """Schema para resposta de geração"""
    id: UUID
    job_id: UUID
    upload_id: Optional[UUID] = None

    # GPT-4o settings
    model_version: str
    seed: Optional[int] = None
    guidance_scale: int

    # Advanced settings
    pixel_perfect: bool
    anti_aliasing: bool
    color_palette_limit: Optional[int] = None

    # Processing hints
    motion_intensity: int
    frame_consistency: int
    detail_level: int

    # Computed properties
    frame_size: dict
    total_duration_ms: int
    frame_duration_ms: int

    class Config:
        from_attributes = True


class GenerationSettings(BaseModel):
    """Schema para configurações de geração"""
    style_presets: list[str] = [
        "8-bit", "16-bit", "gameboy", "nes", "modern_pixel", "custom"
    ]
    animation_types: list[str] = [
        "walk_cycle", "idle", "attack", "jump", "run", "custom"
    ]
    frame_sizes: list[str] = [
        "16x16", "32x32", "64x64", "128x128", "256x256"
    ]
    background_types: list[str] = [
        "transparent", "color", "pattern"
    ]
    max_frames: int = 32
    max_frame_size: int = 512
    min_frame_size: int = 16


class GenerationValidation(BaseModel):
    """Schema para validação de parâmetros"""
    is_valid: bool
    errors: list[str] = []
    warnings: list[str] = []
    estimated_time: Optional[int] = None  # segundos
    estimated_cost: Optional[float] = None  # para futuro sistema de billing


class PromptSuggestion(BaseModel):
    """Schema para sugestões de prompt"""
    original_prompt: str
    suggested_prompt: str
    improvements: list[str]
    style_suggestions: list[str]
    animation_suggestions: list[str]


class GenerationPreview(BaseModel):
    """Schema para preview de geração"""
    prompt: str
    style: str
    frames: int
    frame_size: dict
    estimated_time: int
    estimated_frames_preview: list[str]  # URLs de preview
    similar_examples: list[str]  # URLs de exemplos similares