#!/usr/bin/env python3
"""
Teste de Configuração OpenAI
============================
Testa se a OpenAI API está configurada corretamente
"""

import asyncio
import os
from pathlib import Path

import httpx
from openai import AsyncOpenAI


async def test_env_file():
    """Testa se o arquivo .env está configurado"""
    print("📄 Verificando arquivo .env...")

    env_file = Path(".env")
    if not env_file.exists():
        print("❌ Arquivo .env não encontrado")
        print("   Execute: cp .env.example .env")
        return False

    print("✅ Arquivo .env encontrado")

    # Ler configurações
    content = env_file.read_text(encoding='utf-8')

    if "OPENAI_API_KEY=" not in content:
        print("❌ OPENAI_API_KEY não encontrada no .env")
        return False

    # Extrair a chave
    lines = content.split('\n')
    api_key = None

    for line in lines:
        line = line.strip()
        if line.startswith('OPENAI_API_KEY=') and not line.startswith('#'):
            api_key = line.split('=', 1)[1].strip()
            break

    if not api_key or api_key == "your_openai_api_key_here":
        print("❌ OPENAI_API_KEY não configurada")
        print("   Configure sua chave no arquivo .env")
        return False

    if not api_key.startswith('sk-'):
        print("❌ OPENAI_API_KEY parece inválida (deve começar com 'sk-')")
        return False

    print(f"✅ OPENAI_API_KEY configurada (sk-...{api_key[-6:]})")
    return api_key


async def test_openai_connection(api_key):
    """Testa conexão direta com OpenAI"""
    print("\n🔌 Testando conexão com OpenAI...")

    try:
        client = AsyncOpenAI(api_key=api_key)

        # Teste simples: listar modelos
        print("   Consultando modelos disponíveis...")
        models = await client.models.list()

        # Verificar se tem acesso aos modelos de imagem
        image_models = [model.id for model in models.data if 'dall-e' in model.id.lower()]

        print(f"✅ Conexão OpenAI OK - {len(models.data)} modelos disponíveis")

        if image_models:
            print(f"🎨 Modelos de imagem: {', '.join(image_models)}")
        else:
            print("⚠️  Nenhum modelo de imagem DALL-E encontrado")
            print("   Verifique se sua conta tem acesso ao DALL-E")

        return True

    except Exception as e:
        error_str = str(e).lower()

        if "invalid api key" in error_str or "unauthorized" in error_str:
            print("❌ Chave de API inválida")
            print("   Verifique se a chave está correta no .env")
        elif "insufficient_quota" in error_str:
            print("❌ Quota insuficiente")
            print("   Sua conta OpenAI não tem créditos")
        elif "rate_limit" in error_str:
            print("⚠️  Rate limit excedido")
            print("   Aguarde alguns minutos e tente novamente")
        else:
            print(f"❌ Erro na conexão: {e}")

        return False


async def test_api_integration():
    """Testa integração com nossa API"""
    print("\n🔗 Testando integração com nossa API...")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get("http://localhost:8000/health")

            if response.status_code == 200:
                health = response.json()
                openai_status = health["services"]["openai"]

                print(f"✅ API local: {health['status']}")
                print(f"🔑 OpenAI status: {openai_status}")

                if openai_status == "configured":
                    print("✅ Integração completa funcionando")
                    return True
                else:
                    print("❌ OpenAI não está configurada na API")
                    return False
            else:
                print(f"❌ API local com problemas: HTTP {response.status_code}")
                return False

    except httpx.ConnectError:
        print("❌ Não conseguiu conectar à API local")
        print("   Execute: python main.py")
        return False
    except Exception as e:
        print(f"❌ Erro na integração: {e}")
        return False


async def test_simple_image_generation(api_key):
    """Teste muito simples de geração de imagem"""
    print("\n🎨 Teste simples de geração (opcional)...")

    response = input("🤔 Testar geração de 1 imagem simples? (custará ~$0.04) [y/N]: ")
    if response.lower() not in ['y', 'yes', 's', 'sim']:
        print("⏭️ Pulando teste de geração")
        return True

    try:
        print("   Gerando imagem de teste...")

        client = AsyncOpenAI(api_key=api_key)

        response = await client.images.generate(
            model="dall-e-3",
            prompt="A simple golden star, pixel art style, 16x16, transparent background",
            size="1024x1024",
            quality="standard",
            n=1
        )

        print("✅ Imagem gerada com sucesso!")
        print(f"   URL: {response.data[0].url}")

        return True

    except Exception as e:
        print(f"❌ Erro na geração: {e}")
        return False


def show_configuration_help():
    """Mostra ajuda para configuração"""
    print("\n📚 Como Configurar OpenAI API:")
    print("-" * 40)
    print("1. Visite: https://platform.openai.com/api-keys")
    print("2. Faça login na sua conta OpenAI")
    print("3. Clique em 'Create new secret key'")
    print("4. Copie a chave (começa com 'sk-')")
    print("5. Edite o arquivo .env:")
    print("   OPENAI_API_KEY=sua_chave_aqui")
    print("6. Execute este teste novamente")

    print("\n💰 Custos Estimados:")
    print("• DALL-E 3 (1024x1024): ~$0.04 por imagem")
    print("• Sprite de 8 frames: ~$0.32")
    print("• Teste rápido (1 frame pequeno): ~$0.04")

    print("\n🔧 Solução de Problemas:")
    print("• Chave inválida: Verifique se copiou corretamente")
    print("• Sem créditos: Adicione créditos em platform.openai.com")
    print("• Rate limit: Aguarde alguns minutos")


async def main():
    """Função principal"""
    print("🔑 Teste de Configuração OpenAI")
    print("=" * 40)

    # 1. Verificar arquivo .env
    api_key = await test_env_file()
    if not api_key:
        show_configuration_help()
        return

    # 2. Testar conexão OpenAI
    openai_ok = await test_openai_connection(api_key)
    if not openai_ok:
        show_configuration_help()
        return

    # 3. Testar integração com API
    api_ok = await test_api_integration()

    # 4. Teste opcional de geração
    if openai_ok and api_ok:
        await test_simple_image_generation(api_key)

    # 5. Resumo
    print("\n" + "=" * 40)
    print("📊 RESUMO:")
    print(f"   .env file: {'✅' if api_key else '❌'}")
    print(f"   OpenAI API: {'✅' if openai_ok else '❌'}")
    print(f"   Integração: {'✅' if api_ok else '❌'}")

    if api_key and openai_ok and api_ok:
        print("\n🎉 Tudo configurado corretamente!")
        print("\n🚀 Próximos passos:")
        print("   • python quick_test.py           # Teste rápido")
        print("   • python test_image_generation.py # Teste completo")
        print("   • python main.py                 # Iniciar servidor")
    else:
        print("\n❌ Há problemas na configuração")
        show_configuration_help()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏸️ Teste cancelado pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")