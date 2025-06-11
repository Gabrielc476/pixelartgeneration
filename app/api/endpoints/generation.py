# Conteúdo igual ao arquivo "Generation API Endpoints" já criado
# Este é o arquivo que será salvo em app/api/endpoints/generation.py

"""
Generation API Endpoints
========================
Endpoints para criação e gerenciamento de gerações
"""

from typing import Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_database
from app.schemas.job import JobCreateRequest, JobResponse
from app.schemas.common import APIResponse, ErrorResponse
from app.services.job_service import JobService

logger = structlog.get_logger()
router = APIRouter(prefix="/generation", tags=["generation"])


# Dependency injection
def get_job_service() -> JobService:
    return JobService()


@router.post(
    "/create",
    response_model=APIResponse[JobResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Criar nova geração",
    description="""
    Cria um novo job de geração de pixel art baseado em prompt de texto.

    Suporta dois formatos de output:
    - **sprite_sheet**: Todos os frames em uma única imagem
    - **individual_frames**: Cada frame como arquivo separado

    O processamento é assíncrono. Use o endpoint de status para acompanhar o progresso.
    """
)
async def create_generation(
        job_data: JobCreateRequest,
        db: AsyncSession = Depends(get_database),
        job_service: JobService = Depends(get_job_service),
        # TODO: Adicionar autenticação
        # current_user: User = Depends(get_current_user)
):
    """Cria uma nova geração de pixel art"""

    try:
        logger.info(
            "Creating new generation",
            generation_type=job_data.generation_type,
            output_format=job_data.output_format,
            frames=job_data.frames
        )

        # Validar input básico
        if job_data.generation_type == "prompt" and not job_data.prompt:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Prompt é obrigatório para geração por texto"
            )

        if job_data.generation_type == "image":
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Geração por imagem ainda não implementada"
            )

        # Criar job
        # TODO: Passar user_id quando autenticação estiver implementada
        job_response = await job_service.create_job(
            db=db,
            job_data=job_data,
            user_id=None  # current_user.id
        )

        return APIResponse(
            success=True,
            message="Geração criada com sucesso. Use o endpoint de status para acompanhar o progresso.",
            data=job_response
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create generation", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.post(
    "/prompt",
    response_model=APIResponse[JobResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Gerar por prompt (atalho)",
    description="Endpoint simplificado para geração por prompt de texto"
)
async def generate_from_prompt(
        prompt: str,
        output_format: str = "sprite_sheet",
        style: str = "8-bit",
        frames: int = 8,
        frame_width: int = 64,
        frame_height: int = 64,
        animation_type: str = "walk_cycle",
        fps: int = 12,
        db: AsyncSession = Depends(get_database),
        job_service: JobService = Depends(get_job_service)
):
    """Endpoint simplificado para geração por prompt"""

    try:
        # Validar output_format
        if output_format not in ["sprite_sheet", "individual_frames"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="output_format deve ser 'sprite_sheet' ou 'individual_frames'"
            )

        # Criar request object
        job_data = JobCreateRequest(
            generation_type="prompt",
            prompt=prompt,
            output_format=output_format,
            style=style,
            frames=frames,
            frame_width=frame_width,
            frame_height=frame_height,
            animation_type=animation_type,
            fps=fps
        )

        # Criar job
        job_response = await job_service.create_job(
            db=db,
            job_data=job_data,
            user_id=None
        )

        return APIResponse(
            success=True,
            message="Geração iniciada com sucesso",
            data=job_response
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to generate from prompt", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.get(
    "/presets/styles",
    response_model=APIResponse[list],
    summary="Listar presets de estilo",
    description="Obtém lista de estilos pré-definidos disponíveis"
)
async def get_style_presets():
    """Lista presets de estilo disponíveis"""

    styles = [
        {
            "name": "8-bit Clássico",
            "value": "8-bit",
            "description": "Estilo retrô dos anos 80, paleta limitada",
            "recommended_size": "64x64",
            "example_colors": ["#000000", "#FFFFFF", "#FF0000", "#00FF00"]
        },
        {
            "name": "16-bit",
            "value": "16-bit",
            "description": "Estilo dos anos 90, mais cores disponíveis",
            "recommended_size": "128x128",
            "example_colors": ["#000000", "#FFFFFF", "#FF6B6B", "#4ECDC4"]
        },
        {
            "name": "Game Boy",
            "value": "gameboy",
            "description": "Estilo Game Boy, 4 tons de verde",
            "recommended_size": "32x32",
            "example_colors": ["#0F380F", "#306230", "#8BAC0F", "#9BBD0F"]
        },
        {
            "name": "NES/Famicom",
            "value": "nes",
            "description": "Paleta clássica do Nintendo NES",
            "recommended_size": "64x64",
            "example_colors": ["#000000", "#FCFCFC", "#F8F8F8", "#BCBCBC"]
        },
        {
            "name": "Pixel Art Moderno",
            "value": "modern_pixel",
            "description": "Pixel art com mais detalhes e cores",
            "recommended_size": "128x128",
            "example_colors": ["#2C3E50", "#E74C3C", "#3498DB", "#F39C12"]
        }
    ]

    return APIResponse(
        success=True,
        message="Estilos disponíveis",
        data=styles
    )


@router.get(
    "/presets/animations",
    response_model=APIResponse[list],
    summary="Listar tipos de animação",
    description="Obtém lista de tipos de animação pré-definidos"
)
async def get_animation_presets():
    """Lista tipos de animação disponíveis"""

    animations = [
        {
            "name": "Ciclo de Caminhada",
            "value": "walk_cycle",
            "description": "Animação de personagem caminhando",
            "recommended_frames": 8,
            "recommended_fps": 12
        },
        {
            "name": "Parado/Idle",
            "value": "idle",
            "description": "Animação sutil de personagem parado",
            "recommended_frames": 6,
            "recommended_fps": 8
        },
        {
            "name": "Ataque",
            "value": "attack",
            "description": "Sequência de ataque com arma",
            "recommended_frames": 8,
            "recommended_fps": 15
        },
        {
            "name": "Pulo",
            "value": "jump",
            "description": "Animação de pulo completo",
            "recommended_frames": 6,
            "recommended_fps": 12
        },
        {
            "name": "Corrida",
            "value": "run",
            "description": "Corrida rápida",
            "recommended_frames": 6,
            "recommended_fps": 15
        },
        {
            "name": "Personalizado",
            "value": "custom",
            "description": "Animação personalizada baseada no prompt",
            "recommended_frames": 8,
            "recommended_fps": 12
        }
    ]

    return APIResponse(
        success=True,
        message="Tipos de animação disponíveis",
        data=animations
    )


@router.get(
    "/presets/sizes",
    response_model=APIResponse[list],
    summary="Listar tamanhos recomendados",
    description="Obtém lista de tamanhos de frame recomendados"
)
async def get_size_presets():
    """Lista tamanhos de frame recomendados"""

    sizes = [
        {
            "name": "Micro (16x16)",
            "width": 16,
            "height": 16,
            "description": "Ideal para ícones e elementos pequenos",
            "use_cases": ["ícones", "cursores", "elementos de UI"]
        },
        {
            "name": "Pequeno (32x32)",
            "width": 32,
            "height": 32,
            "description": "Clássico para jogos 8-bit",
            "use_cases": ["sprites de jogos retrô", "avatares pequenos"]
        },
        {
            "name": "Médio (64x64)",
            "width": 64,
            "height": 64,
            "description": "Tamanho padrão, boa qualidade",
            "use_cases": ["personagens principais", "objetos detalhados"]
        },
        {
            "name": "Grande (128x128)",
            "width": 128,
            "height": 128,
            "description": "Alta qualidade para elementos importantes",
            "use_cases": ["bosses", "personagens detalhados", "cutscenes"]
        },
        {
            "name": "Extra Grande (256x256)",
            "width": 256,
            "height": 256,
            "description": "Máxima qualidade, uso específico",
            "use_cases": ["portraits", "arte conceitual", "elementos de fundo"]
        }
    ]

    return APIResponse(
        success=True,
        message="Tamanhos recomendados",
        data=sizes
    )


@router.post(
    "/validate",
    response_model=APIResponse[dict],
    summary="Validar parâmetros de geração",
    description="Valida parâmetros antes de criar a geração"
)
async def validate_generation_params(job_data: JobCreateRequest):
    """Valida parâmetros de geração"""

    try:
        errors = []
        warnings = []

        # Validações básicas
        if job_data.generation_type == "prompt" and not job_data.prompt:
            errors.append("Prompt é obrigatório para geração por texto")

        if job_data.frames < 1 or job_data.frames > 32:
            errors.append("Número de frames deve estar entre 1 e 32")

        if job_data.fps < 1 or job_data.fps > 60:
            errors.append("FPS deve estar entre 1 e 60")

        if job_data.frame_width < 16 or job_data.frame_width > 512:
            errors.append("Largura do frame deve estar entre 16 e 512 pixels")

        if job_data.frame_height < 16 or job_data.frame_height > 512:
            errors.append("Altura do frame deve estar entre 16 e 512 pixels")

        # Warnings
        if job_data.frames > 16:
            warnings.append("Muitos frames podem aumentar significativamente o tempo de processamento")

        if job_data.frame_width > 128 or job_data.frame_height > 128:
            warnings.append("Frames grandes podem demorar mais para serem gerados")

        # Calcular estimativas
        estimated_time = job_data.frames * 30  # 30 segundos por frame
        estimated_cost = 0  # Placeholder para futuro sistema de billing

        validation_result = {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "estimated_time_seconds": estimated_time,
            "estimated_cost": estimated_cost,
            "recommendations": [
                f"Para melhor qualidade, use estilo '{job_data.style}' com {job_data.frames} frames",
                f"FPS {job_data.fps} é adequado para animação tipo '{job_data.animation_type}'"
            ]
        }

        return APIResponse(
            success=True,
            message="Validação concluída",
            data=validation_result
        )

    except Exception as e:
        logger.error("Failed to validate generation params", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro na validação"
        )


@router.get(
    "/limits",
    response_model=APIResponse[dict],
    summary="Obter limites do sistema",
    description="Obtém limites e configurações do sistema"
)
async def get_system_limits():
    """Obtém limites do sistema para geração"""

    limits = {
        "frames": {
            "min": 1,
            "max": 32,
            "recommended": 8
        },
        "fps": {
            "min": 1,
            "max": 60,
            "recommended": 12
        },
        "frame_size": {
            "min_width": 16,
            "max_width": 512,
            "min_height": 16,
            "max_height": 512,
            "recommended": "64x64"
        },
        "prompt": {
            "max_length": 2000,
            "recommended_length": "50-200 caracteres"
        },
        "processing": {
            "max_concurrent_jobs": 5,
            "estimated_time_per_frame": 30,
            "max_processing_time": 1800  # 30 minutos
        },
        "output_formats": ["sprite_sheet", "individual_frames"],
        "supported_styles": ["8-bit", "16-bit", "gameboy", "nes", "modern_pixel"],
        "animation_types": ["walk_cycle", "idle", "attack", "jump", "run", "custom"]
    }

    return APIResponse(
        success=True,
        message="Limites do sistema",
        data=limits
    )