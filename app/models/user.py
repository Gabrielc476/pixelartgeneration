"""
User Model - Sistema de usuários
===============================
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base

if TYPE_CHECKING:
    from .job import Job


class User(Base):
    __tablename__ = "users"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Basic Info
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=True)  # Nullable para auth opcional

    # Profile
    display_name = Column(String(100), nullable=True)
    avatar_url = Column(Text, nullable=True)

    # Preferences
    preferred_style = Column(String(50), default="8-bit")
    default_frame_count = Column(String(10), default="8")
    default_frame_size = Column(String(20), default="64x64")

    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_premium = Column(Boolean, default=False)

    # Usage Limits
    daily_generations = Column(String(10), default="0")
    max_daily_generations = Column(String(10), default="10")
    total_generations = Column(String(20), default="0")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    jobs = relationship("Job", back_populates="user", cascade="all, delete-orphan")
    uploads = relationship("Upload", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"

    @property
    def can_generate(self) -> bool:
        """Verifica se o usuário pode fazer novas gerações"""
        if self.is_premium:
            return True
        return int(self.daily_generations) < int(self.max_daily_generations)