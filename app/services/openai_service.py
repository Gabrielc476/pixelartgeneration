"""
OpenAI Service - Integração com GPT-Image-1 e DALL-E (VERSÃO CORRIGIDA)
========================================================================
Service para integração com a API da OpenAI para geração de imagens
CORRIGIDO: Parâmetros corretos para gpt-image-1 e fallback inteligente
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
    """Service para integração com OpenAI (gpt-image-1 e DALL-E)"""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self._preferred_model = None
        self._model_tested = False

    async def _detect_best_model(self):
        """Detecta o melhor modelo disponível"""
        if self._model_tested:
            return self._preferred_model

        try:
            # Listar modelos disponíveis
            models = await self.client.models.list()
            available_models = [m.id for m in models.data]

            # Testar gpt-image-1 primeiro
            if 'gpt-image-1' in available_models:
                try:
                    test_response = await self.client.images.generate(
                        model="gpt-image-1",
                        prompt="test",
                        size="1024x1024",
                        quality="high",  # CORRIGIDO: usar "high" ao invés de "standard"
                        n=1
                    )
                    self._preferred_model = "gpt-image-1"
                    logger.info("gpt-image-1 available and working")
                except Exception as e:
                    logger.warning("gpt-image-1 failed test", error=str(e))

            # Fallback para dall-e-3
            if not self._preferred_model and 'dall-e-3' in available_models:
                self._preferred_model = "dall-e-3"
                logger.info("Using dall-e-3 as fallback")

            # Último recurso: dall-e-2
            if not self._preferred_model and 'dall-e-2' in available_models:
                self._preferred_model = "dall-e-2"
                logger.info("Using dall-e-2 as last resort")

            self._model_tested = True
            return self._preferred_model

        except Exception as e:
            logger.error("Failed to detect best model", error=str(e))
            return "dall-e-3"  # Default fallback

    async def generate_frame(
            self,
            prompt: str,
            frame_number: int,
            style: str = "8-bit pixel art",
            size: str = "1024x1024",
            **kwargs
    ) -> tuple[bytes, str]:
        """
        Gera um frame individual usando o melhor modelo disponível

        Args:
            prompt: Prompt para geração
            frame_number: Número do frame na sequência
            style: Estilo da imagem
            size: Tamanho da imagem

        Returns:
            tuple: (dados da imagem em bytes, prompt usado)
        """
        try:
            # Detectar melhor modelo
            model = await self._detect_best_model()

            # Construir prompt específico para pixel art
            enhanced_prompt = self._build_pixel_art_prompt(
                prompt, frame_number, style, **kwargs
            )

            logger.info(
                "Generating frame",
                frame_number=frame_number,
                model=model,
                prompt_length=len(enhanced_prompt)
            )

            # Preparar parâmetros baseados no modelo
            generation_params = self._get_model_params(model, enhanced_prompt, size)

            # Chamar API da OpenAI
            response = await self.client.images.generate(**generation_params)

            # Extrair dados da imagem
            image_data = response.data[0]

            # Processar based no formato de resposta
            if hasattr(image_data, 'b64_json') and image_data.b64_json:
                image_bytes = base64.b64decode(image_data.b64_json)
            elif hasattr(image_data, 'url') and image_data.url:
                # Download da URL
                async with httpx.AsyncClient() as client:
                    img_response = await client.get(image_data.url)
                    image_bytes = img_response.content
            else:
                raise ValueError("No image data received from OpenAI")

            # Processar imagem para pixel art
            processed_bytes = await self._process_for_pixel_art(
                image_bytes, **kwargs
            )

            logger.info(
                "Frame generated successfully",
                frame_number=frame_number,
                model=model,
                image_size=len(processed_bytes)
            )

            return processed_bytes, getattr(image_data, 'revised_prompt', enhanced_prompt)

        except Exception as e:
            logger.error(
                "Failed to generate frame",
                frame_number=frame_number,
                error=str(e),
                error_type=type(e).__name__
            )

            # Adicionar informações mais específicas sobre o erro
            error_msg = str(e).lower()
            if "authentication" in error_msg:
                logger.error("OpenAI authentication failed - check API key")
            elif "billing" in error_msg or "quota" in error_msg:
                logger.error("OpenAI billing/quota issue - check account credits")
            elif "rate" in error_msg:
                logger.error("OpenAI rate limit - wait before retrying")
            elif "invalid_value" in error_msg:
                logger.error("Invalid parameter value - check model requirements")

            raise

    def _get_model_params(self, model: str, prompt: str, size: str) -> dict:
        """Obtém parâmetros corretos para cada modelo"""

        base_params = {
            "model": model,
            "prompt": prompt,
            "size": size,
            "n": 1
        }

        if model == "gpt-image-1":
            # Parâmetros específicos para gpt-image-1
            base_params.update({
                "quality": "high",  # CORRIGIDO: valores válidos: low, medium, high, auto
                "response_format": "b64_json"
            })
        elif model == "dall-e-3":
            # Parâmetros para DALL-E 3
            base_params.update({
                "quality": "standard",  # standard ou hd
                "response_format": "b64_json"
            })
        elif model == "dall-e-2":
            # DALL-E 2 tem limitações
            if size not in ["256x256", "512x512", "1024x1024"]:
                base_params["size"] = "512x512"
            base_params["response_format"] = "b64_json"
            # DALL-E 2 não tem parâmetro quality

        return base_params

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
            model = await self._detect_best_model()

            logger.info(
                "Starting animation generation",
                frames=frame_count,
                animation_type=animation_type,
                model=model
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
                        # Delay baseado no modelo
                        delay = 3 if model == "gpt-image-1" else 2
                        await asyncio.sleep(delay)

                except Exception as e:
                    logger.error(
                        "Failed to generate frame in sequence",
                        frame_number=i,
                        error=str(e)
                    )

                    # Se for erro de rate limit, aguardar mais tempo
                    if "rate" in str(e).lower():
                        logger.info("Rate limited, waiting longer...")
                        await asyncio.sleep(10)

                    # Continuar com outros frames em caso de erro
                    continue

            logger.info(
                "Animation generation completed",
                generated_frames=len(frames),
                requested_frames=frame_count,
                model=model
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
            "retro gaming aesthetic",
            "pixelated",
            "clean geometric shapes"
        ]

        if pixel_perfect:
            pixel_qualities.extend([
                "pixel perfect",
                "sharp boundaries",
                "blocky design"
            ])

        # Adicionar informações de frame se necessário
        frame_info = ""
        if frame_number > 1:
            frame_info = f", frame {frame_number} of animation sequence"

        # Construir prompt final
        enhanced_prompt = (
            f"{base_prompt}{frame_info}, "
            f"{style}, {', '.join(pixel_qualities)}, "
            f"digital art, game sprite, "
            f"transparent background, "
            f"suitable for game development, "
            f"high contrast, clear details, "
            f"simple design"
        )

        # Truncar se muito longo (limite de segurança)
        if len(enhanced_prompt) > 1000:
            enhanced_prompt = enhanced_prompt[:997] + "..."

        return enhanced_prompt

    def _generate_frame_prompts(
            self,
            base_prompt: str,
            frame_count: int,
            animation_type: str,
            **kwargs
    ) -> List[str]:
        """Gera prompts específicos para cada frame da animação"""

        # Templates de animação melhorados
        animation_templates = {
            "walk_cycle": [
                "standing position, ready to walk, both feet on ground",
                "lifting left foot, beginning step forward",
                "left foot forward in mid-air, right foot pushing off",
                "left foot touching ground, right foot lifting",
                "both feet on ground, weight shifting",
                "lifting right foot, beginning step forward",
                "right foot forward in mid-air, left foot pushing off",
                "right foot touching ground, completing cycle"
            ],
            "idle": [
                "standing idle, neutral relaxed pose",
                "slight breathing motion, chest slightly up",
                "small weight shift to left side",
                "gentle head movement, looking slightly left",
                "breathing motion, chest slightly down",
                "small weight shift to right side",
                "gentle head movement, looking slightly right",
                "returning to neutral idle position"
            ],
            "attack": [
                "ready stance, weapon or fist raised",
                "pulling back, preparing for strike",
                "mid-attack, full extension and power",
                "impact moment, maximum force",
                "follow-through motion, completing strike",
                "recovering from attack motion",
                "returning to guard position",
                "back to ready attack stance"
            ],
            "jump": [
                "crouched down, preparing to jump",
                "beginning jump, pushing off ground",
                "mid-air, legs tucked up",
                "peak of jump, arms out for balance",
                "beginning descent, legs extending",
                "landing preparation, legs bent",
                "touching ground, absorbing impact",
                "standing up from landing"
            ]
        }

        # Obter template ou criar genérico
        if animation_type in animation_templates:
            templates = animation_templates[animation_type]
        else:
            templates = [f"animation frame {i}, dynamic pose" for i in range(1, frame_count + 1)]

        # Ajustar para o número de frames solicitado
        if len(templates) > frame_count:
            # Pegar frames distribuídos uniformemente
            step = len(templates) / frame_count
            templates = [templates[int(i * step)] for i in range(frame_count)]
        elif len(templates) < frame_count:
            # Interpolar frames adicionais
            while len(templates) < frame_count:
                templates.append(f"transitional frame, smooth motion")

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

            # Redimensionar para tamanho do frame usando NEAREST para manter pixel perfect
            image = image.resize(
                (frame_width, frame_height),
                Image.NEAREST
            )

            # Aplicar limitação de cores se especificada
            if color_palette_limit and color_palette_limit < 256:
                # Quantizar cores preservando transparência
                alpha = image.split()[-1]  # Salvar canal alpha
                rgb_image = image.convert('RGB')
                quantized = rgb_image.quantize(
                    colors=color_palette_limit,
                    method=Image.Quantize.MEDIANCUT
                )
                quantized = quantized.convert('RGB')
                quantized.putalpha(alpha)
                image = quantized

            # Otimizar transparência (remover pixels quase transparentes)
            if image.mode == 'RGBA':
                pixels = image.load()
                for y in range(image.height):
                    for x in range(image.width):
                        r, g, b, a = pixels[x, y]
                        if a < 128:  # Se alpha < 50%, tornar completamente transparente
                            pixels[x, y] = (0, 0, 0, 0)

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

    async def test_connection(self) -> dict:
        """Testa a conexão com a OpenAI API e detecta melhor modelo"""
        try:
            # Listar modelos disponíveis
            models = await self.client.models.list()
            available_models = [m.id for m in models.data]

            # Verificar modelos de imagem
            image_models = [m for m in available_models if 'dall-e' in m or 'image' in m]

            # Detectar melhor modelo
            best_model = await self._detect_best_model()

            return {
                "success": True,
                "available_models": image_models,
                "total_models": len(available_models),
                "best_model": best_model,
                "gpt_image_1_available": 'gpt-image-1' in available_models,
                "dall_e_3_available": 'dall-e-3' in available_models
            }

        except Exception as e:
            logger.error("OpenAI connection test failed", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }

    async def analyze_image_for_animation(
            self,
            image_bytes: bytes
    ) -> dict:
        """Analisa uma imagem para sugerir parâmetros de animação"""

        try:
            # Análise básica da imagem
            image = Image.open(io.BytesIO(image_bytes))

            # Detectar características
            width, height = image.size
            is_small = width <= 128 and height <= 128

            # Contar cores únicas (aproximado)
            colors = image.getcolors(maxcolors=256*256*256)
            color_count = len(colors) if colors else 256

            # Detectar transparência
            has_transparency = image.mode in ('RGBA', 'LA') or 'transparency' in image.info

            # Análise baseada nas características
            if color_count <= 16 and is_small:
                detected_style = "8-bit pixel art"
                suggested_frames = 8
                complexity = "simple"
            elif color_count <= 64 and is_small:
                detected_style = "16-bit pixel art"
                suggested_frames = 6
                complexity = "medium"
            else:
                detected_style = "modern pixel art"
                suggested_frames = 4
                complexity = "complex"

            analysis = {
                "detected_style": detected_style,
                "suggested_frames": suggested_frames,
                "recommended_size": {
                    "width": min(128, width),
                    "height": min(128, height)
                },
                "animation_potential": 0.8 if is_small else 0.6,
                "complexity_score": min(1.0, color_count / 64),
                "complexity": complexity,
                "properties": {
                    "color_count": color_count,
                    "original_size": {"width": width, "height": height},
                    "has_transparency": has_transparency,
                    "is_square": width == height
                }
            }

            return analysis

        except Exception as e:
            logger.error("Failed to analyze image", error=str(e))
            return {
                "detected_style": "unknown",
                "suggested_frames": 8,
                "recommended_size": {"width": 64, "height": 64},
                "animation_potential": 0.5,
                "complexity_score": 0.5,
                "error": str(e)
            }