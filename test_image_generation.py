#!/usr/bin/env python3
"""
Teste de Geração de Imagens - Sora Pixel Art Generator
=====================================================
Script para testar a criação completa de pixel art
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path

import httpx


class ImageGenerationTest:
    """Classe para testar geração de imagens"""

    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.client = None

    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=300.0)  # 5 minutos timeout
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    async def check_api_health(self):
        """Verifica se a API está funcionando"""
        print("🔍 Verificando status da API...")

        try:
            response = await self.client.get(f"{self.base_url}/health")
            response.raise_for_status()

            health = response.json()
            print(f"✅ API Status: {health['status']}")
            print(f"   Database: {health['services']['database']}")
            print(f"   OpenAI: {health['services']['openai']}")

            if health['services']['openai'] != 'configured':
                print("❌ OpenAI API não configurada!")
                print("   Configure OPENAI_API_KEY no arquivo .env")
                return False

            return True

        except Exception as e:
            print(f"❌ Erro ao verificar API: {e}")
            return False

    async def create_sprite_sheet_test(self):
        """Teste: Criar sprite sheet simples"""
        print("\n🎨 Teste 1: Criando Sprite Sheet")
        print("-" * 50)

        # Parâmetros otimizados para teste rápido
        generation_params = {
            "generation_type": "prompt",
            "prompt": "Uma moeda de ouro girando, pixel art simples",
            "output_format": "sprite_sheet",
            "style": "8-bit",
            "frames": 4,  # Poucos frames para ser rápido
            "frame_width": 32,  # Tamanho pequeno para ser rápido
            "frame_height": 32,
            "animation_type": "custom",
            "fps": 8,
            "background_type": "transparent",
            "pixel_perfect": True
        }

        return await self._run_generation_test("Sprite Sheet", generation_params)

    async def create_individual_frames_test(self):
        """Teste: Criar frames individuais"""
        print("\n🎨 Teste 2: Criando Frames Individuais")
        print("-" * 50)

        generation_params = {
            "generation_type": "prompt",
            "prompt": "Um coração pulsando, pixel art fofo",
            "output_format": "individual_frames",
            "style": "16-bit",
            "frames": 3,  # Apenas 3 frames
            "frame_width": 24,  # Bem pequeno
            "frame_height": 24,
            "animation_type": "idle",
            "fps": 6,
            "background_type": "transparent"
        }

        return await self._run_generation_test("Frames Individuais", generation_params)

    async def create_quick_test(self):
        """Teste ultra-rápido com 1 frame apenas"""
        print("\n⚡ Teste 3: Geração Ultra-Rápida (1 frame)")
        print("-" * 50)

        generation_params = {
            "generation_type": "prompt",
            "prompt": "Uma estrela dourada, pixel art",
            "output_format": "sprite_sheet",
            "style": "8-bit",
            "frames": 1,  # Apenas 1 frame
            "frame_width": 16,  # Muito pequeno
            "frame_height": 16,
            "animation_type": "idle",
            "fps": 12,
            "background_type": "transparent"
        }

        return await self._run_generation_test("Ultra-Rápido", generation_params)

    async def _run_generation_test(self, test_name, params):
        """Executa um teste de geração"""
        try:
            print(f"📝 Prompt: {params['prompt']}")
            print(f"🎯 Output: {params['output_format']}")
            print(f"📐 Frames: {params['frames']} de {params['frame_width']}x{params['frame_height']}")

            # 1. Validar parâmetros primeiro
            print("\n🔍 Validando parâmetros...")
            validation_response = await self.client.post(
                f"{self.base_url}/api/v1/generation/validate",
                json=params
            )

            if validation_response.status_code == 200:
                validation = validation_response.json()["data"]
                if validation["is_valid"]:
                    print("✅ Parâmetros válidos")
                    print(f"⏱️  Tempo estimado: {validation['estimated_time_seconds']} segundos")

                    if validation.get("warnings"):
                        for warning in validation["warnings"]:
                            print(f"⚠️  {warning}")
                else:
                    print("❌ Parâmetros inválidos:")
                    for error in validation["errors"]:
                        print(f"   • {error}")
                    return False

            # 2. Criar geração
            print("\n🚀 Criando geração...")
            start_time = time.time()

            response = await self.client.post(
                f"{self.base_url}/api/v1/generation/create",
                json=params
            )
            response.raise_for_status()

            result = response.json()
            job_id = result["data"]["id"]
            estimated_time = result["data"].get("estimated_time", 60)

            print(f"✅ Job criado: {job_id}")
            print(f"⏱️  Tempo estimado: {estimated_time} segundos")

            # 3. Acompanhar progresso
            print("\n⏳ Acompanhando progresso...")
            final_status = await self._wait_for_completion(job_id, max_wait=600)

            # 4. Resultado final
            end_time = time.time()
            total_time = int(end_time - start_time)

            if final_status and final_status["status"] == "completed":
                print(f"\n🎉 {test_name} concluído com sucesso!")
                print(f"⏱️  Tempo total: {total_time} segundos")
                print(f"📁 Diretório: {final_status['working_directory']}")

                # Verificar arquivos criados
                await self._check_generated_files(job_id, params["output_format"])

                return True
            else:
                print(f"\n❌ {test_name} falhou!")
                if final_status:
                    print(f"   Erro: {final_status.get('error_message', 'Desconhecido')}")
                return False

        except Exception as e:
            print(f"\n❌ Erro no teste {test_name}: {e}")
            return False

    async def _wait_for_completion(self, job_id, max_wait=600):
        """Aguarda conclusão com progresso visual"""
        start_time = time.time()
        last_status = None
        last_progress = -1

        while time.time() - start_time < max_wait:
            try:
                # Obter status atual
                response = await self.client.get(f"{self.base_url}/api/v1/jobs/{job_id}")
                response.raise_for_status()

                job = response.json()["data"]

                # Mostrar progresso apenas se mudou
                if job["status"] != last_status or job["progress"] != last_progress:
                    progress_bar = self._create_progress_bar(job["progress"])
                    print(f"   {progress_bar} {job['status']} - {job['progress']}%")

                    if job.get("current_step"):
                        print(f"   📝 {job['current_step']}")

                    last_status = job["status"]
                    last_progress = job["progress"]

                # Verificar se terminou
                if job["status"] in ["completed", "failed", "cancelled"]:
                    return job

                # Aguardar antes do próximo check
                await asyncio.sleep(3)

            except Exception as e:
                print(f"   ⚠️  Erro ao verificar status: {e}")
                await asyncio.sleep(5)

        print(f"   ⏱️  Timeout após {max_wait} segundos")
        return None

    def _create_progress_bar(self, progress, width=20):
        """Cria barra de progresso visual"""
        filled = int(width * progress / 100)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}]"

    async def _check_generated_files(self, job_id, output_format):
        """Verifica arquivos gerados"""
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/jobs/{job_id}/files")

            if response.status_code == 200:
                files_info = response.json()["data"]
                print(f"\n📂 Arquivos gerados:")

                if files_info.get("preview_gif"):
                    print(f"   🎬 Preview: http://localhost:8000{files_info['preview_gif']}")

                if output_format == "sprite_sheet":
                    print(f"   🖼️  Sprite sheet disponível")
                elif output_format == "individual_frames":
                    print(f"   📦 Frames individuais + ZIP disponível")

                # Verificar arquivos no diretório local
                working_dir = Path(files_info.get("working_directory", ""))
                if working_dir.exists():
                    files = list(working_dir.glob("*"))
                    print(f"   📁 {len(files)} arquivos no diretório local")

                    for file in files[:5]:  # Mostrar apenas os primeiros 5
                        size_kb = file.stat().st_size / 1024
                        print(f"      • {file.name} ({size_kb:.1f} KB)")

                    if len(files) > 5:
                        print(f"      • ... e mais {len(files) - 5} arquivos")

        except Exception as e:
            print(f"   ⚠️  Erro ao verificar arquivos: {e}")

    async def run_all_tests(self):
        """Executa todos os testes"""
        print("🧪 Sora Pixel Art Generator - Teste de Geração de Imagens")
        print("=" * 70)
        print(f"📅 Início: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Verificar API
        if not await self.check_api_health():
            print("\n❌ API não está funcionando. Execute: python main.py")
            return

        # Confirmar com usuário
        print("\n⚠️  ATENÇÃO: Este teste irá usar a OpenAI API")
        print("   Isso consumirá créditos da sua conta OpenAI")
        print("   Custo estimado: $0.10 - $0.30 USD")

        response = input("\n🤔 Continuar com os testes? [y/N]: ")
        if response.lower() not in ['y', 'yes', 's', 'sim']:
            print("⏭️  Testes cancelados pelo usuário")
            return

        # Executar testes
        results = []

        # Teste rápido primeiro
        print(f"\n{'=' * 70}")
        result1 = await self.create_quick_test()
        results.append(("Ultra-Rápido (1 frame)", result1))

        if result1:
            # Se o primeiro teste passou, continuar
            print(f"\n{'=' * 70}")
            result2 = await self.create_sprite_sheet_test()
            results.append(("Sprite Sheet", result2))

            print(f"\n{'=' * 70}")
            result3 = await self.create_individual_frames_test()
            results.append(("Frames Individuais", result3))
        else:
            print("\n⏭️  Pulando outros testes devido à falha no primeiro")

        # Resumo final
        print(f"\n{'=' * 70}")
        print("📊 RESUMO DOS TESTES")
        print("-" * 30)

        passed = 0
        for test_name, success in results:
            status = "✅ PASSOU" if success else "❌ FALHOU"
            print(f"{test_name:20} {status}")
            if success:
                passed += 1

        print(f"\n🎯 Resultado: {passed}/{len(results)} testes passaram")

        if passed == len(results):
            print("🎉 Todos os testes passaram! A API está funcionando perfeitamente.")
            print("\n📚 Próximos passos:")
            print("   • Acesse http://localhost:8000/docs para documentação completa")
            print("   • Execute python example_usage.py para mais exemplos")
            print("   • Integre com seu frontend ou aplicação")
        elif passed > 0:
            print("⚠️  Alguns testes passaram. Verifique os logs para problemas.")
        else:
            print("❌ Todos os testes falharam. Verifique:")
            print("   • Configuração da OPENAI_API_KEY")
            print("   • Conexão com a internet")
            print("   • Logs do servidor (terminal onde executou python main.py)")

        print(f"\n📅 Fim: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


async def main():
    """Função principal"""
    try:
        async with ImageGenerationTest() as tester:
            await tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n\n⏸️  Testes cancelados pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())