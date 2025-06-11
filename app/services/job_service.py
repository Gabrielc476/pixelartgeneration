"""
Job Service - Gerenciamento de Jobs
===================================
Service principal para gerenciamento do ciclo de vida dos jobs
"""

import asyncio
import json
import shutil
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.models.job import Job, JobStatus, OutputFormat
from app.models.generation import Generation
from app.models.sprite_sheet import SpriteSheet
from app.models.frame import Frame
from app.schemas.job import JobCreateRequest, JobResponse
from app.services.openai_service import OpenAIService
from app.services.sprite_service import SpriteService
from app.services.frame_service import FrameService

logger = structlog.get_logger()
settings = get_settings()


class JobService:
    """Service para gerenciamento de jobs de geração"""

    def __init__(self):
        self.openai_service = OpenAIService()
        self.sprite_service = SpriteService()
        self.frame_service = FrameService()

        # Storage paths
        self.storage_path = Path(settings.STORAGE_LOCAL_PATH)
        self.jobs_path = self.storage_path / "jobs"
        self.temp_path = self.storage_path / "temp"

        # Ensure directories exist
        self.jobs_path.mkdir(parents=True, exist_ok=True)
        self.temp_path.mkdir(parents=True, exist_ok=True)

    async def create_job(
            self,
            db: AsyncSession,
            job_data: JobCreateRequest,
            user_id: Optional[uuid.UUID] = None
    ) -> JobResponse:
        """
        Cria um novo job de geração

        Args:
            db: Sessão do banco de dados
            job_data: Dados do job
            user_id: ID do usuário (opcional)

        Returns:
            JobResponse com dados do job criado
        """
        try:
            logger.info(
                "Creating new job",
                generation_type=job_data.generation_type,
                output_format=job_data.output_format,
                user_id=user_id
            )

            # Validar dados do job
            await self._validate_job_data(job_data)

            # Criar diretório de trabalho
            job_id = uuid.uuid4()
            working_dir = self.jobs_path / str(job_id)
            working_dir.mkdir(parents=True, exist_ok=True)

            # Calcular tempo estimado
            estimated_time = self._calculate_estimated_time(job_data)

            # Criar job no banco
            job = Job(
                id=job_id,
                user_id=user_id,
                status=JobStatus.CREATED,
                output_format=job_data.output_format,
                estimated_time=estimated_time,
                working_directory=str(working_dir),
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )

            # Criar configuração de geração
            generation = Generation(
                job_id=job_id,
                generation_type=job_data.generation_type,
                prompt=job_data.prompt,
                upload_id=job_data.upload_id,
                style=job_data.style,
                style_strength=job_data.style_strength,
                animation_type=job_data.animation_type,
                frames=job_data.frames,
                fps=job_data.fps,
                loop=job_data.loop,
                frame_width=job_data.frame_width,
                frame_height=job_data.frame_height,
                background_type=job_data.background_type,
                background_color=job_data.background_color,
                pixel_perfect=job_data.pixel_perfect,
                motion_intensity=job_data.motion_intensity
            )

            # Salvar no banco
            db.add(job)
            db.add(generation)
            await db.commit()
            await db.refresh(job)

            logger.info(
                "Job created successfully",
                job_id=job_id,
                estimated_time=estimated_time
            )

            # Iniciar processamento assíncrono
            asyncio.create_task(self._process_job_async(job_id))

            return JobResponse(
                id=job.id,
                user_id=job.user_id,
                status=job.status,
                progress=job.progress,
                output_format=job.output_format,
                estimated_time=job.estimated_time,
                working_directory=job.working_directory,
                created_at=job.created_at,
                is_processing=job.is_processing,
                is_finished=job.is_finished,
                can_retry=job.can_retry()
            )

        except Exception as e:
            logger.error("Failed to create job", error=str(e))
            raise

    async def get_job(
            self,
            db: AsyncSession,
            job_id: uuid.UUID,
            include_details: bool = False
    ) -> Optional[JobResponse]:
        """
        Obtém um job por ID

        Args:
            db: Sessão do banco
            job_id: ID do job
            include_details: Se deve incluir detalhes dos relacionamentos

        Returns:
            JobResponse ou None se não encontrado
        """
        try:
            query = select(Job).where(Job.id == job_id)

            if include_details:
                query = query.options(
                    selectinload(Job.generation),
                    selectinload(Job.sprite_sheet),
                    selectinload(Job.frames),
                    selectinload(Job.exports)
                )

            result = await db.execute(query)
            job = result.scalar_one_or_none()

            if not job:
                return None

            # Construir URLs para arquivos
            preview_gif_url = None
            thumbnail_url = None

            if job.preview_gif_path and Path(job.preview_gif_path).exists():
                preview_gif_url = f"/static/jobs/{job.id}/preview.gif"

            if job.thumbnail_path and Path(job.thumbnail_path).exists():
                thumbnail_url = f"/static/jobs/{job.id}/thumbnail.png"

            return JobResponse(
                id=job.id,
                user_id=job.user_id,
                status=job.status,
                progress=job.progress,
                current_step=job.current_step,
                output_format=job.output_format,
                estimated_time=job.estimated_time,
                actual_time=job.actual_time,
                retry_count=job.retry_count,
                error_message=job.error_message,
                error_code=job.error_code,
                working_directory=job.working_directory,
                preview_gif_url=preview_gif_url,
                thumbnail_url=thumbnail_url,
                created_at=job.created_at,
                started_at=job.started_at,
                completed_at=job.completed_at,
                expires_at=job.expires_at,
                is_processing=job.is_processing,
                is_finished=job.is_finished,
                can_retry=job.can_retry()
            )

        except Exception as e:
            logger.error("Failed to get job", job_id=job_id, error=str(e))
            return None

    async def list_jobs(
            self,
            db: AsyncSession,
            user_id: Optional[uuid.UUID] = None,
            status: Optional[List[JobStatus]] = None,
            limit: int = 20,
            offset: int = 0
    ) -> List[JobResponse]:
        """Lista jobs com filtros"""
        try:
            query = select(Job)

            if user_id:
                query = query.where(Job.user_id == user_id)

            if status:
                query = query.where(Job.status.in_(status))

            query = query.order_by(Job.created_at.desc()).limit(limit).offset(offset)

            result = await db.execute(query)
            jobs = result.scalars().all()

            # Converter para response schemas
            responses = []
            for job in jobs:
                job_response = await self.get_job(db, job.id)
                if job_response:
                    responses.append(job_response)

            return responses

        except Exception as e:
            logger.error("Failed to list jobs", error=str(e))
            return []

    async def _process_job_async(self, job_id: uuid.UUID):
        """Processa job de forma assíncrona"""

        # Usar nova sessão de banco para processamento assíncrono
        from app.core.database import async_session

        async with async_session() as db:
            try:
                await self._process_job(db, job_id)
            except Exception as e:
                logger.error(
                    "Job processing failed",
                    job_id=job_id,
                    error=str(e)
                )
                # Marcar job como falhou
                await self._update_job_status(
                    db, job_id, JobStatus.FAILED,
                    error_message=str(e)
                )

    async def _process_job(self, db: AsyncSession, job_id: uuid.UUID):
        """Processa um job completo"""

        start_time = datetime.utcnow()

        try:
            # Atualizar status para processamento
            await self._update_job_status(
                db, job_id, JobStatus.PROCESSING,
                current_step="Preparando geração",
                started_at=start_time
            )

            # Carregar job e configurações
            job = await self._load_job_with_generation(db, job_id)
            if not job or not job.generation:
                raise ValueError("Job ou configuração não encontrada")

            generation = job.generation
            working_dir = Path(job.working_directory)

            logger.info(
                "Starting job processing",
                job_id=job_id,
                generation_type=generation.generation_type,
                frames=generation.frames
            )

            # Fase 1: Geração de imagens
            await self._update_job_status(
                db, job_id, JobStatus.GENERATING,
                current_step="Gerando frames com IA",
                progress=10
            )

            frames_data = await self._generate_frames(generation)

            # Fase 2: Pós-processamento
            await self._update_job_status(
                db, job_id, JobStatus.POST_PROCESSING,
                current_step="Processando frames",
                progress=70
            )

            if job.output_format == OutputFormat.SPRITE_SHEET:
                await self._create_sprite_sheet(db, job, frames_data)
            else:
                await self._create_individual_frames(db, job, frames_data)

            # Fase 3: Criação de preview
            await self._update_job_status(
                db, job_id, JobStatus.POST_PROCESSING,
                current_step="Criando preview animado",
                progress=90
            )

            await self._create_preview_gif(job, frames_data)

            # Finalizar
            end_time = datetime.utcnow()
            actual_time = int((end_time - start_time).total_seconds())

            await self._update_job_status(
                db, job_id, JobStatus.COMPLETED,
                current_step="Concluído",
                progress=100,
                completed_at=end_time,
                actual_time=actual_time
            )

            logger.info(
                "Job processing completed",
                job_id=job_id,
                processing_time=actual_time
            )

        except Exception as e:
            logger.error(
                "Job processing failed",
                job_id=job_id,
                error=str(e)
            )
            await self._update_job_status(
                db, job_id, JobStatus.FAILED,
                error_message=str(e),
                error_code="PROCESSING_ERROR"
            )
            raise

    async def _generate_frames(self, generation: Generation) -> List[tuple[bytes, str]]:
        """Gera frames usando OpenAI"""

        if generation.generation_type == "prompt":
            return await self.openai_service.generate_animation_frames(
                prompt=generation.prompt,
                frame_count=generation.frames,
                style=generation.style,
                animation_type=generation.animation_type,
                frame_width=generation.frame_width,
                frame_height=generation.frame_height,
                pixel_perfect=generation.pixel_perfect,
                motion_intensity=generation.motion_intensity
            )
        else:
            # TODO: Implementar geração baseada em imagem
            raise NotImplementedError("Image-based generation not implemented yet")

    async def _create_sprite_sheet(
            self,
            db: AsyncSession,
            job: Job,
            frames_data: List[tuple[bytes, str]]
    ):
        """Cria sprite sheet"""

        sprite_sheet = await self.sprite_service.create_sprite_sheet(
            job_id=job.id,
            frames_data=frames_data,
            working_dir=Path(job.working_directory),
            generation=job.generation
        )

        db.add(sprite_sheet)
        await db.commit()

        logger.info(
            "Sprite sheet created",
            job_id=job.id,
            file_size=sprite_sheet.file_size
        )

    async def _create_individual_frames(
            self,
            db: AsyncSession,
            job: Job,
            frames_data: List[tuple[bytes, str]]
    ):
        """Cria frames individuais"""

        frames = await self.frame_service.create_individual_frames(
            job_id=job.id,
            frames_data=frames_data,
            working_dir=Path(job.working_directory),
            generation=job.generation
        )

        for frame in frames:
            db.add(frame)

        await db.commit()

        logger.info(
            "Individual frames created",
            job_id=job.id,
            frame_count=len(frames)
        )

    async def _create_preview_gif(
            self,
            job: Job,
            frames_data: List[tuple[bytes, str]]
    ):
        """Cria GIF de preview"""

        try:
            from PIL import Image
            import io

            # Carregar frames
            images = []
            for frame_bytes, _ in frames_data:
                img = Image.open(io.BytesIO(frame_bytes))
                images.append(img)

            # Criar GIF
            gif_path = Path(job.working_directory) / "preview.gif"

            if images:
                duration = int(1000 / job.generation.fps)  # ms por frame

                images[0].save(
                    gif_path,
                    save_all=True,
                    append_images=images[1:],
                    duration=duration,
                    loop=0,
                    optimize=True
                )

                # Atualizar job com caminho do GIF
                from app.core.database import async_session
                async with async_session() as db:
                    result = await db.execute(select(Job).where(Job.id == job.id))
                    job_obj = result.scalar_one()
                    job_obj.preview_gif_path = str(gif_path)
                    await db.commit()

                logger.info("Preview GIF created", gif_path=gif_path)

        except Exception as e:
            logger.error("Failed to create preview GIF", error=str(e))

    async def _validate_job_data(self, job_data: JobCreateRequest):
        """Valida dados do job"""

        if job_data.generation_type == "prompt" and not job_data.prompt:
            raise ValueError("Prompt é obrigatório para geração por prompt")

        if job_data.generation_type == "image" and not job_data.upload_id:
            raise ValueError("Upload ID é obrigatório para geração por imagem")

        if job_data.frames < 1 or job_data.frames > 32:
            raise ValueError("Número de frames deve estar entre 1 e 32")

        if job_data.fps < 1 or job_data.fps > 60:
            raise ValueError("FPS deve estar entre 1 e 60")

    def _calculate_estimated_time(self, job_data: JobCreateRequest) -> int:
        """Calcula tempo estimado em segundos"""

        # Base: 30 segundos por frame
        base_time = job_data.frames * 30

        # Ajustar baseado no tamanho
        size_factor = (job_data.frame_width * job_data.frame_height) / (64 * 64)

        # Ajustar baseado na complexidade do estilo
        style_multiplier = 1.5 if "modern" in job_data.style.lower() else 1.0

        return int(base_time * size_factor * style_multiplier)

    async def _update_job_status(
            self,
            db: AsyncSession,
            job_id: uuid.UUID,
            status: JobStatus,
            **kwargs
    ):
        """Atualiza status do job"""

        result = await db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()

        if job:
            job.status = status
            for key, value in kwargs.items():
                if hasattr(job, key) and value is not None:
                    setattr(job, key, value)

            await db.commit()

    async def _load_job_with_generation(
            self,
            db: AsyncSession,
            job_id: uuid.UUID
    ) -> Optional[Job]:
        """Carrega job com configuração de geração"""

        query = select(Job).where(Job.id == job_id).options(
            selectinload(Job.generation)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()