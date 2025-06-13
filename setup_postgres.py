#!/usr/bin/env python3
"""
Setup PostgreSQL para Sora Pixel Art Generator
==============================================
Script para configurar e testar PostgreSQL
"""

import sys
import asyncio
from pathlib import Path


def check_postgresql_dependencies():
    """Verifica se as dependências do PostgreSQL estão instaladas"""
    print("🔍 Verificando dependências PostgreSQL...")

    missing_deps = []

    try:
        import asyncpg
        print("✅ asyncpg instalado")
    except ImportError:
        missing_deps.append("asyncpg")

    try:
        import psycopg2
        print("✅ psycopg2 instalado")
    except ImportError:
        missing_deps.append("psycopg2-binary")

    if missing_deps:
        print(f"\n❌ Dependências faltando: {', '.join(missing_deps)}")
        print("💡 Para instalar:")
        print(f"   pip install {' '.join(missing_deps)}")
        return False

    return True


async def test_database_connection():
    """Testa conexão com o banco PostgreSQL"""
    print("\n🔌 Testando conexão com PostgreSQL...")

    try:
        from app.core.config import get_settings
        settings = get_settings()

        database_url = settings.DATABASE_URL
        print(f"📝 URL do banco: {database_url}")

        # Extrair informações da URL
        if "postgresql://" in database_url:
            # postgresql://user:password@host:port/database
            url_parts = database_url.replace("postgresql://", "").split("/")
            connection_part = url_parts[0]
            database_name = url_parts[1] if len(url_parts) > 1 else "postgres"

            if "@" in connection_part:
                auth_part, host_part = connection_part.split("@")
                if ":" in auth_part:
                    username, password = auth_part.split(":", 1)
                else:
                    username = auth_part
                    password = ""

                if ":" in host_part:
                    host, port = host_part.split(":")
                    port = int(port)
                else:
                    host = host_part
                    port = 5432
            else:
                username = "postgres"
                password = ""
                host = "localhost"
                port = 5432

            print(f"   Host: {host}:{port}")
            print(f"   Database: {database_name}")
            print(f"   Username: {username}")

        # Testar conexão com asyncpg
        import asyncpg

        try:
            # Conectar ao banco
            conn = await asyncpg.connect(database_url)

            # Executar query simples
            result = await conn.fetchval("SELECT version()")
            print(f"✅ Conexão PostgreSQL OK!")
            print(f"   Versão: {result.split()[1] if result else 'Desconhecida'}")

            # Fechar conexão
            await conn.close()
            return True

        except asyncpg.InvalidCatalogNameError:
            print(f"❌ Banco de dados '{database_name}' não existe")
            print("💡 Crie o banco no pgAdmin:")
            print(f"   1. Abra pgAdmin4")
            print(f"   2. Conecte ao servidor PostgreSQL")
            print(f"   3. Clique com botão direito em 'Databases'")
            print(f"   4. Selecione 'Create' > 'Database...'")
            print(f"   5. Nome: {database_name}")
            print(f"   6. Owner: {username}")
            return False

        except asyncpg.InvalidPasswordError:
            print(f"❌ Senha incorreta para usuário '{username}'")
            print("💡 Verifique a senha no arquivo .env")
            return False

        except asyncpg.ConnectionDoesNotExistError:
            print(f"❌ Não foi possível conectar ao PostgreSQL em {host}:{port}")
            print("💡 Verifique se:")
            print("   1. PostgreSQL está rodando")
            print("   2. Porta está correta (padrão: 5432)")
            print("   3. Firewall permite conexões")
            return False

    except Exception as e:
        print(f"❌ Erro ao testar conexão: {e}")
        return False


async def create_database_tables():
    """Cria tabelas no banco de dados"""
    print("\n📊 Criando tabelas do banco...")

    try:
        from app.core.database import create_tables
        await create_tables()
        print("✅ Tabelas criadas com sucesso!")
        return True

    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        return False


def show_postgresql_config_help():
    """Mostra ajuda para configuração do PostgreSQL"""
    print("\n📚 Guia de Configuração PostgreSQL")
    print("=" * 50)

    print("\n1️⃣ **Instalação PostgreSQL** (se ainda não instalado):")
    print("   • Windows: https://www.postgresql.org/download/windows/")
    print("   • macOS: brew install postgresql")
    print("   • Ubuntu: sudo apt install postgresql postgresql-contrib")

    print("\n2️⃣ **Configuração Inicial:**")
    print("   • Instale pgAdmin4 para interface gráfica")
    print("   • Configure senha do usuário 'postgres'")
    print("   • Anote a porta (padrão: 5432)")

    print("\n3️⃣ **Criar Banco de Dados:**")
    print("   • Abra pgAdmin4")
    print("   • Conecte ao servidor PostgreSQL local")
    print("   • Clique com botão direito em 'Databases'")
    print("   • Selecione 'Create' > 'Database...'")
    print("   • Nome: sora_pixel_art")
    print("   • Owner: postgres")

    print("\n4️⃣ **Configurar .env:**")
    print("   DATABASE_URL=postgresql://usuario:senha@localhost:5432/sora_pixel_art")
    print("   \n   Exemplos:")
    print("   • DATABASE_URL=postgresql://postgres:admin@localhost:5432/sora_pixel_art")
    print("   • DATABASE_URL=postgresql://postgres:postgres@localhost:5432/sora_pixel_art")

    print("\n5️⃣ **Testar Configuração:**")
    print("   python setup_postgres.py")


async def main():
    """Função principal do setup PostgreSQL"""
    print("🐘 Sora Pixel Art Generator - Setup PostgreSQL")
    print("=" * 60)

    # Verificar dependências
    if not check_postgresql_dependencies():
        print("\n❌ Instale as dependências antes de continuar")
        return

    # Verificar se arquivo .env existe
    env_file = Path(".env")
    if not env_file.exists():
        print("\n❌ Arquivo .env não encontrado")
        print("💡 Crie o arquivo .env com as configurações do PostgreSQL")
        show_postgresql_config_help()
        return

    # Testar conexão
    connection_ok = await test_database_connection()

    if connection_ok:
        print("\n🎯 Conexão PostgreSQL estabelecida!")

        # Criar tabelas
        tables_ok = await create_database_tables()

        if tables_ok:
            print("\n🎉 Setup PostgreSQL concluído com sucesso!")
            print("\n🚀 Próximos passos:")
            print("   1. python main.py                  # Iniciar servidor")
            print("   2. python teste_basico.py          # Testar API")
            print("   3. http://localhost:8000/docs      # Documentação")
        else:
            print("\n❌ Erro ao criar tabelas")
    else:
        print("\n❌ Falha na conexão PostgreSQL")
        show_postgresql_config_help()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏸️  Setup cancelado pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        import traceback

        traceback.print_exc()