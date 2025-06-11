"""
Metadata Model - Metadados C2PA e de animação
=============================================
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base

if TYPE_CHECKING:
    from .job import Job


class MetadataType(str, Enum):
    """Tipos de metadata"""
    C2PA = "c2pa"
    ANIMATION = "animation"
    PROCESSING = "processing"
    EXPORT = "export"
    QUALITY = "quality"


class Metadata(Base):
    __tablename__ = "metadata"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Job relationship
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)

    # Metadata Type and Target
    metadata_type = Column(String(20), nullable=False)
    target_entity = Column(String(50), nullable=False)  # job, sprite_sheet, frame, export
    target_id = Column(UUID(as_uuid=True), nullable=True)

    # Content Authenticity (C2PA)
    c2pa_manifest = Column(Text, nullable=True)  # JSON com manifest C2PA
    generator = Column(String(50), default="GPT-4o Images")
    created_with = Column(String(100), default="Sora Pixel Art Generator")
    provenance = Column(String(100), default="AI Generated Content")
    model_version = Column(String(30), nullable=True)

    # Generation Metadata
    generation_prompt = Column(Text, nullable=True)
    generation_settings = Column(Text, nullable=True)  # JSON
    seed_used = Column(String(50), nullable=True)
    processing_time = Column(String(20), nullable=True)  # em segundos como string

    # Animation Metadata
    animation_info = Column(Text, nullable=True)  # JSON com info da animação
    frame_timings = Column(Text, nullable=True)  # JSON array com timings
    loop_info = Column(Text, nullable=True)  # JSON com configurações de loop

    # Quality Metrics
    quality_scores = Column(Text, nullable=True)  # JSON com scores de qualidade
    consistency_metrics = Column(Text, nullable=True)  # JSON com métricas
    optimization_info = Column(Text, nullable=True)  # JSON com info de otimização

    # Export Metadata
    export_settings = Column(Text, nullable=True)  # JSON com configurações de export
    file_info = Column(Text, nullable=True)  # JSON com informações de arquivo
    compression_info = Column(Text, nullable=True)  # JSON com info de compressão

    # Technical Information
    software_version = Column(String(20), default="1.0.0")
    api_version = Column(String(20), nullable=True)
    platform_info = Column(Text, nullable=True)  # JSON com info da plataforma

    # Compliance and Legal
    copyright_info = Column(Text, nullable=True)
    license_info = Column(String(100), nullable=True)
    usage_rights = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    job = relationship("Job")

    def __repr__(self):
        return f"<Metadata(id={self.id}, type={self.metadata_type}, target={self.target_entity})>"

    @property
    def processing_time_seconds(self) -> float:
        """Tempo de processamento em segundos"""
        if self.processing_time:
            return float(self.processing_time)
        return 0.0

    @property
    def c2pa_info(self) -> dict:
        """Informações C2PA formatadas"""
        return {
            "generator": self.generator,
            "created_with": self.created_with,
            "provenance": self.provenance,
            "model_version": self.model_version,
            "timestamp": self.created_at.isoformat() if self.created_at else None
        }

    @property
    def is_ai_generated(self) -> bool:
        """Verifica se é conteúdo gerado por IA"""
        return "AI Generated" in (self.provenance or "")

    def get_metadata_json(self) -> dict:
        """Retorna todos os metadados como JSON"""
        return {
            "type": self.metadata_type,
            "target": {
                "entity": self.target_entity,
                "id": str(self.target_id) if self.target_id else None
            },
            "c2pa": self.c2pa_info,
            "generation": {
                "prompt": self.generation_prompt,
                "seed": self.seed_used,
                "processing_time": self.processing_time_seconds
            },
            "created_at": self.created_at.isoformat() if self.created_at else None
        }