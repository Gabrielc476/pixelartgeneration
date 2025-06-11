"""
Export Model - Exportações de arquivos
======================================
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base

if TYPE_CHECKING:
    from .job import Job


class ExportFormat(str, Enum):
    """Formatos de exportação suportados"""
    PNG = "png"
    ASE = "ase"  # Aseprite
    GIF = "gif"
    ZIP = "zip"
    JSON = "json"  # Metadata


class ExportStatus(str, Enum):
    """Status da exportação"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class Export(Base):
    __tablename__ = "exports"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Job relationship
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)

    # Export Configuration
    format = Column(String(20), nullable=False)
    export_type = Column(String(30), nullable=False)  # sprite_sheet, individual_frames, preview, metadata

    # File Information
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)  # bytes

    # Export Settings (JSON as Text)
    settings = Column(Text, nullable=True)  # JSON com configurações específicas

    # Status
    status = Column(String(20), default="pending")
    progress = Column(Integer, default=0)  # 0-100

    # Download Information
    download_url = Column(String(500), nullable=True)
    download_count = Column(Integer, default=0)
    max_downloads = Column(Integer, default=100)

    # Error Handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    last_downloaded = Column(DateTime, nullable=True)

    # Relationships
    job = relationship("Job", back_populates="exports")

    def __repr__(self):
        return f"<Export(id={self.id}, format={self.format}, status={self.status})>"

    @property
    def file_size_mb(self) -> float:
        """Tamanho em MB"""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0.0

    @property
    def is_expired(self) -> bool:
        """Verifica se o export expirou"""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False

    @property
    def can_download(self) -> bool:
        """Verifica se ainda pode ser baixado"""
        return (
                self.status == "completed" and
                not self.is_expired and
                self.download_count < self.max_downloads
        )

    @property
    def remaining_downloads(self) -> int:
        """Downloads restantes"""
        return max(0, self.max_downloads - self.download_count)

    def increment_download(self):
        """Incrementa contador de downloads"""
        self.download_count += 1
        self.last_downloaded = datetime.utcnow()