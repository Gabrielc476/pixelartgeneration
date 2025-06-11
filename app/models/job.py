"""
Job Model - Núcleo do sistema de geração
========================================
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base

if TYPE_CHECKING:
    from .user import User
    from .generation import Generation
    from .sprite_sheet import SpriteSheet
    from .frame import Frame
    from .export import Export


class JobStatus(str, Enum):
    """Estados possíveis de um job"""
    CREATED = "created"
    PROCESSING = "processing"
    GENERATING = "generating"
    POST_PROCESSING = "post_processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OutputFormat(str, Enum):
    """Formatos de output suportados"""
    SPRITE_SHEET = "sprite_sheet"
    INDIVIDUAL_FRAMES = "individual_frames"


class Job(Base):
    __tablename__ = "jobs"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # User relationship
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Status and Progress
    status = Column(SQLEnum(JobStatus), default=JobStatus.CREATED, nullable=False)
    progress = Column(Integer, default=0)  # 0-100
    current_step = Column(String(100), nullable=True)

    # Output Configuration
    output_format = Column(SQLEnum(OutputFormat), nullable=False)

    # Processing Info
    estimated_time = Column(Integer, nullable=True)  # segundos
    actual_time = Column(Integer, nullable=True)  # segundos
    retry_count = Column(Integer, default=0)

    # Error Handling
    error_message = Column(Text, nullable=True)
    error_code = Column(String(50), nullable=True)

    # File Paths
    working_directory = Column(String(500), nullable=True)
    preview_gif_path = Column(String(500), nullable=True)
    thumbnail_path = Column(String(500), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="jobs")
    generation = relationship("Generation", back_populates="job", uselist=False, cascade="all, delete-orphan")
    sprite_sheet = relationship("SpriteSheet", back_populates="job", uselist=False, cascade="all, delete-orphan")
    frames = relationship("Frame", back_populates="job", cascade="all, delete-orphan")
    exports = relationship("Export", back_populates="job", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Job(id={self.id}, status={self.status}, output_format={self.output_format})>"

    @property
    def is_processing(self) -> bool:
        """Verifica se o job está em processamento"""
        return self.status in [JobStatus.PROCESSING, JobStatus.GENERATING, JobStatus.POST_PROCESSING]

    @property
    def is_finished(self) -> bool:
        """Verifica se o job terminou (sucesso ou erro)"""
        return self.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]

    def can_retry(self) -> bool:
        """Verifica se o job pode ser retentado"""
        return self.status == JobStatus.FAILED and self.retry_count < 3