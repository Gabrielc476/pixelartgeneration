#!/usr/bin/env python3
"""
Teste Rápido de Geração de Imagem
=================================
Script simples para testar geração de 1 frame apenas
"""

import asyncio
import time

import httpx


async def quick_test():
    """Teste ultra-rápido com apenas 1 frame"""
    print("⚡ Teste Rápido de Geração de Imagem")
    print("=" * 40)

    async with httpx.AsyncClient(timeout=180.0) as client:
        try:
            # 1. Verificar API
            print("🔍 Verificando API...")
            health_response = await client.get("http://localhost:8000/health")
            health = health_response.json()

            if health["services"]["openai"] != "configured":
                print("❌ OpenAI não configurada no .env")
                return

            print("✅ API e OpenAI configuradas")

            # 2. Parâmetros mínimos
            params = {
                "generation_type": "prompt",
                "prompt": "Uma estrela dourada brilhante, pixel art",
                "output_format": "sprite_sheet",
                "style": "8-bit",
                "frames": 1,  # Apenas 1 frame = mais rápido
                "frame_width": 16,  # Muito pequeno = mais rápido
                "frame_height": 16,
                "fps": 12
            }

            print(f"📝 Prompt: {params['prompt']}")
            print(f"📐 Tamanho: {params['frame_width']}x{params['frame_height']} (1 frame)")

            # Confirmar
            response = input("\n🤔 Criar imagem? (custará ~$0.04) [y/N]: ")
            if response.lower() not in ['y', 'yes', 's', 'sim']:
                print("⏭️ Cancelado")
                return

            # 3. Criar geração
            print("\n🚀 Criando...")
            start_time = time.time()

            create_response = await client.post(
                "http://localhost:8000/api/v1/generation/create",
                json=params
            )
            create_response.raise_for_status()

            job_id = create_response.json()["data"]["id"]
            print(f"✅ Job criado: {job_id}")

            # 4. Aguardar conclusão
            print("⏳ Aguardando (1-2 minutos)...")

            while True:
                await asyncio.sleep(5)

                status_response = await client.get(f"http://localhost:8000/api/v1/jobs/{job_id}")
                job = status_response.json()["data"]

                print(f"   Status: {job['status']} - {job['progress']}%")

                if job["status"] == "completed":
                    end_time = time.time()
                    print(f"\n🎉 Concluído em {int(end_time - start_time)} segundos!")

                    if job.get("preview_gif_url"):
                        print(f"🎬 Preview: http://localhost:8000{job['preview_gif_url']}")

                    print(f"📁 Arquivos em: {job['working_directory']}")
                    break

                elif job["status"] == "failed":
                    print(f"\n❌ Falhou: {job.get('error_message', 'Erro desconhecido')}")
                    break

                elif time.time() - start_time > 180:  # 3 minutos timeout
                    print("\n⏱️ Timeout - processo demorou muito")
                    break

        except httpx.ConnectError:
            print("❌ Não conseguiu conectar à API")
            print("   Execute: python main.py")
        except Exception as e:
            print(f"❌ Erro: {e}")


if __name__ == "__main__":
    asyncio.run(quick_test())