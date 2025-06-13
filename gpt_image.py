#!/usr/bin/env python3
"""
🔍 Diagnóstico GPT-Image-1 Access - Sora Pixel Art Generator
==========================================================
Script para verificar acesso ao modelo gpt-image-1 da OpenAI
"""

import asyncio
import os
import sys
import httpx
import json
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent))


async def main():
    print("🔍 DIAGNÓSTICO ACESSO GPT-IMAGE-1")
    print("=" * 50)

    # 1. Verificar API Key
    print("\n1️⃣ VERIFICANDO API KEY")
    print("-" * 25)

    openai_key = os.getenv('OPENAI_API_KEY')

    if not openai_key:
        print("❌ OPENAI_API_KEY não configurada")
        print("💡 Configure no .env: OPENAI_API_KEY=sk-...")
        return

    if not openai_key.startswith('sk-'):
        print("❌ API Key em formato inválido")
        print("💡 Deve começar com 'sk-'")
        return

    print(f"✅ API Key configurada: {openai_key[:12]}...")

    # 2. Testar conexão básica OpenAI
    print("\n2️⃣ TESTANDO CONEXÃO OPENAI")
    print("-" * 30)

    headers = {
        'Authorization': f'Bearer {openai_key}',
        'Content-Type': 'application/json'
    }

    try:
        async with httpx.AsyncClient() as client:
            # Teste 1: Listar modelos
            response = await client.get(
                'https://api.openai.com/v1/models',
                headers=headers,
                timeout=10.0
            )

            if response.status_code == 200:
                models_data = response.json()
                print("✅ Conexão OpenAI funcionando")

                # Verificar se gpt-image-1 está disponível
                available_models = [m['id'] for m in models_data['data']]

                if 'gpt-image-1' in available_models:
                    print("✅ gpt-image-1 DISPONÍVEL na sua conta!")
                else:
                    print("❌ gpt-image-1 NÃO DISPONÍVEL")
                    print("📝 Modelos de imagem encontrados:")
                    image_models = [m for m in available_models if 'dall-e' in m or 'image' in m]
                    for model in image_models:
                        print(f"   - {model}")

            elif response.status_code == 401:
                print("❌ API key inválida ou expirada")
                print("💡 Gere nova chave em: https://platform.openai.com/api-keys")
                return
            else:
                print(f"❌ Erro na API: {response.status_code}")
                print(f"   Resposta: {response.text[:200]}")
                return

    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        return

    # 3. Testar gpt-image-1 especificamente
    print("\n3️⃣ TESTANDO GPT-IMAGE-1")
    print("-" * 25)

    test_payload = {
        "model": "gpt-image-1",
        "prompt": "A simple red square, pixel art style",
        "size": "1024x1024",
        "quality": "standard",
        "n": 1
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                'https://api.openai.com/v1/images/generations',
                headers=headers,
                json=test_payload,
                timeout=60.0
            )

            print(f"🎯 Status: {response.status_code}")

            if response.status_code == 200:
                print("✅ GPT-IMAGE-1 FUNCIONANDO PERFEITAMENTE!")
                result = response.json()
                print(f"   Imagem gerada: {len(result.get('data', []))} resultado(s)")
                return True

            elif response.status_code == 400:
                error_data = response.json()
                error_message = error_data.get('error', {}).get('message', '')
                print(f"❌ Erro 400: {error_message}")

                if 'model' in error_message.lower():
                    print("💡 Modelo gpt-image-1 não disponível para sua conta")
                    print("🔧 SOLUÇÕES:")
                    print("   1. Verificar organização: https://platform.openai.com/settings/organization")
                    print("   2. Usar dall-e-3 temporariamente")

            elif response.status_code == 403:
                print("❌ Acesso negado ao gpt-image-1")
                print("🔧 SOLUÇÕES:")
                print("   1. Verificar organização OpenAI")
                print("   2. Aguardar aprovação para acesso")
                print("   3. Usar dall-e-3 como alternativa")

            elif response.status_code == 429:
                print("❌ Rate limit ou quota esgotada")
                print("💰 Verifique: https://platform.openai.com/account/billing")

            else:
                print(f"❌ Erro inesperado: {response.status_code}")
                print(f"   Resposta: {response.text}")

    except Exception as e:
        print(f"❌ Erro ao testar gpt-image-1: {e}")

    # 4. Testar alternativa DALL-E 3
    print("\n4️⃣ TESTANDO DALL-E 3 (ALTERNATIVA)")
    print("-" * 35)

    dalle3_payload = {
        "model": "dall-e-3",
        "prompt": "A simple red square, pixel art style",
        "size": "1024x1024",
        "quality": "standard",
        "n": 1
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                'https://api.openai.com/v1/images/generations',
                headers=headers,
                json=dalle3_payload,
                timeout=60.0
            )

            if response.status_code == 200:
                print("✅ DALL-E 3 funciona como alternativa!")
                print("💡 Pode usar dall-e-3 enquanto gpt-image-1 não estiver disponível")
                return "dall-e-3"
            else:
                print(f"❌ DALL-E 3 também falhou: {response.status_code}")

    except Exception as e:
        print(f"❌ Erro ao testar DALL-E 3: {e}")

    # 5. Verificar status da organização
    print("\n5️⃣ VERIFICAÇÕES DE ACESSO")
    print("-" * 25)

    try:
        async with httpx.AsyncClient() as client:
            # Verificar detalhes da conta
            response = await client.get(
                'https://api.openai.com/v1/organization',
                headers=headers,
                timeout=10.0
            )

            if response.status_code == 200:
                org_data = response.json()
                print("✅ Informações da organização:")
                print(f"   ID: {org_data.get('id', 'N/A')}")
                print(f"   Nome: {org_data.get('name', 'N/A')}")

                # Verificar se está verificada
                if 'personal' in org_data.get('name', '').lower():
                    print("⚠️  Conta pessoal - pode precisar de verificação")
                    print("🔧 Verifique em: https://platform.openai.com/settings/organization")

            else:
                print(f"⚠️  Não foi possível obter info da organização: {response.status_code}")

    except Exception as e:
        print(f"⚠️  Erro ao verificar organização: {e}")

    # 6. Resumo e recomendações
    print("\n6️⃣ RESUMO E RECOMENDAÇÕES")
    print("-" * 30)

    print("📋 STATUS:")
    print("   • API Key: ✅ Válida")
    print("   • Conexão: ✅ Funcionando")
    print("   • gpt-image-1: ❓ Aguardando verificação")

    print("\n🔧 PRÓXIMOS PASSOS:")
    print("1. Verificar organização em: https://platform.openai.com/settings/organization")
    print("2. Se necessário, iniciar processo de verificação")
    print("3. Usar dall-e-3 temporariamente")
    print("4. Aguardar acesso ao gpt-image-1")

    print("\n💡 SOLUÇÃO TEMPORÁRIA:")
    print("Modificar app/services/openai_service.py:")
    print('   model="gpt-image-1"  # Para contas verificadas')
    print('   model="dall-e-3"     # Para contas não verificadas')

    return False


if __name__ == "__main__":
    result = asyncio.run(main())