#!/usr/bin/env python3
"""
Script de Teste da API Sora Pixel Art Generator
===============================================
Testa funcionalidades básicas da API sem depender do OpenAI
"""

import asyncio
import json
import sys
from pathlib import Path

import httpx


async def test_health_check():
    """Testa se a API está rodando"""
    print("🔍 Testando health check...")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health")
            response.raise_for_status()

            data = response.json()
            print(f"✅ API está rodando - Status: {data['status']}")
            print(f"   Versão: {data['version']}")
            return True

    except httpx.ConnectError:
        print("❌ Erro: Não foi possível conectar à API em http://localhost:8000")
        print("   Verifique se o servidor está rodando: python main.py")
        return False
    except Exception as e:
        print(f"❌ Erro no health check: {e}")
        return False


async def test_documentation():
    """Testa se a documentação está acessível"""
    print("\n📚 Testando documentação...")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/docs")

            if response.status_code == 200:
                print("✅ Documentação Swagger acessível em /docs")
            else:
                print("⚠️  Documentação não acessível (modo produção?)")

    except Exception as e:
        print(f"❌ Erro ao acessar documentação: {e}")


async def test_presets_endpoints():
    """Testa endpoints de presets"""
    print("\n🎨 Testando endpoints de presets...")

    try:
        async with httpx.AsyncClient() as client:
            # Testar estilos
            response = await client.get("http://localhost:8000/api/v1/generation/presets/styles")
            response.raise_for_status()

            styles = response.json()
            print(f"✅ Estilos disponíveis: {len(styles['data'])} estilos")

            # Testar animações
            response = await client.get("http://localhost:8000/api/v1/generation/presets/animations")
            response.raise_for_status()

            animations = response.json()
            print(f"✅ Animações disponíveis: {len(animations['data'])} tipos")

            # Testar tamanhos
            response = await client.get("http://localhost:8000/api/v1/generation/presets/sizes")
            response.raise_for_status()

            sizes = response.json()
            print(f"✅ Tamanhos disponíveis: {len(sizes['data'])} opções")

    except Exception as e:
        print(f"❌ Erro ao testar presets: {e}")


async def test_validation_endpoint():
    """Testa endpoint de validação"""
    print("\n✅ Testando validação de parâmetros...")

    try:
        async with httpx.AsyncClient() as client:
            # Teste com parâmetros válidos
            valid_params = {
                "generation_type": "prompt",
                "prompt": "Um teste simples",
                "output_format": "sprite_sheet",
                "style": "8-bit",
                "frames": 4,
                "frame_width": 64,
                "frame_height": 64,
                "animation_type": "idle",
                "fps": 12
            }

            response = await client.post(
                "http://localhost:8000/api/v1/generation/validate",
                json=valid_params
            )
            response.raise_for_status()

            result = response.json()
            if result["data"]["is_valid"]:
                print("✅ Validação com parâmetros válidos: OK")
            else:
                print(f"❌ Parâmetros válidos foram rejeitados: {result['data']['errors']}")

            # Teste com parâmetros inválidos
            invalid_params = {
                "generation_type": "prompt",
                "prompt": "",  # Prompt vazio (inválido)
                "output_format": "sprite_sheet",
                "frames": 50,  # Muitos frames (inválido)
                "fps": 100  # FPS muito alto (inválido)
            }

            response = await client.post(
                "http://localhost:8000/api/v1/generation/validate",
                json=invalid_params
            )
            response.raise_for_status()

            result = response.json()
            if not result["data"]["is_valid"]:
                print("✅ Validação com parâmetros inválidos: Rejeitado corretamente")
                print(f"   Erros detectados: {len(result['data']['errors'])}")
            else:
                print("❌ Parâmetros inválidos foram aceitos incorretamente")

    except Exception as e:
        print(f"❌ Erro ao testar validação: {e}")


async def test_limits_endpoint():
    """Testa endpoint de limites do sistema"""
    print("\n⚙️ Testando limites do sistema...")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/api/v1/generation/limits")
            response.raise_for_status()

            limits = response.json()["data"]
            print("✅ Limites do sistema obtidos:")
            print(f"   Frames: {limits['frames']['min']}-{limits['frames']['max']}")
            print(f"   FPS: {limits['fps']['min']}-{limits['fps']['max']}")
            print(
                f"   Tamanho: {limits['frame_size']['min_width']}x{limits['frame_size']['min_height']} a {limits['frame_size']['max_width']}x{limits['frame_size']['max_height']}")

    except Exception as e:
        print(f"❌ Erro ao testar limites: {e}")


async def test_job_creation_mock():
    """Testa criação de job (sem OpenAI real)"""
    print("\n🚧 Testando criação de job (mock)...")
    print("   ⚠️  Este teste tentará criar um job real - cancele se não quiser usar OpenAI API")

    # Dar chance ao usuário de cancelar
    await asyncio.sleep(2)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            job_params = {
                "generation_type": "prompt",
                "prompt": "Teste de API - ignorar",
                "output_format": "sprite_sheet",
                "style": "8-bit",
                "frames": 1,  # Apenas 1 frame para ser rápido
                "frame_width": 32,
                "frame_height": 32,
                "animation_type": "idle",
                "fps": 12
            }

            print("   📝 Tentando criar job...")
            response = await client.post(
                "http://localhost:8000/api/v1/generation/create",
                json=job_params
            )

            if response.status_code == 201:
                result = response.json()
                job_id = result["data"]["id"]
                print(f"✅ Job criado com sucesso: {job_id}")

                # Testar obter status do job
                print("   📊 Testando obter status...")
                status_response = await client.get(f"http://localhost:8000/api/v1/jobs/{job_id}")
                if status_response.status_code == 200:
                    print("✅ Status do job obtido com sucesso")
                else:
                    print("❌ Erro ao obter status do job")

            else:
                print(f"❌ Erro ao criar job: {response.status_code}")
                print(f"   Response: {response.text}")

    except httpx.TimeoutException:
        print("⏱️  Timeout na criação do job (esperado se OpenAI não estiver configurado)")
    except Exception as e:
        print(f"⚠️  Erro na criação do job: {e}")
        print("   Isso é esperado se OPENAI_API_KEY não estiver configurada")


def check_environment():
    """Verifica configuração do ambiente"""
    print("🔧 Verificando ambiente...")

    # Verificar se .env existe
    env_file = Path(".env")
    if env_file.exists():
        print("✅ Arquivo .env encontrado")

        # Ler configurações básicas
        content = env_file.read_text()
        if "OPENAI_API_KEY=" in content:
            if "your_openai_api_key_here" in content:
                print("⚠️  OPENAI_API_KEY ainda não foi configurada")
            else:
                print("✅ OPENAI_API_KEY configurada")
        else:
            print("❌ OPENAI_API_KEY não encontrada no .env")

    else:
        print("❌ Arquivo .env não encontrado")
        print("   Execute: cp .env.example .env")

    # Verificar diretórios de storage
    storage_dir = Path("storage")
    if storage_dir.exists():
        print("✅ Diretório storage/ existe")
    else:
        print("⚠️  Diretório storage/ não existe (será criado automaticamente)")


async def main():
    """Executa todos os testes"""
    print("🧪 Sora Pixel Art Generator - Teste da API")
    print("=" * 60)

    # Verificar ambiente
    check_environment()

    # Testes da API
    print("\n🌐 Testando API...")

    # Health check é obrigatório
    if not await test_health_check():
        print("\n❌ API não está rodando. Execute primeiro:")
        print("   python main.py")
        sys.exit(1)

    # Outros testes
    await test_documentation()
    await test_presets_endpoints()
    await test_validation_endpoint()
    await test_limits_endpoint()

    # Teste de criação (opcional)
    print("\n" + "=" * 50)
    response = input("🤔 Testar criação de job real? (requer OpenAI API) [y/N]: ")
    if response.lower() in ['y', 'yes', 's', 'sim']:
        await test_job_creation_mock()
    else:
        print("⏭️  Pulando teste de criação de job")

    print("\n🎉 Testes concluídos!")
    print("\n📖 Próximos passos:")
    print("   1. Configure OPENAI_API_KEY no .env")
    print("   2. Execute: python example_usage.py")
    print("   3. Acesse documentação: http://localhost:8000/docs")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏸️  Testes cancelados pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        sys.exit(1)