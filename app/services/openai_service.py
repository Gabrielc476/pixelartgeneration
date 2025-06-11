"""
OpenAI Service - Integração com GPT-4o Images
=============================================
Service para integração com a API da OpenAI para geração de imagens
"""

import asyncio
import base64
import io
from typing import List, Optional

import httpx
import structlog
from openai import AsyncOpenAI
from PIL import Image

from app.core.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


class OpenAIService:
    """Service para integração com OpenAI GPT-4o Images"""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def generate_frame(
            self,
            prompt: str,
            frame_number: int,
            style: str = "8-bit pixel art",
            size: str = "1024x1024",
            quality: str = "standard",
            **kwargs
    ) -> tuple[bytes, str]:
        """
        Gera um frame individual usando GPT-4o Images

        Args:
            prompt: Prompt para geração
            frame_number: Número do frame na sequência
            style: Estilo da imagem
            size: Tamanho da imagem
            quality: Qualidade da imagem

        Returns:
            tuple: (dados da imagem em bytes, image_id da OpenAI)
        """
        try:
            # Construir prompt específico para pixel art
            enhanced_prompt = self._build_pixel_art_prompt(
                prompt, frame_number, style, **kwargs
            )

            logger.info(
                "Generating frame with OpenAI",
                frame_number=frame_number,
                prompt_length=len(enhanced_prompt)
            )

            # Chamar API da OpenAI
            response = await self.client.images.generate(
                model="gpt-image-1",  # Usar DALL-E 3 por enquanto, atualizar para GPT-4o quando disponível
                prompt=enhanced_prompt,
                size=size,
                quality=quality,
                n=1,
                response_format="b64_json"
            )

            # Extrair dados da imagem
            image_data = response.data[0]
            image_bytes = base64.b64decode(image_data.b64_json)

            # Processar imagem para pixel art
            processed_bytes = await self._process_for_pixel_art(
                image_bytes, **kwargs
            )

            logger.info(
                "Frame generated successfully",
                frame_number=frame_number,
                image_size=len(processed_bytes)
            )

            return processed_bytes, image_data.revised_prompt or enhanced_prompt

        except Exception as e:
            logger.error(
                "Failed to generate frame",
                frame_number=frame_number,
                error=str(e)
            )
            raise

    async def generate_animation_frames(
            self,
            prompt: str,
            frame_count: int,
            style: str = "8-bit pixel art",
            animation_type: str = "walk_cycle",
            **kwargs
    ) -> List[tuple[bytes, str]]:
        """
        Gera múltiplos frames para uma animação

        Args:
            prompt: Prompt base
            frame_count: Número de frames
            style: Estilo da animação
            animation_type: Tipo de animação

        Returns:
            Lista de (dados da imagem, prompt usado)
        """
        try:
            logger.info(
                "Starting animation generation",
                frames=frame_count,
                animation_type=animation_type
            )

            # Gerar prompts específicos para cada frame
            frame_prompts = self._generate_frame_prompts(
                prompt, frame_count, animation_type, **kwargs
            )

            # Gerar frames com controle de rate limiting
            frames = []
            for i, frame_prompt in enumerate(frame_prompts, 1):
                try:
                    frame_data, used_prompt = await self.generate_frame(
                        frame_prompt,
                        frame_number=i,
                        style=style,
                        **kwargs
                    )
                    frames.append((frame_data, used_prompt))

                    # Rate limiting - aguardar entre requests
                    if i < len(frame_prompts):
                        await asyncio.sleep(1)

                except Exception as e:
                    logger.error(
                        "Failed to generate frame in sequence",
                        frame_number=i,
                        error=str(e)
                    )
                    # Continuar com outros frames em caso de erro
                    continue

            logger.info(
                "Animation generation completed",
                generated_frames=len(frames),
                requested_frames=frame_count
            )

            return frames

        except Exception as e:
            logger.error(
                "Failed to generate animation",
                frame_count=frame_count,
                error=str(e)
            )
            raise

    def _build_pixel_art_prompt(
            self,
            base_prompt: str,
            frame_number: int,
            style: str,
            pixel_perfect: bool = True,
            frame_width: int = 64,
            frame_height: int = 64,
            **kwargs
    ) -> str:
        """Constrói prompt otimizado para pixel art"""

        # Qualidades específicas para pixel art
        pixel_qualities = [
            "pixel art style",
            "crisp edges",
            "no anti-aliasing",
            "limited color palette",
            "retro gaming aesthetic"
        ]

        if pixel_perfect:
            pixel_qualities.extend([
                "pixel perfect",
                "sharp boundaries",
                "clean geometric shapes"
            ])

        # Adicionar informações de frame se necessário
        frame_info = ""
        if frame_number > 1:
            frame_info = f", frame {frame_number} of animation sequence"

        # Construir prompt final
        enhanced_prompt = (
            f"{base_prompt}{frame_info}, "
            f"{style}, {', '.join(pixel_qualities)}, "
            f"resolution {frame_width}x{frame_height}, "
            f"transparent background, "
            f"suitable for game sprites"
        )

        return enhanced_prompt

    def _generate_frame_prompts(
            self,
            base_prompt: str,
            frame_count: int,
            animation_type: str,
            **kwargs
    ) -> List[str]:
        """Gera prompts específicos para cada frame da animação"""

        # Templates de animação
        animation_templates = {
            "walk_cycle": [
                "standing position, ready to walk",
                "lifting left foot, mid-step",
                "left foot forward, right foot back",
                "both feet together, transitioning",
                "lifting right foot, mid-step",
                "right foot forward, left foot back",
                "both feet together, completing cycle",
                "back to standing position"
            ],
            "idle": [
                "standing idle, neutral pose",
                "slight lean to the left",
                "slight breathing animation, chest up",
                "small movement, shifting weight",
                "slight lean to the right",
                "breathing animation, chest down",
                "small head movement",
                "back to neutral pose"
            ],
            "attack": [
                "ready position, weapon raised",
                "pulling back for attack",
                "mid-swing, maximum extension",
                "impact frame, full force",
                "follow-through motion",
                "recovering from attack",
                "returning to guard position",
                "back to ready stance"
            ]
        }

        # Obter template ou criar genérico
        if animation_type in animation_templates:
            templates = animation_templates[animation_type]
        else:
            templates = [f"frame {i} of {frame_count}" for i in range(1, frame_count + 1)]

        # Ajustar para o número de frames solicitado
        if len(templates) > frame_count:
            templates = templates[:frame_count]
        elif len(templates) < frame_count:
            # Repetir último template se necessário
            while len(templates) < frame_count:
                templates.append(templates[-1])

        # Combinar com prompt base
        frame_prompts = []
        for i, template in enumerate(templates):
            frame_prompt = f"{base_prompt}, {template}"
            frame_prompts.append(frame_prompt)

        return frame_prompts

    async def _process_for_pixel_art(
            self,
            image_bytes: bytes,
            frame_width: int = 64,
            frame_height: int = 64,
            color_palette_limit: Optional[int] = None,
            **kwargs
    ) -> bytes:
        """Processa imagem para otimizar para pixel art"""

        try:
            # Carregar imagem
            image = Image.open(io.BytesIO(image_bytes))

            # Converter para RGBA se necessário
            if image.mode != 'RGBA':
                image = image.convert('RGBA')

            # Redimensionar para tamanho do frame
            image = image.resize(
                (frame_width, frame_height),
                Image.NEAREST  # Usar NEAREST para manter pixel perfect
            )

            # Aplicar limitação de cores se especificada
            if color_palette_limit and color_palette_limit < 256:
                # Quantizar cores
                image = image.quantize(
                    colors=color_palette_limit,
                    method=Image.Quantize.MEDIANCUT
                ).convert('RGBA')

            # Salvar como PNG com transparência
            output = io.BytesIO()
            image.save(
                output,
                format='PNG',
                optimize=True,
                compress_level=6
            )

            return output.getvalue()

        except Exception as e:
            logger.error("Failed to process image for pixel art", error=str(e))
            # Retornar imagem original em caso de erro
            return image_bytes

    async def analyze_image_for_animation(
            self,
            image_bytes: bytes
    ) -> dict:
        """Analisa uma imagem para sugerir parâmetros de animação"""

        try:
            # Esta funcionalidade pode ser implementada futuramente
            # usando GPT-4V para análise de imagem

            # Por enquanto, retornar análise básica
            image = Image.open(io.BytesIO(image_bytes))

            analysis = {
                "detected_style": "pixel_art",
                "suggested_frames": 8,
                "recommended_size": {
                    "width": min(64, image.width),
                    "height": min(64, image.height)
                },
                "animation_potential": 0.8,
                "complexity_score": 0.6
            }

            return analysis

        except Exception as e:
            logger.error("Failed to analyze image", error=str(e))
            return {
                "detected_style": "unknown",
                "suggested_frames": 8,
                "recommended_size": {"width": 64, "height": 64},
                "animation_potential": 0.5,
                "complexity_score": 0.5
            }