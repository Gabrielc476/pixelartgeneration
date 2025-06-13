#!/usr/bin/env python3
"""
Menu Interativo de Testes - Sora Pixel Art Generator
===================================================
Interface amigável para executar todos os tipos de teste
"""

import asyncio
import os
import subprocess
import sys
from pathlib import Path


class TestMenu:
    """Menu interativo para testes"""

    def __init__(self):
        self.test_scripts = {
            "1": {
                "name": "🔑 Teste de Configuração OpenAI",
                "script": "test_openai.py",
                "description": "Verifica se OpenAI está configurada corretamente",
                "cost": "~$0.04 (opcional)",
                "time": "1-2 min"
            },
            "2": {
                "name": "🎭 Teste Simulado (Mock)",
                "script": "mock_test.py",
                "description": "Teste completo SEM usar OpenAI (gratuito)",
                "cost": "GRÁTIS",
                "time": "10 seg"
            },
            "3": {
                "name": "⚡ Teste Rápido",
                "script": "quick_test.py",
                "description": "1 frame pequeno para validação rápida",
                "cost": "~$0.04",
                "time": "1-2 min"
            },
            "4": {
                "name": "🎨 Teste Completo",
                "script": "test_image_generation.py",
                "description": "Múltiplos testes abrangentes",
                "cost": "~$0.20-0.40",
                "time": "5-8 min"
            },
            "5": {
                "name": "📊 Status da API",
                "script": "health_check",
                "description": "Verifica se a API local está funcionando",
                "cost": "GRÁTIS",
                "time": "5 seg"
            },
            "6": {
                "name": "🧪 Teste Básico da API",
                "script": "teste_basico.py",
                "description": "Testa endpoints básicos sem geração",
                "cost": "GRÁTIS",
                "time": "30 seg"
            }
        }

    def show_header(self):
        """Mostra cabeçalho do menu"""
        print("🎨 Sora Pixel Art Generator - Menu de Testes")
        print("=" * 55)
        print("Escolha o tipo de teste que deseja executar:\n")

    def show_menu(self):
        """Mostra opções do menu"""
        for key, test in self.test_scripts.items():
            print(f"{key}. {test['name']}")
            print(f"   📝 {test['description']}")
            print(f"   💰 Custo: {test['cost']} | ⏱️ Tempo: {test['time']}")
            print()

        print("0. ❌ Sair")
        print("-" * 55)

    def show_recommendations(self):
        """Mostra recomendações de uso"""
        print("💡 RECOMENDAÇÕES:")
        print("   🥇 Primeira vez: Execute opção 1 (Configuração)")
        print("   🔧 Desenvolvimento: Use opção 2 (Mock - grátis)")
        print("   ⚡ Validação rápida: Use opção 3 (Teste rápido)")
        print("   🎯 Validação completa: Use opção 4 (Teste completo)")
        print()

    async def check_api_status(self):
        """Verifica status da API local"""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("http://localhost:8000/health")
                if response.status_code == 200:
                    health = response.json()
                    print("✅ API Local: Funcionando")
                    print(f"   🔗 Status: {health['status']}")
                    print(f"   🗄️ Database: {health['services']['database']}")
                    print(f"   🔑 OpenAI: {health['services']['openai']}")
                    return True
                else:
                    print(f"⚠️ API Local: HTTP {response.status_code}")
                    return False
        except Exception:
            print("❌ API Local: Não está rodando")
            print("   💡 Execute: python main.py")
            return False

    def check_dependencies(self):
        """Verifica dependências necessárias"""
        print("🔍 Verificando dependências...")

        missing = []
        deps = [
            ("httpx", "httpx"),
            ("openai", "openai"),
            ("PIL", "Pillow")
        ]

        for import_name, package_name in deps:
            try:
                __import__(import_name)
                print(f"   ✅ {package_name}")
            except ImportError:
                missing.append(package_name)
                print(f"   ❌ {package_name}")

        if missing:
            print(f"\n💡 Para instalar dependências faltando:")
            print(f"   pip install {' '.join(missing)}")
            return False

        return True

    def check_files(self):
        """Verifica arquivos necessários"""
        print("\n📁 Verificando arquivos...")

        files_to_check = [
            (".env", "Arquivo de configuração"),
            ("main.py", "Servidor principal"),
            ("app/", "Diretório da aplicação")
        ]

        all_good = True
        for file_path, description in files_to_check:
            if Path(file_path).exists():
                print(f"   ✅ {description}: {file_path}")
            else:
                print(f"   ❌ {description}: {file_path} não encontrado")
                all_good = False

        # Verificar .env especificamente
        env_file = Path(".env")
        if env_file.exists():
            content = env_file.read_text()
            if "OPENAI_API_KEY=" in content and "your_openai_api_key_here" not in content:
                print("   ✅ OpenAI API Key: Configurada")
            else:
                print("   ⚠️ OpenAI API Key: Não configurada")

        return all_good

    async def run_health_check(self):
        """Executa verificação de saúde"""
        print("🏥 Verificação de Saúde do Sistema")
        print("-" * 40)

        # Verificar dependências
        deps_ok = self.check_dependencies()

        # Verificar arquivos
        files_ok = self.check_files()

        # Verificar API
        api_ok = await self.check_api_status()

        print(f"\n📊 RESUMO:")
        print(f"   Dependências: {'✅' if deps_ok else '❌'}")
        print(f"   Arquivos: {'✅' if files_ok else '❌'}")
        print(f"   API Local: {'✅' if api_ok else '❌'}")

        if deps_ok and files_ok and api_ok:
            print("\n🎉 Sistema totalmente funcionando!")
        elif not api_ok:
            print("\n💡 Execute 'python main.py' para iniciar a API")
        else:
            print("\n⚠️ Há problemas no sistema")

    def run_script(self, script_name):
        """Executa um script de teste"""
        if script_name == "health_check":
            asyncio.run(self.run_health_check())
            return

        script_path = Path(script_name)
        if not script_path.exists():
            print(f"❌ Script não encontrado: {script_name}")
            print("💡 Certifique-se de estar no diretório correto")
            return

        print(f"🚀 Executando: {script_name}")
        print("-" * 50)

        try:
            result = subprocess.run([sys.executable, script_name], capture_output=False)
            print("-" * 50)
            if result.returncode == 0:
                print(f"✅ {script_name} executado com sucesso!")
            else:
                print(f"❌ {script_name} terminou com erro (código {result.returncode})")
        except Exception as e:
            print(f"❌ Erro ao executar {script_name}: {e}")

    async def run_menu(self):
        """Executa o menu principal"""
        while True:
            print("\n" + "=" * 55)
            self.show_header()
            self.show_recommendations()
            self.show_menu()

            try:
                choice = input("Digite sua escolha (0-6): ").strip()

                if choice == "0":
                    print("\n👋 Até logo!")
                    break
                elif choice in self.test_scripts:
                    test_info = self.test_scripts[choice]
                    print(f"\n🎯 Você escolheu: {test_info['name']}")
                    print(f"📝 {test_info['description']}")
                    print(f"💰 Custo: {test_info['cost']}")

                    if "GRÁTIS" not in test_info['cost']:
                        confirm = input("\n⚠️ Este teste pode consumir créditos OpenAI. Continuar? [y/N]: ")
                        if confirm.lower() not in ['y', 'yes', 's', 'sim']:
                            print("⏭️ Teste cancelado")
                            continue

                    print(f"\n⏳ Executando {test_info['name']}...")
                    self.run_script(test_info['script'])

                    input("\n📱 Pressione Enter para voltar ao menu...")
                else:
                    print("❌ Opção inválida. Digite um número de 0 a 6.")

            except KeyboardInterrupt:
                print("\n\n⏸️ Menu cancelado pelo usuário")
                break
            except Exception as e:
                print(f"\n❌ Erro inesperado: {e}")


def show_welcome():
    """Mostra mensagem de boas-vindas"""
    print("🎨 Bem-vindo ao Sora Pixel Art Generator!")
    print()
    print("Este menu permite testar facilmente todas as funcionalidades:")
    print("• 🔧 Verificar configuração")
    print("• 🎭 Testar sem gastar créditos (mock)")
    print("• ⚡ Validações rápidas")
    print("• 🎨 Testes completos")
    print()


async def main():
    """Função principal"""
    try:
        show_welcome()
        menu = TestMenu()
        await menu.run_menu()
    except KeyboardInterrupt:
        print("\n\n⏸️ Programa cancelado pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")


if __name__ == "__main__":
    asyncio.run(main())