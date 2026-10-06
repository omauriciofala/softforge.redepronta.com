#!/usr/bin/env python3
"""SoftForge — Script Unificado de Migrações do Banco de Dados (Alembic).

Facilita o gerenciamento de migrações assíncronas no PostgreSQL para
desenvolvedores humanos e Agentes Autônomos de IA.

Uso:
    python tools/scripts/migrate.py makemigrations "descricao_da_migracao"
    python tools/scripts/migrate.py upgrade
    python tools/scripts/migrate.py downgrade -1
    python tools/scripts/migrate.py current
    python tools/scripts/migrate.py history
    python tools/scripts/migrate.py sql
"""

import argparse
import subprocess
import sys
from pathlib import Path


def get_paths() -> tuple[Path, Path, Path]:
    """Retorna caminhos canônicos do monorepo."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    api_dir = repo_root / "apps" / "api"
    alembic_ini = api_dir / "alembic.ini"

    # Detecta executável do Python dentro do virtualenv
    if sys.platform == "win32":
        python_bin = api_dir / ".venv" / "Scripts" / "python.exe"
    else:
        python_bin = api_dir / ".venv" / "bin" / "python"

    if not python_bin.exists():
        python_bin = Path(sys.executable)

    return repo_root, api_dir, alembic_ini, python_bin


def run_alembic_command(args: list[str]) -> int:
    """Executa o comando alembic apontando explicitamente para apps/api/alembic.ini."""
    repo_root, api_dir, alembic_ini, python_bin = get_paths()

    if not alembic_ini.exists():
        print(f"[ERRO] Arquivo de configuração não encontrado: {alembic_ini}", file=sys.stderr)
        return 1

    cmd = [
        str(python_bin),
        "-m",
        "alembic",
        "-c",
        str(alembic_ini),
        *args,
    ]

    print(f"[*] Executando Alembic: {' '.join(args)}")
    result = subprocess.run(cmd, cwd=str(repo_root))
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(
        description="SoftForge Database Migration Helper (Alembic + PostgreSQL)",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # makemigrations
    make_parser = subparsers.add_parser(
        "makemigrations",
        help="Gera uma nova revisão de migração baseada nas alterações dos models.py das fatias",
    )
    make_parser.add_argument("message", help="Descrição sucinta das alterações de schema")

    # upgrade
    upgrade_parser = subparsers.add_parser(
        "upgrade",
        help="Aplica as migrações pendentes no banco de dados até a revisão especificada (padrão: head)",
    )
    upgrade_parser.add_argument("revision", nargs="?", default="head", help="Revisão alvo (padrão: head)")

    # downgrade
    downgrade_parser = subparsers.add_parser(
        "downgrade",
        help="Reverte migrações aplicadas no banco de dados (ex: -1)",
    )
    downgrade_parser.add_argument("revision", nargs="?", default="-1", help="Alvo de reversão (padrão: -1)")

    # current
    subparsers.add_parser(
        "current",
        help="Exibe a revisão de migração atualmente aplicada no banco de dados",
    )

    # history
    subparsers.add_parser(
        "history",
        help="Exibe o histórico cronológico de todas as migrações registradas",
    )

    # sql
    subparsers.add_parser(
        "sql",
        help="Gera e exibe o SQL puro das migrações offline sem conectar no banco",
    )

    args = parser.parse_args()

    if args.command == "makemigrations":
        return run_alembic_command(["revision", "--autogenerate", "-m", args.message])
    elif args.command == "upgrade":
        return run_alembic_command(["upgrade", args.revision])
    elif args.command == "downgrade":
        return run_alembic_command(["downgrade", args.revision])
    elif args.command == "current":
        return run_alembic_command(["current"])
    elif args.command == "history":
        return run_alembic_command(["history"])
    elif args.command == "sql":
        return run_alembic_command(["upgrade", "head", "--sql"])

    return 0


if __name__ == "__main__":
    sys.exit(main())
