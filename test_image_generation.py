#!/usr/bin/env python3
"""
🧪 Teste de Geração de Imagens - VERSÃO CORRIGIDA
================================================
Teste completo do sistema Sora Pixel Art Generator
CORRIGIDO: Parâmetros corretos e testes robustos
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path

import httpx
import structlog

# Configurar logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="ISO"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.WriteLoggerFactory(),
    wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO level
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Configuração da API
API_BASE_URL = "http://localhost:8000"


class TestImageGeneration:
    """Classe para testes de geração de imagens"""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=300.0)  # 5 minutos timeout
        self.results = []
        self.start_time = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def check_api_health(self):
        """Verifica se a API está funcionando"""
        print("🔍 Verificando status da API...")

        try:
            response = await self.client.get(f"{API_BASE_URL}/health")

            if response.status_code == 200:
                health_data = response.json()
                print("✅ API Status: healthy")

                services = health_data.get('services', {})
                print(f"   Database: {services.get('database', 'unknown')}")
                print(f"   OpenAI: {services.get('openai', 'unknown')}")

                return True
            else:
                print(f"❌ API não saudável: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Erro ao conectar com API: {e}")
            print("💡 Certifique-se que 'python main.py' está rodando")
            return False

    async def test_generation_limits(self):
        """Testa os limites do sistema"""
        print("\n📏 Verificando limites do sistema...")

        try:
            response = await self.client.get(f"{API_BASE_URL}/api/v1/generation/limits")

            if response.status_code == 200:
                limits = response.json().get('data', {})
                print("✅ Limites obtidos:")
                print(f"   Frames: {limits.get('frames', {}).get('min')}-{limits.get('frames', {}).get('max')}")
                print(
                    f"   Tamanho: {limits.get('frame_size', {}).get('min_width')}x{limits.get('frame_size', {}).get('min_height')} até {limits.get('frame_size', {}).get('max_width')}x{limits.get('frame_size', {}).get('max_height')}")
                return True
            else:
                print("⚠️  Não foi possível obter limites")
                return True  # Não crítico

        except Exception as e:
            print(f"⚠️  Erro ao obter limites: {e}")
            return True  # Não crítico

    async def validate_generation_params(self, test_data):
        """Valida parâmetros de geração"""
        print(f"🔍 Validando parâmetros...")

        try:
            response = await self.client.post(
                f"{API_BASE_URL}/api/v1/generation/validate",
                json=test_data
            )

            if response.status_code == 200:
                validation = response.json().get('data', {})

                if validation.get('is_valid'):
                    print("✅ Parâmetros válidos")
                    estimated_time = validation.get('estimated_time_seconds', 0)
                    print(f"⏱️  Tempo estimado: {estimated_time} segundos")
                    return True
                else:
                    print("❌ Parâmetros inválidos:")
                    for error in validation.get('errors', []):
                        print(f"   • {error}")
                    return False
            else:
                print(f"❌ Erro na validação: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Erro na validação: {e}")
            return False

    async def create_generation(self, test_data, test_name):
        """Cria uma nova geração"""
        print(f"🚀 Criando geração...")

        try:
            response = await self.client.post(
                f"{API_BASE_URL}/api/v1/generation/create",
                json=test_data
            )

            if response.status_code in [200, 201]:
                result = response.json()
                job_data = result.get('data', {})
                job_id = job_data.get('id')

                if job_id:
                    print(f"✅ Job criado: {job_id}")
                    return job_id
                else:
                    print("❌ Job ID não retornado")
                    return None
            else:
                print(f"❌ Erro na criação: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Detalhes: {error_data.get('detail', 'Erro desconhecido')}")
                except:
                    print(f"   Resposta: {response.text[:200]}")
                return None

        except Exception as e:
            print(f"❌ Erro na criação: {e}")
            return None

    async def monitor_job_progress(self, job_id, test_name, max_wait_time=300):
        """Monitora progresso do job"""
        print(f"⏳ Monitorando progresso do job {job_id}...")

        start_time = time.time()
        last_status = None
        last_progress = -1

        while time.time() - start_time < max_wait_time:
            try:
                response = await self.client.get(f"{API_BASE_URL}/api/v1/jobs/{job_id}")

                if response.status_code == 200:
                    job_data = response.json().get('data', {})
                    status = job_data.get('status')
                    progress = job_data.get('progress', 0)
                    current_step = job_data.get('current_step', '')

                    # Mostrar progresso apenas se mudou
                    if status != last_status or progress != last_progress:
                        print(f"   Status: {status} ({progress}%) - {current_step}")
                        last_status = status
                        last_progress = progress

                    # Verificar se terminou
                    if status == 'completed':
                        elapsed = time.time() - start_time
                        print(f"✅ Job concluído em {elapsed:.1f}s")

                        # Verificar arquivos gerados
                        output_format = job_data.get('output_format')
                        preview_gif_url = job_data.get('preview_gif_url')

                        print(f"   Formato: {output_format}")
                        if preview_gif_url:
                            print(f"   Preview: {preview_gif_url}")

                        return {
                            'success': True,
                            'job_data': job_data,
                            'elapsed_time': elapsed
                        }

                    elif status == 'failed':
                        error_message = job_data.get('error_message', 'Erro desconhecido')
                        print(f"❌ Job falhou: {error_message}")
                        return {
                            'success': False,
                            'error': error_message,
                            'job_data': job_data
                        }

                    # Aguardar antes da próxima verificação
                    await asyncio.sleep(2)

                else:
                    print(f"❌ Erro ao verificar status: {response.status_code}")
                    await asyncio.sleep(5)

            except Exception as e:
                print(f"❌ Erro no monitoramento: {e}")
                await asyncio.sleep(5)

        print(f"⏰ Timeout após {max_wait_time}s")
        return {
            'success': False,
            'error': 'Timeout',
            'elapsed_time': max_wait_time
        }

    async def run_test(self, test_config):
        """Executa um teste completo"""
        test_name = test_config['name']
        test_data = test_config['data']

        print(f"\n{'=' * 50}")
        print(f"⚡ Teste {test_config.get('number', '?')}: {test_name}")
        print(f"{'=' * 50}")
        print(f"📝 Prompt: {test_data['prompt']}")
        print(f"🎯 Output: {test_data['output_format']}")
        print(f"📐 Frames: {test_data['frames']} de {test_data['frame_width']}x{test_data['frame_height']}")

        # 1. Validar parâmetros
        if not await self.validate_generation_params(test_data):
            return {'success': False, 'error': 'Validação falhou', 'test_name': test_name}

        # 2. Criar geração
        job_id = await self.create_generation(test_data, test_name)
        if not job_id:
            return {'success': False, 'error': 'Criação falhou', 'test_name': test_name}

        # 3. Monitorar progresso
        result = await self.monitor_job_progress(job_id, test_name)
        result['test_name'] = test_name
        result['job_id'] = job_id

        return result

    async def run_all_tests(self):
        """Executa todos os testes"""
        self.start_time = datetime.now()

        print("🧪 Sora Pixel Art Generator - Teste de Geração de Imagens")
        print("=" * 70)
        print(f"📅 Início: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        # Verificar API
        if not await self.check_api_health():
            print("\n❌ API não está funcionando. Certifique-se que 'python main.py' está rodando.")
            return

        # Verificar limites
        await self.test_generation_limits()

        # Configurações de teste
        test_configs = [
            {
                'number': 1,
                'name': 'Ultra-Rápido (1 frame)',
                'data': {
                    'generation_type': 'prompt',
                    'prompt': 'Uma estrela dourada, pixel art',
                    'output_format': 'sprite_sheet',
                    'style': '8-bit',
                    'frames': 1,
                    'frame_width': 16,
                    'frame_height': 16,
                    'animation_type': 'idle',
                    'fps': 12,
                    'pixel_perfect': True,
                    'motion_intensity': 50
                }
            },
            {
                'number': 2,
                'name': 'Sprite Sheet Clássico',
                'data': {
                    'generation_type': 'prompt',
                    'prompt': 'Um cavaleiro medieval caminhando, pixel art',
                    'output_format': 'sprite_sheet',
                    'style': '16-bit',
                    'frames': 4,
                    'frame_width': 32,
                    'frame_height': 32,
                    'animation_type': 'walk_cycle',
                    'fps': 8,
                    'pixel_perfect': True,
                    'motion_intensity': 70
                }
            },
            {
                'number': 3,
                'name': 'Frames Individuais',
                'data': {
                    'generation_type': 'prompt',
                    'prompt': 'Um dragão voando, estilo pixel art',
                    'output_format': 'individual_frames',
                    'style': '8-bit',
                    'frames': 3,
                    'frame_width': 64,
                    'frame_height': 64,
                    'animation_type': 'custom',
                    'fps': 10,
                    'pixel_perfect': True,
                    'motion_intensity': 80
                }
            }
        ]

        # Verificar se usuário quer continuar
        print(f"\n⚠️  ATENÇÃO: Este teste irá usar a OpenAI API")
        print(f"   Isso consumirá créditos da sua conta OpenAI")
        print(f"   Custo estimado: $0.10 - $0.50 USD")

        try:
            user_input = input("\n🤔 Continuar com os testes? [y/N]: ").strip().lower()
            if user_input not in ['y', 'yes', 'sim', 's']:
                print("⏹️  Testes cancelados pelo usuário")
                return
        except KeyboardInterrupt:
            print("\n⏹️  Testes cancelados")
            return

        # Executar testes
        print("\n" + "=" * 70)

        for test_config in test_configs:
            try:
                result = await self.run_test(test_config)
                self.results.append(result)

                if result['success']:
                    print(f"✅ {test_config['name']} PASSOU")
                    if 'elapsed_time' in result:
                        print(f"   ⏱️  Tempo: {result['elapsed_time']:.1f}s")
                    if 'job_id' in result:
                        print(f"   🎯 Job ID: {result['job_id']}")
                else:
                    print(f"❌ {test_config['name']} FALHOU")
                    print(f"   ❌ Erro: {result.get('error', 'Desconhecido')}")

                    # Se primeiro teste falhar, perguntar se continua
                    if test_config['number'] == 1:
                        print("\n⏭️  Pulando outros testes devido à falha no primeiro")
                        break

            except KeyboardInterrupt:
                print(f"\n⏹️  Teste {test_config['name']} cancelado")
                break
            except Exception as e:
                print(f"❌ Erro no teste {test_config['name']}: {e}")
                self.results.append({
                    'success': False,
                    'error': str(e),
                    'test_name': test_config['name']
                })

        # Resumo final
        await self.print_summary()

    async def print_summary(self):
        """Imprime resumo dos testes"""
        end_time = datetime.now()
        duration = end_time - self.start_time

        print("\n" + "=" * 70)
        print("📊 RESUMO DOS TESTES")
        print("-" * 30)

        passed = sum(1 for r in self.results if r.get('success'))
        total = len(self.results)

        for result in self.results:
            status = "✅ PASSOU" if result.get('success') else "❌ FALHOU"
            test_name = result.get('test_name', 'Desconhecido')
            print(f"{test_name} {status}")

            if not result.get('success') and 'error' in result:
                print(f"   └─ {result['error']}")

        print(f"\n🎯 Resultado: {passed}/{total} testes passaram")

        if passed == total and total > 0:
            print("🎉 Todos os testes passaram! Sistema funcionando perfeitamente!")
        elif passed > 0:
            print(f"⚠️  {total - passed} teste(s) falharam, mas alguns funcionaram")
        else:
            print("❌ Todos os testes falharam. Verifique:")
            print("   • Configuração da OPENAI_API_KEY")
            print("   • Conexão com a internet")
            print("   • Logs do servidor (terminal onde executou python main.py)")

        print(f"\n📅 Fim: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️  Duração total: {duration.total_seconds():.1f}s")


async def main():
    """Função principal"""
    try:
        async with TestImageGeneration() as tester:
            await tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n\n⏹️  Testes interrompidos pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro geral nos testes: {e}")
        logger.error("Test execution failed", error=str(e))


if __name__ == "__main__":
    print("🚀 Executando: test_image_generation.py")
    print("-" * 50)
    asyncio.run(main())