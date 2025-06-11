"""
Preset Model - Presets de estilo e animação
===========================================
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class PresetType(str, Enum):
    """Tipos de preset"""
    STYLE = "style"
    ANIMATION = "animation"
    FRAME_SIZE = "frame_size"
    COMBINED = "combined"


class PresetCategory(str, Enum):
    """Categorias de preset"""
    RETRO = "retro"
    MODERN = "modern"
    GAMEBOY = "gameboy"
    ARCADE = "arcade"
    RPG = "rpg"
    PLATFORMER = "platformer"
    CUSTOM = "custom"


class Preset(Base):
    __tablename__ = "presets"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Basic Information
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    preset_type = Column(String(20), nullable=False)
    category = Column(String(30), default="custom")

    # Configuration (JSON as Text)
    configuration = Column(Text, nullable=False)  # JSON com todas as configurações

    # Display
    thumbnail_path = Column(String(500), nullable=True)
    icon = Column(String(50), nullable=True)  # emoji ou nome do ícone
    color = Column(String(7), nullable=True)  # cor hex para display

    # System Presets vs User Presets
    is_system = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    # Usage Statistics
    usage_count = Column(Integer, default=0)
    rating = Column(String(10), default="0.0")  # 0.0-5.0 as string
    rating_count = Column(Integer, default=0)

    # Versioning
    version = Column(String(20), default="1.0")
    parent_preset_id = Column(UUID(as_uuid=True), nullable=True)

    # Metadata
    tags = Column(Text, nullable=True)  # JSON array de tags
    recommended_for = Column(Text, nullable=True)  # JSON array de use cases

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Preset(id={self.id}, name={self.name}, type={self.preset_type})>"

    @property
    def rating_float(self) -> float:
        """Rating como float"""
        return float(self.rating) if self.rating else 0.0

    @property
    def display_name(self) -> str:
        """Nome para exibição com ícone"""
        if self.icon:
            return f"{self.icon} {self.name}"
        return self.name

    def increment_usage(self):
        """Incrementa contador de uso"""
        self.usage_count += 1

    def add_rating(self, new_rating: float):
        """Adiciona uma nova avaliação"""
        current_total = self.rating_float * self.rating_count
        self.rating_count += 1
        new_average = (current_total + new_rating) / self.rating_count
        self.rating = str(round(new_average, 1))