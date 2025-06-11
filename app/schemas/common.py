"""
Common Schemas - Schemas compartilhados
======================================
"""

from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field
from pydantic.generics import GenericModel

# Type variable for generic responses
DataT = TypeVar('DataT')


class PaginationParams(BaseModel):
    """Schema para parâmetros de paginação"""
    page: int = Field(default=1, ge=1, description="Número da página")
    per_page: int = Field(default=20, ge=1, le=100, description="Itens por página")
    sort_by: Optional[str] = Field(None, description="Campo para ordenação")
    sort_order: str = Field(default="desc", regex="^(asc|desc)$", description="Ordem de classificação")


class PaginationMeta(BaseModel):
    """Schema para metadados de paginação"""
    page: int
    per_page: int
    total: int
    pages: int
    has_next: bool
    has_prev: bool
    next_page: Optional[int] = None
    prev_page: Optional[int] = None


class PaginatedResponse(GenericModel, Generic[DataT]):
    """Schema genérico para respostas paginadas"""
    data: List[DataT]
    meta: PaginationMeta


class APIResponse(GenericModel, Generic[DataT]):
    """Schema genérico para respostas da API"""
    success: bool = True
    message: Optional[str] = None
    data: Optional[DataT] = None
    errors: Optional[List[str]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Schema para respostas de erro"""
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SuccessResponse(BaseModel):
    """Schema para respostas de sucesso simples"""
    success: bool = True
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    """Schema para resposta de health check"""
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0.0"
    services: Dict[str, str] = Field(default_factory=dict)
    uptime: Optional[float] = None


class FileInfo(BaseModel):
    """Schema para informações de arquivo"""
    filename: str
    file_size: int
    content_type: str
    file_path: Optional[str] = None
    file_url: Optional[str] = None
    checksum: Optional[str] = None

    @property
    def file_size_mb(self) -> float:
        """Tamanho em MB"""
        return round(self.file_size / (1024 * 1024), 2)

    @property
    def file_size_kb(self) -> float:
        """Tamanho em KB"""
        return round(self.file_size / 1024, 2)


class ImageInfo(FileInfo):
    """Schema para informações de imagem"""
    width: int
    height: int
    format: str
    has_transparency: bool = False
    color_depth: Optional[int] = None

    @property
    def resolution_string(self) -> str:
        """Resolução formatada"""
        return f"{self.width}x{self.height}"

    @property
    def aspect_ratio(self) -> float:
        """Proporção da imagem"""
        return round(self.width / self.height, 2)


class FrameSize(BaseModel):
    """Schema para tamanho de frame"""
    width: int = Field(..., ge=16, le=512)
    height: int = Field(..., ge=16, le=512)

    def __str__(self) -> str:
        return f"{self.width}x{self.height}"

    @classmethod
    def from_string(cls, size_str: str) -> "FrameSize":
        """Cria FrameSize a partir de string 'WIDTHxHEIGHT'"""
        try:
            width, height = size_str.split('x')
            return cls(width=int(width), height=int(height))
        except (ValueError, AttributeError):
            raise ValueError("Frame size must be in format 'WIDTHxHEIGHT'")


class ColorInfo(BaseModel):
    """Schema para informações de cor"""
    hex: str = Field(..., regex="^#[0-9A-Fa-f]{6}$")
    rgb: tuple[int, int, int]
    name: Optional[str] = None

    @classmethod
    def from_hex(cls, hex_color: str, name: Optional[str] = None) -> "ColorInfo":
        """Cria ColorInfo a partir de cor hexadecimal"""
        hex_color = hex_color.strip('#')
        rgb = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
        return cls(hex=f"#{hex_color}", rgb=rgb, name=name)


class TimeRange(BaseModel):
    """Schema para intervalo de tempo"""
    start: datetime
    end: datetime

    @property
    def duration_seconds(self) -> float:
        """Duração em segundos"""
        return (self.end - self.start).total_seconds()

    def contains(self, timestamp: datetime) -> bool:
        """Verifica se timestamp está no intervalo"""
        return self.start <= timestamp <= self.end


class FilterParams(BaseModel):
    """Schema base para parâmetros de filtro"""
    search: Optional[str] = Field(None, max_length=100)
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    is_active: Optional[bool] = None


class SortParams(BaseModel):
    """Schema para parâmetros de ordenação"""
    sort_by: str = "created_at"
    sort_order: str = Field(default="desc", regex="^(asc|desc)$")

    def get_sort_expression(self, model_class) -> Any:
        """Retorna expressão de ordenação para SQLAlchemy"""
        from sqlalchemy import asc, desc

        field = getattr(model_class, self.sort_by, None)
        if not field:
            field = getattr(model_class, 'created_at')

        return desc(field) if self.sort_order == 'desc' else asc(field)


class StatsResponse(BaseModel):
    """Schema para respostas de estatísticas"""
    total_count: int
    period_start: datetime
    period_end: datetime
    breakdown: Dict[str, Any]
    trends: Optional[Dict[str, List[float]]] = None


class BatchRequest(BaseModel):
    """Schema para requisições em lote"""
    ids: List[UUID] = Field(..., min_items=1, max_items=100)
    operation: str
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)


class BatchResponse(BaseModel):
    """Schema para respostas de operações em lote"""
    total_requested: int
    successful: int
    failed: int
    results: List[Dict[str, Any]]
    errors: List[Dict[str, Any]] = []


class ValidationError(BaseModel):
    """Schema para erros de validação"""
    field: str
    message: str
    value: Optional[Any] = None


class ValidationResponse(BaseModel):
    """Schema para resposta de validação"""
    is_valid: bool
    errors: List[ValidationError] = []
    warnings: List[str] = []


class ProgressUpdate(BaseModel):
    """Schema para atualizações de progresso"""
    entity_id: UUID
    entity_type: str
    progress: int = Field(..., ge=0, le=100)
    status: str
    message: Optional[str] = None
    estimated_completion: Optional[datetime] = None


class NotificationEvent(BaseModel):
    """Schema para eventos de notificação"""
    event_type: str
    entity_id: UUID
    entity_type: str
    user_id: Optional[UUID] = None
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConfigurationUpdate(BaseModel):
    """Schema para atualizações de configuração"""
    section: str
    key: str
    value: Any
    previous_value: Optional[Any] = None
    updated_by: Optional[UUID] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SystemStatus(BaseModel):
    """Schema para status do sistema"""
    service: str
    status: str = Field(..., regex="^(healthy|degraded|unhealthy|maintenance)$")
    last_check: datetime
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None


class APIKey(BaseModel):
    """Schema para chave de API"""
    key_id: UUID
    name: str
    key_prefix: str  # Primeiros caracteres da chave
    permissions: List[str]
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    is_active: bool = True


class RateLimitInfo(BaseModel):
    """Schema para informações de rate limiting"""
    limit: int
    remaining: int
    reset_time: datetime
    window_size: int  # seconds