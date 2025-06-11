"""
Generation Model - Configurações de geração
===========================================
"""

import uuid
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base

if TYPE_CHECKING:
    from .job import Job
    from .upload import Upload


class GenerationType(str, Enum):
    """Tipos de geração suportados"""
    PROMPT = "prompt"
    IMAGE = "image"


class AnimationType(str, Enum):
    """Tipos de animação pré-definidos"""
    WALK_CYCLE = "walk_cycle"
    IDLE = "idle"
    ATTACK = "attack"
    JUMP = "jump"
    RUN = "run"
    CUSTOM = "custom"


class StylePreset(str, Enum):
    """Presets de estilo"""
    RETRO_8BIT = "8-bit"
    RETRO_16BIT = "16-bit"
    PIXEL_ART_MODERN = "modern_pixel"
    GAMEBOY = "gameboy"
    NES = "nes"
    CUSTOM = "custom"


class Generation(Base):
    __tablename__ = "generations"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Job relationship
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)

    # Generation Type
    generation_type = Column(String(20), nullable=False)  # prompt|image

    # Input Data
    prompt = Column(Text, nullable=True)
    negative_prompt = Column(Text, nullable=True)
    upload_id = Column(UUID(as_uuid=True), ForeignKey("uploads.id"), nullable=True)

    # Style Configuration
    style = Column(String(50), default="8-bit")
    style_strength = Column(Integer, default=75)  # 0-100

    # Animation Configuration
    animation_type = Column(String(30), default="walk_cycle")
    frames = Column(Integer, default=8)
    fps = Column(Integer, default=12)
    loop = Column(Boolean, default=True)

    # Frame Configuration
    frame_width = Column(Integer, default=64)
    frame_height = Column(Integer, default=64)

    # Background
    background_type = Column(String(20), default="transparent")  # transparent|color|pattern
    background_color = Column(String(7), nullable=True)  # hex color

    # GPT-4o Specific Settings
    model_version = Column(String(20), default="gpt-4o")
    seed = Column(Integer, nullable=True)
    guidance_scale = Column(Integer, default=7)

    # Advanced Settings
    pixel_perfect = Column(Boolean, default=True)
    anti_aliasing = Column(Boolean, default=False)
    color_palette_limit = Column(Integer, nullable=True)  # limitação de cores

    # Processing Hints
    motion_intensity = Column(Integer, default=50)  # 0-100
    frame_consistency = Column(Integer, default=80)  # 0-100
    detail_level = Column(Integer, default=70)  # 0-100

    # Relationships
    job = relationship("Job", back_populates="generation")
    upload = relationship("Upload", back_populates="generations")

    def __repr__(self):
        return f"<Generation(id={self.id}, type={self.generation_type}, frames={self.frames})>"

    @property
    def frame_size(self) -> dict:
        """Retorna tamanho do frame como dict"""
        return {"width": self.frame_width, "height": self.frame_height}

    @property
    def total_duration_ms(self) -> int:
        """Duração total da animação em milissegundos"""
        return int((self.frames / self.fps) * 1000)

    @property
    def frame_duration_ms(self) -> int:
        """Duração de cada frame em milissegundos"""
        return int(1000 / self.fps)