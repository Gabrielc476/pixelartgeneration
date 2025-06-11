"""
Upload Model - Imagens de referência
====================================
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base

if TYPE_CHECKING:
    from .user import User
    from .generation import Generation


class Upload(Base):
    __tablename__ = "uploads"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # User relationship
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # File Information
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)  # bytes
    file_path = Column(String(500), nullable=False)

    # Image Analysis
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    format = Column(String(10), nullable=True)  # PNG, JPG, etc.

    # AI Analysis Results
    detected_style = Column(String(100), nullable=True)
    suggested_frames = Column(Integer, nullable=True)
    recommended_width = Column(Integer, nullable=True)
    recommended_height = Column(Integer, nullable=True)
    color_count = Column(Integer, nullable=True)
    has_transparency = Column(String(10), nullable=True)  # true/false as string
    dominant_colors = Column(Text, nullable=True)  # JSON array

    # Processing Status
    analysis_completed = Column(String(10), default="false")
    analysis_error = Column(Text, nullable=True)

    # Usage
    usage_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    analyzed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="uploads")
    generations = relationship("Generation", back_populates="upload")

    def __repr__(self):
        return f"<Upload(id={self.id}, filename={self.filename}, size={self.file_size})>"

    @property
    def file_size_mb(self) -> float:
        """Tamanho do arquivo em MB"""
        return round(self.file_size / (1024 * 1024), 2)

    @property
    def is_analyzed(self) -> bool:
        """Verifica se a análise foi concluída"""
        return self.analysis_completed == "true"

    @property
    def aspect_ratio(self) -> float:
        """Proporção da imagem"""
        if self.width and self.height:
            return round(self.width / self.height, 2)
        return 1.0

    @property
    def resolution_string(self) -> str:
        """String de resolução formatada"""
        if self.width and self.height:
            return f"{self.width}x{self.height}"
        return "Unknown"