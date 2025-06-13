#!/usr/bin/env python3
"""
Teste com Imagens Simuladas (Mock)
==================================
Testa todo o sistema sem usar OpenAI real
"""

import asyncio
import io
import json
import uuid
from pathlib import Path

from PIL import Image, ImageDraw


class MockImageGenerator:
    """Gerador de imagens simuladas para teste"""

    def __init__(self):
        self.colors = [
            "#FF6B6B",  # Vermelho
            "#4ECDC4",  # Verde-azul
            "#45B7D1",  # Azul
            "#96CEB4",  # Verde
            "#FFEAA7",  # Amarelo
            "#DDA0DD",  # Roxo
            "#F39C12",  # Laranja
            "#E74C3C"  # Vermelho escuro
        ]

    def create_pixel_art_frame(self, width, height, frame_number, style="8-bit"):
        """Cria um frame de pixel art simulado"""

        # Criar imagem base
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Escolher cor baseada no frame
        color = self.colors[frame_number % len(self.colors)]

        if style == "8-bit":
            # Estilo 8-bit: formas simples e pixeladas
            self._draw_8bit_shape(draw, width, height, color, frame_number)
        elif style == "16-bit":
            # Estilo 16-bit: mais detalhado
            self._draw_16bit_shape(draw, width, height, color, frame_number)
        else:
            # Padrão simples
            self._draw_simple_shape(draw, width, height, color, frame_number)

        return img

    def _draw_8bit_shape(self, draw, width, height, color, frame_number):
        """Desenha forma estilo 8-bit"""
        center_x, center_y = width // 2, height // 2

        if frame_number % 4 == 0:
            # Quadrado
            size = min(width, height) // 3
            draw.rectangle([
                center_x - size // 2, center_y - size // 2,
                center_x + size // 2, center_y + size // 2
            ], fill=color)
        elif frame_number % 4 == 1:
            # Círculo (aproximado com quadrados)
            radius = min(width, height) // 4
            for x in range(center_x - radius, center_x + radius, 2):
                for y in range(center_y - radius, center_y + radius, 2):
                    if (x - center_x) ** 2 + (y - center_y) ** 2 <= radius ** 2:
                        draw.rectangle([x, y, x + 1, y + 1], fill=color)
        elif frame_number % 4 == 2:
            # Triângulo
            size = min(width, height) // 3
            draw.polygon([
                (center_x, center_y - size // 2),
                (center_x - size // 2, center_y + size // 2),
                (center_x + size // 2, center_y + size // 2)
            ], fill=color)
        else:
            # Cruz
            size = min(width, height) // 4
            # Horizontal
            draw.rectangle([
                center_x - size, center_y - size // 4,
                center_x + size, center_y + size // 4
            ], fill=color)
            # Vertical
            draw.rectangle([
                center_x - size // 4, center_y - size,
                center_x + size // 4, center_y + size
            ], fill=color)

    def _draw_16bit_shape(self, draw, width, height, color, frame_number):
        """Desenha forma estilo 16-bit"""
        center_x, center_y = width // 2, height // 2

        # Formas mais complexas para 16-bit
        if frame_number % 3 == 0:
            # Estrela
            points = []
            import math
            for i in range(10):
                angle = i * math.pi / 5
                radius = (min(width, height) // 4) if i % 2 == 0 else (min(width, height) // 6)
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                points.append((x, y))
            draw.polygon(points, fill=color)
        elif frame_number % 3 == 1:
            # Hexágono
            import math
            points = []
            for i in range(6):
                angle = i * math.pi / 3
                radius = min(width, height) // 4
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                points.append((x, y))
            draw.polygon(points, fill=color)
        else:
            # Losango
            size = min(width, height) // 3
            draw.polygon([
                (center_x, center_y - size // 2),
                (center_x + size // 2, center_y),
                (center_x, center_y + size // 2),
                (center_x - size // 2, center_y)
            ], fill=color)

    def _draw_simple_shape(self, draw, width, height, color, frame_number):
        """Desenha forma simples"""
        center_x, center_y = width // 2, height // 2
        size = min(width, height) // 4

        # Círculo simples
        draw.ellipse([
            center_x - size, center_y - size,
            center_x + size, center_y + size
        ], fill=color)


async def test_mock_generation():
    """Testa geração com imagens simuladas"""
    print("🎭 Teste com Imagens Simuladas (Mock)")
    print("=" * 45)
    print("✨ Este teste não usa OpenAI - é completamente gratuito!")

    # Configuração do teste
    test_params = {
        "prompt": "Teste simulado - formas coloridas",
        "frames": 4,
        "frame_width": 32,
        "frame_height": 32,
        "style": "8-bit",
        "output_format": "sprite_sheet"
    }

    print(f"📝 Prompt: {test_params['prompt']}")
    print(f"📐 Frames: {test_params['frames']} de {test_params['frame_width']}x{test_params['frame_height']}")
    print(f"🎨 Estilo: {test_params['style']}")

    # Criar gerador mock
    generator = MockImageGenerator()

    # Simular criação de diretório
    job_id = str(uuid.uuid4())
    working_dir = Path("storage") / "jobs" / job_id
    working_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n🆔 Job ID simulado: {job_id}")
    print(f"📁 Diretório: {working_dir}")

    print("\n⚡ Gerando frames simulados...")

    # Gerar frames
    frames = []
    for i in range(test_params["frames"]):
        print(f"   Frame {i + 1}/{test_params['frames']}")

        frame_img = generator.create_pixel_art_frame(
            test_params["frame_width"],
            test_params["frame_height"],
            i,
            test_params["style"]
        )
        frames.append(frame_img)

        # Salvar frame individual
        frame_path = working_dir / f"frame_{i + 1:03d}.png"
        frame_img.save(frame_path, format='PNG')

    print("✅ Frames gerados")

    # Criar sprite sheet
    if test_params["output_format"] == "sprite_sheet":
        print("\n🖼️ Criando sprite sheet...")

        sprite_width = test_params["frame_width"] * test_params["frames"]
        sprite_height = test_params["frame_height"]

        sprite_sheet = Image.new('RGBA', (sprite_width, sprite_height), (0, 0, 0, 0))

        for i, frame in enumerate(frames):
            x_pos = i * test_params["frame_width"]
            sprite_sheet.paste(frame, (x_pos, 0))

        # Salvar sprite sheet
        sprite_path = working_dir / "sprite_sheet.png"
        sprite_sheet.save(sprite_path, format='PNG')

        print(f"✅ Sprite sheet criado: {sprite_path}")

    # Criar GIF de preview
    print("\n🎬 Criando preview GIF...")

    gif_path = working_dir / "preview.gif"

    # Redimensionar frames para GIF (maior para visualização)
    gif_frames = []
    for frame in frames:
        # Aumentar tamanho para melhor visualização (4x)
        large_frame = frame.resize(
            (test_params["frame_width"] * 4, test_params["frame_height"] * 4),
            Image.NEAREST
        )
        gif_frames.append(large_frame)

    # Salvar GIF
    gif_frames[0].save(
        gif_path,
        save_all=True,
        append_images=gif_frames[1:],
        duration=200,  # 200ms por frame
        loop=0,
        optimize=True
    )

    print(f"✅ Preview GIF criado: {gif_path}")

    # Criar metadados
    print("\n📋 Criando metadados...")

    metadata = {
        "format": test_params["output_format"],
        "frame_count": test_params["frames"],
        "frame_size": {
            "width": test_params["frame_width"],
            "height": test_params["frame_height"]
        },
        "style": test_params["style"],
        "animation": {
            "fps": 5,  # 5 FPS para o GIF
            "duration": test_params["frames"] * 200,  # ms
            "loop": True
        },
        "files": {
            "sprite_sheet": "sprite_sheet.png" if test_params["output_format"] == "sprite_sheet" else None,
            "frames": [f"frame_{i + 1:03d}.png" for i in range(test_params["frames"])],
            "preview": "preview.gif"
        },
        "mock_generation": True,
        "generated_with": "Mock Generator",
        "prompt": test_params["prompt"]
    }

    metadata_path = working_dir / "metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"✅ Metadados criados: {metadata_path}")

    # Listar arquivos criados
    print("\n📂 Arquivos criados:")
    files = list(working_dir.glob("*"))
    total_size = 0

    for file in sorted(files):
        size_kb = file.stat().st_size / 1024
        total_size += size_kb
        print(f"   • {file.name} ({size_kb:.1f} KB)")

    print(f"\n📊 Total: {len(files)} arquivos, {total_size:.1f} KB")

    # Mostrar como abrir
    print(f"\n🎯 Para visualizar:")
    print(f"   • Sprite sheet: {sprite_path}")
    print(f"   • Preview GIF: {gif_path}")
    print(f"   • Abra no navegador ou editor de imagem")

    # Verificar se arquivos realmente existem
    print(f"\n✅ Verificação:")
    if sprite_path.exists():
        print(f"   ✅ Sprite sheet: {sprite_path.stat().st_size} bytes")
    if gif_path.exists():
        print(f"   ✅ Preview GIF: {gif_path.stat().st_size} bytes")

    print(f"\n🎉 Teste mock concluído com sucesso!")
    print(f"📁 Todos os arquivos em: {working_dir}")

    return working_dir


async def test_different_styles():
    """Testa diferentes estilos"""
    print("\n🎨 Testando Diferentes Estilos")
    print("-" * 35)

    styles = ["8-bit", "16-bit", "simple"]
    generator = MockImageGenerator()

    for style in styles:
        print(f"\n🎯 Estilo: {style}")

        style_dir = Path("storage") / "mock_tests" / style
        style_dir.mkdir(parents=True, exist_ok=True)

        # Gerar 3 frames de exemplo
        for i in range(3):
            frame = generator.create_pixel_art_frame(64, 64, i, style)
            frame_path = style_dir / f"example_{i + 1}.png"
            frame.save(frame_path)
            print(f"   ✅ {frame_path}")

    print(f"\n📁 Exemplos de estilos em: storage/mock_tests/")


async def main():
    """Função principal"""
    try:
        # Criar diretórios necessários
        Path("storage/jobs").mkdir(parents=True, exist_ok=True)

        # Teste principal
        working_dir = await test_mock_generation()

        # Teste de estilos
        response = input("\n🤔 Testar diferentes estilos também? [y/N]: ")
        if response.lower() in ['y', 'yes', 's', 'sim']:
            await test_different_styles()

        print(f"\n🎉 Todos os testes mock concluídos!")
        print(f"\n💡 Este teste mostra como o sistema funciona")
        print(f"   sem gastar créditos OpenAI")

    except Exception as e:
        print(f"\n❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())