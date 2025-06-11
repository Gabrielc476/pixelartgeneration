"""
SpriteSheet Model - Sprite sheets gerados
==========================================
"""

import uuid
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base

if TYPE_CHECKING:
    from .job import Job


class LayoutType(str, Enum):
    """Tipos de layout do sprite sheet"""
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    GRID = "grid"
    PACKED = "packed"


class SpriteSheet(Base):
    __tablename__ = "sprite_sheets"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Job relationship
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)

    # File Information
    file_path = Column(String(500), nullable=False)
    filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)  # bytes

    # Sprite Sheet Properties
    sheet_width = Column(Integer, nullable=False)
    sheet_height = Column(Integer, nullable=False)
    frame_count = Column(Integer, nullable=False)

    # Layout Configuration
    layout_type = Column(String(20), default="horizontal")
    columns = Column(Integer, nullable=True)
    rows = Column(Integer, nullable=True)
    spacing = Column(Integer, default=0)
    padding = Column(Integer, default=0)

    # Frame Properties
    frame_width = Column(Integer, nullable=False)
    frame_height = Column(Integer, nullable=False)

    # Animation Properties
    fps = Column(Integer, default=12)
    loop = Column(String(10), default="true")
    total_duration = Column(Integer, nullable=False)  # ms

    # File Format
    format = Column(String(10), default="PNG")
    has_transparency = Column(String(10), default="true")
    color_depth = Column(Integer, default=32)

    # Optimization
    is_optimized = Column(String(10), default="false")
    original_size = Column(Integer, nullable=True)
    compression_ratio = Column(String(10), nullable=True)  # as string for precision

    # Frame Mapping (JSON string)
    frame_positions = Column(Text, nullable=True)  # JSON array com posições x,y

    # Metadata
    c2pa_embedded = Column(String(10), default="true")
    generated_with = Column(String(50), default="GPT-4o")

    # Relationships
    job = relationship("Job", back_populates="sprite_sheet")

    def __repr__(self):
        return f"<SpriteSheet(id={self.id}, frames={self.frame_count}, layout={self.layout_type})>"

    @property
    def file_size_mb(self) -> float:
        """Tamanho em MB"""
        return round(self.file_size / (1024 * 1024), 2)

    @property
    def resolution_string(self) -> str:
        """Resolução formatada"""
        return f"{self.sheet_width}x{self.sheet_height}"

    @property
    def frame_size_string(self) -> str:
        """Tamanho do frame formatado"""
        return f"{self.frame_width}x{self.frame_height}"

    @property
    def duration_seconds(self) -> float:
        """Duração em segundos"""
        return self.total_duration / 1000.0

    @property
    def layout_info(self) -> dict:
        """Informações do layout"""
        return {
            "type": self.layout_type,
            "columns": self.columns,
            "rows": self.rows,
            "spacing": self.spacing,
            "padding": self.padding
        }