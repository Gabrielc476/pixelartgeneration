"""
Frame Model - Frames individuais
================================
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base

if TYPE_CHECKING:
    from .job import Job


class Frame(Base):
    __tablename__ = "frames"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Job relationship
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)

    # Frame Information
    frame_number = Column(Integer, nullable=False)  # 1, 2, 3...
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)  # bytes

    # Frame Properties
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    duration = Column(Integer, default=100)  # ms

    # Animation Properties
    timing_offset = Column(Integer, default=0)  # ms desde início
    delay_after = Column(Integer, default=0)  # ms de delay adicional

    # Visual Properties
    format = Column(String(10), default="PNG")
    has_transparency = Column(String(10), default="true")
    color_count = Column(Integer, nullable=True)

    # Processing Information
    generated_prompt = Column(Text, nullable=True)  # prompt específico usado
    generation_seed = Column(Integer, nullable=True)
    processing_time = Column(Integer, nullable=True)  # ms

    # Quality Metrics
    sharpness_score = Column(String(10), nullable=True)  # 0.0-1.0 as string
    consistency_score = Column(String(10), nullable=True)  # 0.0-1.0 as string
    motion_score = Column(String(10), nullable=True)  # 0.0-1.0 as string

    # Optimization
    is_optimized = Column(String(10), default="false")
    original_size = Column(Integer, nullable=True)
    compression_ratio = Column(String(10), nullable=True)

    # Metadata
    c2pa_embedded = Column(String(10), default="true")
    generated_with = Column(String(50), default="GPT-4o")
    gpt4o_image_id = Column(String(255), nullable=True)  # ID da OpenAI

    # Relationships
    job = relationship("Job", back_populates="frames")

    def __repr__(self):
        return f"<Frame(id={self.id}, frame_number={self.frame_number}, filename={self.filename})>"

    @property
    def file_size_kb(self) -> float:
        """Tamanho em KB"""
        return round(self.file_size / 1024, 2)

    @property
    def resolution_string(self) -> str:
        """Resolução formatada"""
        return f"{self.width}x{self.height}"

    @property
    def duration_seconds(self) -> float:
        """Duração em segundos"""
        return self.duration / 1000.0

    @property
    def timing_offset_seconds(self) -> float:
        """Offset de timing em segundos"""
        return self.timing_offset / 1000.0

    @property
    def formatted_filename(self) -> str:
        """Nome formatado com zero-padding"""
        return f"frame_{self.frame_number:03d}.png"

    @property
    def quality_metrics(self) -> dict:
        """Métricas de qualidade"""
        return {
            "sharpness": float(self.sharpness_score) if self.sharpness_score else None,
            "consistency": float(self.consistency_score) if self.consistency_score else None,
            "motion": float(self.motion_score) if self.motion_score else None
        }