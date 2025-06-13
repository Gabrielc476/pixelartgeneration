"""
Sprite Service - Criação de Sprite Sheets
=========================================
Service para criação e manipulação de sprite sheets
"""

import io
import json
import uuid
from pathlib import Path
from typing import List, Tuple

import structlog
from PIL import Image

from app.models.generation import Generation
from app.models.sprite_sheet import SpriteSheet, LayoutType

logger = structlog.get_logger()


class SpriteService:
    """Service para criação de sprite sheets"""

    async def create_sprite_sheet(
            self,
            job_id: uuid.UUID,
            frames_data: List[Tuple[bytes, str]],
            working_dir: Path,
            generation: Generation,
            layout_type: str = "horizontal",
            spacing: int = 0,
            padding: int = 0
    ) -> SpriteSheet:
        """
        Cria um sprite sheet a partir dos frames

        Args:
            job_id: ID do job
            frames_data: Lista de (dados da imagem, prompt usado)
            working_dir: Diretório de trabalho
            generation: Configuração de geração
            layout_type: Tipo de layout (horizontal, vertical, grid)
            spacing: Espaçamento entre frames
            padding: Padding ao redor do sprite sheet

        Returns:
            SpriteSheet model
        """
        try:
            logger.info(
                "Creating sprite sheet",
                job_id=job_id,
                frame_count=len(frames_data),
                layout=layout_type
            )

            # Carregar frames como imagens PIL
            frames = []
            for frame_bytes, _ in frames_data:
                img = Image.open(io.BytesIO(frame_bytes))
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                frames.append(img)

            if not frames:
                raise ValueError("Nenhum frame fornecido")

            # Calcular layout
            layout_info = self._calculate_layout(
                frame_count=len(frames),
                frame_width=generation.frame_width,
                frame_height=generation.frame_height,
                layout_type=layout_type,
                spacing=spacing,
                padding=padding
            )

            # Criar sprite sheet
            sprite_sheet_image = self._create_sprite_sheet_image(
                frames=frames,
                layout_info=layout_info,
                spacing=spacing,
                padding=padding
            )

            # Salvar arquivo
            filename = f"sprite_sheet_{job_id}.png"
            file_path = working_dir / filename

            sprite_sheet_image.save(
                file_path,
                format='PNG',
                optimize=True,
                compress_level=6
            )

            file_size = file_path.stat().st_size

            # Criar frame positions
            frame_positions = self._create_frame_positions(layout_info)

            # Criar modelo SpriteSheet
            sprite_sheet = SpriteSheet(
                job_id=job_id,
                file_path=str(file_path),
                filename=filename,
                file_size=file_size,
                sheet_width=layout_info['sheet_width'],
                sheet_height=layout_info['sheet_height'],
                frame_count=len(frames),
                layout_type=layout_type,
                columns=layout_info['columns'],
                rows=layout_info['rows'],
                spacing=spacing,
                padding=padding,
                frame_width=generation.frame_width,
                frame_height=generation.frame_height,
                fps=generation.fps,
                loop=generation.loop,
                total_duration=generation.total_duration_ms,
                format="PNG",
                has_transparency=True,
                color_depth=32,
                is_optimized=True,
                frame_positions=json.dumps(frame_positions),
                c2pa_embedded=True,
                generated_with="GPT-4o"
            )

            logger.info(
                "Sprite sheet created successfully",
                job_id=job_id,
                file_size=file_size,
                dimensions=f"{layout_info['sheet_width']}x{layout_info['sheet_height']}"
            )

            return sprite_sheet

        except Exception as e:
            logger.error(
                "Failed to create sprite sheet",
                job_id=job_id,
                error=str(e)
            )
            raise

    def _calculate_layout(
            self,
            frame_count: int,
            frame_width: int,
            frame_height: int,
            layout_type: str = "horizontal",
            spacing: int = 0,
            padding: int = 0
    ) -> dict:
        """Calcula layout do sprite sheet"""

        if layout_type == "horizontal":
            columns = frame_count
            rows = 1
        elif layout_type == "vertical":
            columns = 1
            rows = frame_count
        elif layout_type == "grid":
            # Calcular grid mais quadrado possível
            import math
            sqrt_frames = math.sqrt(frame_count)
            columns = math.ceil(sqrt_frames)
            rows = math.ceil(frame_count / columns)
        else:
            # Default para horizontal
            columns = frame_count
            rows = 1

        # Calcular dimensões do sheet
        sheet_width = (columns * frame_width) + ((columns - 1) * spacing) + (2 * padding)
        sheet_height = (rows * frame_height) + ((rows - 1) * spacing) + (2 * padding)

        return {
            'columns': columns,
            'rows': rows,
            'sheet_width': sheet_width,
            'sheet_height': sheet_height,
            'frame_width': frame_width,
            'frame_height': frame_height
        }

    def _create_sprite_sheet_image(
            self,
            frames: List[Image.Image],
            layout_info: dict,
            spacing: int = 0,
            padding: int = 0
    ) -> Image.Image:
        """Cria a imagem do sprite sheet"""

        # Criar imagem de fundo transparente
        sprite_sheet = Image.new(
            'RGBA',
            (layout_info['sheet_width'], layout_info['sheet_height']),
            (0, 0, 0, 0)  # Transparente
        )

        # Posicionar frames
        columns = layout_info['columns']
        frame_width = layout_info['frame_width']
        frame_height = layout_info['frame_height']

        for i, frame in enumerate(frames):
            # Calcular posição
            col = i % columns
            row = i // columns

            x = padding + (col * (frame_width + spacing))
            y = padding + (row * (frame_height + spacing))

            # Garantir que o frame tem o tamanho correto
            if frame.size != (frame_width, frame_height):
                frame = frame.resize((frame_width, frame_height), Image.NEAREST)

            # Colar frame na posição
            sprite_sheet.paste(frame, (x, y), frame)

        return sprite_sheet

    def _create_frame_positions(self, layout_info: dict) -> List[dict]:
        """Cria lista de posições dos frames"""

        positions = []
        columns = layout_info['columns']
        frame_width = layout_info['frame_width']
        frame_height = layout_info['frame_height']

        frame_count = columns * layout_info['rows']

        for i in range(frame_count):
            col = i % columns
            row = i // columns

            x = col * frame_width
            y = row * frame_height

            positions.append({
                'frame': i + 1,
                'x': x,
                'y': y,
                'width': frame_width,
                'height': frame_height
            })

        return positions

    async def create_sprite_sheet_variants(
            self,
            job_id: uuid.UUID,
            frames_data: List[Tuple[bytes, str]],
            working_dir: Path,
            generation: Generation
    ) -> List[SpriteSheet]:
        """Cria múltiplas variações de sprite sheet"""

        variants = []

        # Criar diferentes layouts
        layouts = ["horizontal", "vertical", "grid"]

        for layout in layouts:
            try:
                sprite_sheet = await self.create_sprite_sheet(
                    job_id=job_id,
                    frames_data=frames_data,
                    working_dir=working_dir,
                    generation=generation,
                    layout_type=layout
                )
                variants.append(sprite_sheet)
            except Exception as e:
                logger.warning(
                    "Failed to create sprite sheet variant",
                    layout=layout,
                    error=str(e)
                )

        return variants

    def get_sprite_sheet_metadata(self, sprite_sheet: SpriteSheet) -> dict:
        """Obtém metadados do sprite sheet"""

        frame_positions = []
        if sprite_sheet.frame_positions:
            try:
                frame_positions = json.loads(sprite_sheet.frame_positions)
            except json.JSONDecodeError:
                pass

        return {
            "format": "sprite_sheet",
            "frame_count": sprite_sheet.frame_count,
            "frame_size": {
                "width": sprite_sheet.frame_width,
                "height": sprite_sheet.frame_height
            },
            "sheet_size": {
                "width": sprite_sheet.sheet_width,
                "height": sprite_sheet.sheet_height
            },
            "layout": {
                "type": sprite_sheet.layout_type,
                "columns": sprite_sheet.columns,
                "rows": sprite_sheet.rows,
                "spacing": sprite_sheet.spacing,
                "padding": sprite_sheet.padding
            },
            "animation": {
                "fps": sprite_sheet.fps,
                "total_duration": sprite_sheet.total_duration,
                "loop": sprite_sheet.loop
            },
            "frames": frame_positions,
            "file_info": {
                "filename": sprite_sheet.filename,
                "size_bytes": sprite_sheet.file_size,
                "format": sprite_sheet.format,
                "has_transparency": sprite_sheet.has_transparency,
                "color_depth": sprite_sheet.color_depth
            },
            "c2pa_metadata": {
                "generator": sprite_sheet.generated_with,
                "created_with": "Sora Pixel Art Generator",
                "provenance": "AI Generated Content",
                "embedded": sprite_sheet.c2pa_embedded
            }
        }