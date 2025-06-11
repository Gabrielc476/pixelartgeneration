# Conteúdo igual ao arquivo "Jobs API Endpoints" já criado
# Este é o arquivo que será salvo em app/api/endpoints/jobs.py

"""
Jobs API Endpoints
==================
Endpoints para gerenciamento e monitoramento de jobs
"""

from typing import List, Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_database
from app.models.job import JobStatus, OutputFormat
from app.schemas.job import JobResponse, JobListResponse
from app.schemas.common import APIResponse, ErrorResponse
from app.services.job_service import JobService

logger = structlog.get_logger()
router = APIRouter(prefix="/jobs", tags=["jobs"])


# Dependency injection
def get_job_service() -> JobService:
    return JobService()


@router.get(
    "/{job_id}",
    response_model=APIResponse[JobResponse],
    summary="Obter status do job",
    description="""
    Obtém o status atual de um job de geração.

    Use este endpoint para fazer polling e acompanhar o progresso:
    - **created**: Job criado, aguardando processamento
    - **processing**: Preparando geração
    - **generating**: Gerando frames com IA
    - **post_processing**: Processando e organizando arquivos
    - **completed**: Concluído com sucesso
    - **failed**: Falhou (verifique error_message)
    """
)
async def get_job_status(
        job_id: UUID,
        include_details: bool = Query(False, description="Incluir detalhes dos relacionamentos"),
        db: AsyncSession = Depends(get_database),
        job_service: JobService = Depends(get_job_service)
):
    """Obtém status de um job específico"""

    try:
        job = await job_service.get_job(
            db=db,
            job_id=job_id,
            include_details=include_details
        )

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job não encontrado"
            )

        return APIResponse(
            success=True,
            message="Status do job obtido com sucesso",
            data=job
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get job status", job_id=job_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.get(
    "",
    response_model=APIResponse[List[JobResponse]],
    summary="Listar jobs",
    description="Lista jobs com filtros opcionais. Útil para dashboards e histórico."
)
async def list_jobs(
        status_filter: Optional[List[JobStatus]] = Query(None, description="Filtrar por status"),
        output_format: Optional[List[OutputFormat]] = Query(None, description="Filtrar por formato"),
        limit: int = Query(20, ge=1, le=100, description="Número máximo de resultados"),
        offset: int = Query(0, ge=0, description="Deslocamento para paginação"),
        db: AsyncSession = Depends(get_database),
        job_service: JobService = Depends(get_job_service),
        # TODO: Adicionar filtro por usuário quando autenticação estiver implementada
        # current_user: User = Depends(get_current_user)
):
    """Lista jobs com filtros"""

    try:
        jobs = await job_service.list_jobs(
            db=db,
            user_id=None,  # current_user.id quando autenticação estiver implementada
            status=status_filter,
            limit=limit,
            offset=offset
        )

        return APIResponse(
            success=True,
            message=f"Encontrados {len(jobs)} jobs",
            data=jobs
        )

    except Exception as e:
        logger.error("Failed to list jobs", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.get(
    "/{job_id}/progress",
    response_model=APIResponse[dict],
    summary="Obter progresso detalhado",
    description="Obtém informações detalhadas de progresso para monitoramento em tempo real"
)
async def get_job_progress(
        job_id: UUID,
        db: AsyncSession = Depends(get_database),
        job_service: JobService = Depends(get_job_service)
):
    """Obtém progresso detalhado de um job"""

    try:
        job = await job_service.get_job(db=db, job_id=job_id)

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job não encontrado"
            )

        # Calcular tempo restante estimado
        estimated_remaining = None
        if job.is_processing and job.estimated_time and job.progress > 0:
            elapsed_ratio = job.progress / 100
            if elapsed_ratio > 0:
                total_estimated = job.estimated_time
                elapsed_estimated = total_estimated * elapsed_ratio
                estimated_remaining = max(0, total_estimated - elapsed_estimated)

        # Mapear etapas para descrições mais detalhadas
        step_descriptions = {
            "Preparando geração": "Analisando prompt e configurando parâmetros",
            "Gerando frames com IA": "Criando frames individuais usando GPT-4o",
            "Processando frames": "Otimizando imagens e aplicando filtros",
            "Criando preview animado": "Gerando GIF de preview",
            "Concluído": "Geração finalizada com sucesso"
        }

        progress_info = {
            "job_id": job.id,
            "status": job.status,
            "progress_percentage": job.progress,
            "current_step": job.current_step,
            "step_description": step_descriptions.get(job.current_step, job.current_step),
            "estimated_time_remaining_seconds": estimated_remaining,
            "is_processing": job.is_processing,
            "is_finished": job.is_finished,
            "can_retry": job.can_retry,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "estimated_completion": None  # Calculado se necessário
        }

        # Adicionar informações específicas baseadas no status
        if job.status == JobStatus.FAILED:
            progress_info.update({
                "error_message": job.error_message,
                "error_code": job.error_code,
                "retry_count": job.retry_count
            })
        elif job.status == JobStatus.COMPLETED:
            progress_info.update({
                "completed_at": job.completed_at,
                "actual_processing_time": job.actual_time,
                "preview_gif_url": job.preview_gif_url,
                "thumbnail_url": job.thumbnail_url
            })

        return APIResponse(
            success=True,
            message="Progresso obtido com sucesso",
            data=progress_info
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get job progress", job_id=job_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.post(
    "/{job_id}/retry",
    response_model=APIResponse[JobResponse],
    summary="Tentar novamente",
    description="Tenta executar novamente um job que falhou"
)
async def retry_job(
        job_id: UUID,
        db: AsyncSession = Depends(get_database),
        job_service: JobService = Depends(get_job_service)
):
    """Tenta executar novamente um job que falhou"""

    try:
        job = await job_service.get_job(db=db, job_id=job_id)

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job não encontrado"
            )

        if not job.can_retry:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job não pode ser executado novamente (não falhou ou excedeu tentativas)"
            )

        # TODO: Implementar lógica de retry
        # Por enquanto, retornar erro informativo
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Funcionalidade de retry será implementada em breve"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to retry job", job_id=job_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.delete(
    "/{job_id}",
    response_model=APIResponse[dict],
    summary="Cancelar/deletar job",
    description="Cancela um job em processamento ou deleta um job concluído"
)
async def delete_job(
        job_id: UUID,
        force: bool = Query(False, description="Forçar deleção mesmo se em processamento"),
        db: AsyncSession = Depends(get_database),
        job_service: JobService = Depends(get_job_service)
):
    """Cancela ou deleta um job"""

    try:
        job = await job_service.get_job(db=db, job_id=job_id)

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job não encontrado"
            )

        if job.is_processing and not force:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job está em processamento. Use force=true para cancelar"
            )

        # TODO: Implementar lógica de cancelamento/deleção
        # - Cancelar processamento se necessário
        # - Remover arquivos gerados
        # - Atualizar status no banco

        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Funcionalidade de cancelamento será implementada em breve"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete job", job_id=job_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.get(
    "/stats/summary",
    response_model=APIResponse[dict],
    summary="Estatísticas dos jobs",
    description="Obtém estatísticas gerais dos jobs do sistema"
)
async def get_jobs_stats(
        db: AsyncSession = Depends(get_database),
        job_service: JobService = Depends(get_job_service)
):
    """Obtém estatísticas dos jobs"""

    try:
        # TODO: Implementar lógica de estatísticas
        # Por enquanto, retornar dados mock

        stats = {
            "total_jobs": 0,
            "completed_jobs": 0,
            "failed_jobs": 0,
            "processing_jobs": 0,
            "avg_processing_time_seconds": 0,
            "by_output_format": {
                "sprite_sheet": 0,
                "individual_frames": 0
            },
            "by_status": {
                "created": 0,
                "processing": 0,
                "generating": 0,
                "post_processing": 0,
                "completed": 0,
                "failed": 0,
                "cancelled": 0
            },
            "recent_activity": {
                "last_24h": 0,
                "last_7d": 0,
                "last_30d": 0
            }
        }

        return APIResponse(
            success=True,
            message="Estatísticas obtidas",
            data=stats
        )

    except Exception as e:
        logger.error("Failed to get jobs stats", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.get(
    "/batch/status",
    response_model=APIResponse[List[JobResponse]],
    summary="Status de múltiplos jobs",
    description="Obtém status de múltiplos jobs em uma única requisição"
)
async def get_batch_job_status(
        job_ids: List[UUID] = Query(..., description="Lista de IDs dos jobs"),
        db: AsyncSession = Depends(get_database),
        job_service: JobService = Depends(get_job_service)
):
    """Obtém status de múltiplos jobs"""

    try:
        if len(job_ids) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Máximo de 50 jobs por requisição"
            )

        jobs = []
        for job_id in job_ids:
            job = await job_service.get_job(db=db, job_id=job_id)
            if job:
                jobs.append(job)

        return APIResponse(
            success=True,
            message=f"Status de {len(jobs)} jobs obtido",
            data=jobs
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get batch job status", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.get(
    "/{job_id}/files",
    response_model=APIResponse[dict],
    summary="Listar arquivos do job",
    description="Lista todos os arquivos gerados por um job concluído"
)
async def list_job_files(
        job_id: UUID,
        db: AsyncSession = Depends(get_database),
        job_service: JobService = Depends(get_job_service)
):
    """Lista arquivos gerados por um job"""

    try:
        job = await job_service.get_job(db=db, job_id=job_id, include_details=True)

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job não encontrado"
            )

        if job.status != JobStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job ainda não foi concluído"
            )

        # TODO: Implementar listagem de arquivos baseada no output_format
        # - Para sprite_sheet: arquivo principal + preview + metadata
        # - Para individual_frames: frames individuais + ZIP + preview + metadata

        files_info = {
            "job_id": job_id,
            "output_format": job.output_format,
            "files": [],
            "preview_gif": job.preview_gif_url,
            "thumbnail": job.thumbnail_url,
            "working_directory": job.working_directory
        }

        return APIResponse(
            success=True,
            message="Arquivos listados",
            data=files_info
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to list job files", job_id=job_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )