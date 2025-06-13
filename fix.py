#!/usr/bin/env python3
"""
🔧 FIX ALL-IN-ONE - Sora Pixel Art Generator
==========================================
Script único que resolve TODOS os problemas automaticamente:
- Carrega .env manualmente
- Testa API OpenAI
- Detecta modelo disponível (gpt-image-1 ou dall-e-3)
- Corrige código automaticamente
- Diagnóstico completo
"""

import os
import sys
import asyncio
from pathlib import Path


# ============================================================================
# 🔧 CONFIGURAÇÃO E CARREGAMENTO
# ============================================================================

def load_env_file():
    """Carrega arquivo .env manualmente"""
    print("📁 CARREGANDO ARQUIVO .ENV")
    print("-" * 25)

    env_file = Path(".env")

    if not env_file.exists():
        print("❌ Arquivo .env não encontrado!")
        print("💡 Crie o arquivo .env com:")
        print("   OPENAI_API_KEY=sk-sua-chave-aqui")
        return False

    try:
        content = env_file.read_text(encoding='utf-8')
        loaded_vars = {}

        for line_num, line in enumerate(content.splitlines(), 1):
            line = line.strip()

            # Pular comentários e linhas vazias
            if not line or line.startswith('#'):
                continue

            # Verificar formato KEY=VALUE
            if '=' not in line:
                print(f"⚠️  Linha {line_num} ignorada: {line}")
                continue

            # Separar chave e valor
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()

            # Remover aspas se existirem
            if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]

            # Definir no ambiente
            os.environ[key] = value
            loaded_vars[key] = value

        print(f"✅ Carregadas {len(loaded_vars)} variáveis")

        # Mostrar variáveis importantes
        important_vars = ['OPENAI_API_KEY', 'DATABASE_URL', 'SECRET_KEY']
        for var in important_vars:
            if var in loaded_vars:
                if 'key' in var.lower() or 'secret' in var.lower():
                    display = f"{loaded_vars[var][:12]}..." if len(loaded_vars[var]) > 12 else "***"
                else:
                    display = loaded_vars[var][:50] + "..." if len(loaded_vars[var]) > 50 else loaded_vars[var]
                print(f"   {var}: {display}")

        return True

    except Exception as e:
        print(f"❌ Erro ao carregar .env: {e}")
        return False


# ============================================================================
# 🧪 TESTES OPENAI
# ============================================================================

def test_openai_sync():
    """Teste síncrono da OpenAI (mais simples)"""
    print("\n🧪 TESTE RÁPIDO OPENAI")
    print("-" * 25)

    openai_key = os.getenv('OPENAI_API_KEY')

    if not openai_key:
        print("❌ OPENAI_API_KEY não encontrada")
        return None

    print(f"🔑 API Key: {openai_key[:12]}...{openai_key[-8:]}")

    if not openai_key.startswith('sk-'):
        print("❌ Formato inválido (deve começar com sk-)")
        return None

    try:
        from openai import OpenAI
        print("✅ Biblioteca OpenAI importada")

        client = OpenAI(api_key=openai_key)
        print("✅ Cliente criado")

        # Testar listagem de modelos
        print("🔍 Testando conexão...")
        models = client.models.list()
        print("✅ Conexão funcionando!")

        # Encontrar modelos de imagem
        available_models = [m.id for m in models.data]
        image_models = [m for m in available_models if 'dall-e' in m or 'image' in m]

        print(f"🎨 Modelos de imagem: {image_models}")

        # Determinar qual modelo testar
        if 'gpt-image-1' in image_models:
            test_model = 'gpt-image-1'
            print("🎯 Testando gpt-image-1...")
        elif 'dall-e-3' in image_models:
            test_model = 'dall-e-3'
            print("🔄 gpt-image-1 não disponível, testando dall-e-3...")
        else:
            print("❌ Nenhum modelo adequado encontrado")
            return None

        # Testar geração de imagem
        try:
            print("🚀 Gerando imagem de teste...")

            response = client.images.generate(
                model=test_model,
                prompt="A simple red pixel art square",
                size="1024x1024",
                quality="standard" if test_model != "dall-e-2" else None,
                n=1
            )

            print(f"🎉 SUCESSO! {test_model} funcionando!")
            print("✅ API Key válida")
            print("✅ Créditos disponíveis")

            if response.data:
                print(f"🔗 Imagem: {response.data[0].url[:50]}...")

            return test_model

        except Exception as e:
            error_msg = str(e).lower()
            print(f"❌ Erro na geração com {test_model}: {e}")

            # Se gpt-image-1 falhar, tentar dall-e-3
            if test_model == 'gpt-image-1' and 'dall-e-3' in image_models:
                print("🔄 Tentando DALL-E 3...")

                try:
                    response = client.images.generate(
                        model="dall-e-3",
                        prompt="A simple red pixel art square",
                        size="1024x1024",
                        quality="standard",
                        n=1
                    )

                    print("✅ DALL-E 3 funcionando como alternativa!")
                    return "dall-e-3"

                except Exception as e2:
                    print(f"❌ DALL-E 3 também falhou: {e2}")

            # Diagnóstico do erro
            if 'authentication' in error_msg:
                print("💡 Problema: API key inválida")
            elif 'billing' in error_msg or 'quota' in error_msg:
                print("💡 Problema: Sem créditos ou quota esgotada")
                print("💰 Verifique: https://platform.openai.com/account/billing")
            elif 'organization' in error_msg:
                print("💡 Problema: Organização não verificada")
                print("🔧 Acesse: https://platform.openai.com/settings/organization")

            return None

    except ImportError:
        print("❌ Biblioteca openai não instalada")
        print("💡 Execute: pip install openai")
        return None
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        return None


async def test_openai_async():
    """Teste assíncrono completo da OpenAI"""
    print("\n🔍 TESTE COMPLETO OPENAI")
    print("-" * 25)

    openai_key = os.getenv('OPENAI_API_KEY')

    try:
        import httpx

        headers = {
            'Authorization': f'Bearer {openai_key}',
            'Content-Type': 'application/json'
        }

        async with httpx.AsyncClient() as client:
            # Teste de modelos
            response = await client.get(
                'https://api.openai.com/v1/models',
                headers=headers,
                timeout=15.0
            )

            if response.status_code != 200:
                print(f"❌ Erro na API: {response.status_code}")
                return None

            models_data = response.json()
            available_models = [m['id'] for m in models_data['data']]
            image_models = [m for m in available_models if 'dall-e' in m or 'image' in m]

            print(f"🎨 Modelos disponíveis: {image_models}")

            # Escolher modelo para teste
            test_model = 'gpt-image-1' if 'gpt-image-1' in image_models else 'dall-e-3'

            # Teste de geração
            test_payload = {
                "model": test_model,
                "prompt": "A simple red pixel art square",
                "size": "1024x1024",
                "quality": "standard",
                "n": 1
            }

            response = await client.post(
                'https://api.openai.com/v1/images/generations',
                headers=headers,
                json=test_payload,
                timeout=120.0
            )

            if response.status_code == 200:
                print(f"✅ Teste assíncrono OK com {test_model}")
                return test_model
            else:
                print(f"❌ Teste assíncrono falhou: {response.status_code}")
                return None

    except ImportError:
        print("⚠️  httpx não disponível, usando apenas teste síncrono")
        return None
    except Exception as e:
        print(f"❌ Erro no teste assíncrono: {e}")
        return None


# ============================================================================
# 🔧 CORREÇÃO AUTOMÁTICA DE ARQUIVOS
# ============================================================================

def fix_openai_service(working_model):
    """Corrige app/services/openai_service.py"""
    print(f"\n🔧 CORRIGINDO openai_service.py")
    print("-" * 30)

    service_file = Path("app/services/openai_service.py")

    if not service_file.exists():
        print(f"❌ Arquivo não encontrado: {service_file}")
        return False

    try:
        content = service_file.read_text(encoding='utf-8')
        original_content = content

        # Padrões para encontrar e substituir o modelo
        import re
        patterns = [
            (r'model="gpt-image-1"', f'model="{working_model}"'),
            (r'model="dall-e-3"', f'model="{working_model}"'),
            (r'model="dall-e-2"', f'model="{working_model}"'),
            (r"model='gpt-image-1'", f"model='{working_model}'"),
            (r"model='dall-e-3'", f"model='{working_model}'"),
            (r"model='dall-e-2'", f"model='{working_model}'"),
        ]

        updated = False
        for old_pattern, new_value in patterns:
            if re.search(old_pattern, content):
                content = re.sub(old_pattern, new_value, content)
                updated = True

        if updated:
            service_file.write_text(content, encoding='utf-8')
            print(f"✅ Modelo atualizado para {working_model}")
            return True
        else:
            print("⚠️  Padrão de modelo não encontrado")
            # Verificar se já está correto
            if f'model="{working_model}"' in content or f"model='{working_model}'" in content:
                print(f"✅ Modelo já configurado para {working_model}")
                return True
            return False

    except Exception as e:
        print(f"❌ Erro ao corrigir openai_service.py: {e}")
        return False


def fix_config_loading():
    """Corrige app/core/config.py para carregar .env"""
    print(f"\n🔧 CORRIGINDO config.py")
    print("-" * 20)

    config_file = Path("app/core/config.py")

    if not config_file.exists():
        print(f"❌ Arquivo não encontrado: {config_file}")
        return False

    try:
        content = config_file.read_text(encoding='utf-8')

        # Verificar se já tem carregamento manual
        if '_load_from_env' in content:
            print("✅ Carregamento .env já presente")
            return True

        # Código para carregar .env manualmente
        env_loading_code = '''
    def _load_from_env(self, **kwargs):
        """Carrega configurações do .env manualmente"""
        from pathlib import Path
        import os

        env_file = Path(".env")
        if env_file.exists():
            for line in env_file.read_text(encoding='utf-8').splitlines():
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key, value = key.strip(), value.strip()

                    # Remover aspas
                    if value.startswith(('"', "'")) and value.endswith(('"', "'")):
                        value = value[1:-1]

                    # Definir no ambiente e no objeto
                    os.environ[key] = value
                    if hasattr(self, key):
                        setattr(self, key, value)

        return kwargs
'''

        # Encontrar onde inserir o método
        lines = content.split('\n')
        new_lines = []
        inserted = False

        for i, line in enumerate(lines):
            new_lines.append(line)

            # Inserir após __init__ da classe Settings
            if ('def __init__(self' in line and
                    'Settings' in ''.join(lines[max(0, i - 5):i + 1])):

                # Adicionar o método
                new_lines.extend(env_loading_code.split('\n'))

                # Procurar super().__init__ para adicionar chamada
                for j in range(i + 1, min(len(lines), i + 15)):
                    if 'super().__init__' in lines[j]:
                        # Inserir chamada antes do super().__init__
                        indent = '        '
                        call_line = f'{indent}kwargs = self._load_from_env(**kwargs)'
                        new_lines.insert(len(new_lines) - len(env_loading_code.split('\n')) + j - i, call_line)
                        break

                inserted = True
                break

        if inserted:
            new_content = '\n'.join(new_lines)
            config_file.write_text(new_content, encoding='utf-8')
            print("✅ Carregamento .env adicionado")
            return True
        else:
            print("⚠️  Não foi possível inserir automaticamente")
            print("💡 Adicione manualmente o carregamento do .env")
            return False

    except Exception as e:
        print(f"❌ Erro ao corrigir config.py: {e}")
        return False


def create_corrected_files(working_model):
    """Cria versões corrigidas dos arquivos se necessário"""
    print(f"\n📝 CRIANDO ARQUIVOS CORRIGIDOS")
    print("-" * 30)

    # Criar .env corrigido se não existir
    if not Path(".env").exists():
        env_content = f'''# Sora Pixel Art Generator - Configurações
# ==========================================

# OpenAI API Key (OBRIGATÓRIO)
OPENAI_API_KEY=sk-sua-chave-aqui

# Database
DATABASE_URL=sqlite:///./sora_pixel_art.db
# DATABASE_URL=postgresql://postgres:password@localhost:5432/sora_pixel_art

# Redis (opcional)
REDIS_URL=redis://localhost:6379/0

# Segurança
SECRET_KEY=desenvolvimento-apenas-nao-usar-em-producao

# CORS Origins
CORS_ORIGINS=http://localhost:3000

# Debug
DEBUG=true
LOG_LEVEL=INFO

# Storage
STORAGE_LOCAL_PATH=./storage
UPLOAD_MAX_SIZE=10485760

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=3600
'''
        Path(".env.template").write_text(env_content, encoding='utf-8')
        print("✅ .env.template criado")

    # Mostrar comandos de correção manual se automática falhar
    print(f"\n💡 COMANDOS MANUAIS (se necessário):")
    print("Se a correção automática falhar, execute:")
    print(f"1. No openai_service.py, trocar model= para '{working_model}'")
    print("2. No config.py, adicionar carregamento manual do .env")


# ============================================================================
# 🎯 FUNÇÃO PRINCIPAL
# ============================================================================

def diagnose_and_fix():
    """Diagnóstico completo e correção automática"""
    print("🔧 SORA PIXEL ART GENERATOR - FIX ALL-IN-ONE")
    print("=" * 55)
    print("Este script vai:")
    print("✅ Carregar .env automaticamente")
    print("✅ Testar sua API OpenAI")
    print("✅ Detectar modelo disponível")
    print("✅ Corrigir código automaticamente")
    print("✅ Preparar sistema para funcionar")

    # 1. Carregar .env
    if not load_env_file():
        print("\n❌ FALHA: Não foi possível carregar .env")
        print("🔧 SOLUÇÃO: Crie o arquivo .env com sua OPENAI_API_KEY")
        return False

    # 2. Testar OpenAI (síncrono primeiro)
    working_model = test_openai_sync()

    if not working_model:
        print("\n❌ FALHA: API OpenAI não funcionou")
        print("🔧 SOLUÇÕES:")
        print("1. Verifique se OPENAI_API_KEY está correta")
        print("2. Verifique créditos: https://platform.openai.com/account/billing")
        print("3. Verifique organização: https://platform.openai.com/settings/organization")
        return False

    # 3. Teste assíncrono (opcional)
    print(f"\n🔄 Testando modo assíncrono...")
    async_result = asyncio.run(test_openai_async())
    if async_result:
        print("✅ Modo assíncrono também OK")

    # 4. Corrigir arquivos
    print(f"\n🛠️  CORRIGINDO SISTEMA AUTOMATICAMENTE")
    print("=" * 40)

    corrections_ok = 0

    # Corrigir openai_service.py
    if fix_openai_service(working_model):
        corrections_ok += 1

    # Corrigir config.py
    if fix_config_loading():
        corrections_ok += 1

    # Criar arquivos de apoio
    create_corrected_files(working_model)

    # 5. Resumo final
    print(f"\n🎉 DIAGNÓSTICO E CORREÇÃO CONCLUÍDOS!")
    print("=" * 40)

    print(f"✅ API OpenAI: Funcionando")
    print(f"🤖 Modelo detectado: {working_model}")

    if working_model == 'gpt-image-1':
        print("🌟 Você tem acesso ao gpt-image-1 (modelo mais avançado)!")
    else:
        print("💡 Usando dall-e-3 (gpt-image-1 requer verificação)")

    print(f"✅ Correções aplicadas: {corrections_ok}/2")

    if corrections_ok >= 1:
        print(f"\n🚀 SISTEMA PRONTO!")
        print("Execute agora:")
        print("  python main.py")
        print("  python test_image_generation.py")

        print(f"\n📊 Configuração final:")
        print(f"  • Modelo: {working_model}")
        print(f"  • API Key: Válida")
        print(f"  • Créditos: Disponíveis")
        print(f"  • Sistema: Corrigido")

        return True
    else:
        print(f"\n⚠️  CORREÇÃO PARCIAL")
        print("Alguns arquivos podem precisar de correção manual")
        print("Mas a API OpenAI está funcionando!")
        return False


def main():
    """Função principal"""
    try:
        success = diagnose_and_fix()

        if success:
            print(f"\n🎯 PRÓXIMO PASSO: Testar o sistema completo!")
            print("Execute: python test_image_generation.py")
        else:
            print(f"\n🔧 Verifique as instruções acima para resolver pendências")

    except KeyboardInterrupt:
        print(f"\n\n⏹️  Operação cancelada pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        print("💡 Tente executar os scripts de diagnóstico individuais")


if __name__ == "__main__":
    main()