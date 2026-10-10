"""SoftForge — Assistente de Engenharia Reversa e Quarentena de Código Legado.

Utilitário para inicializar áreas de análise segura em `staging/`, auditar
fatias migradas e garantir que nenhum código ou elemento de UI legado polua o framework.
"""

import argparse
import os
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Lista de bibliotecas/frameworks estritamente proibidos de serem importados
PROHIBITED_BACKEND_IMPORTS = [
    "django",
    "flask",
    "express",
    "prisma",
    "typeorm",
    "peewee",
    "tortoise",
    "pymongo",
    "bottle",
    "falcon",
    "fastify",
]

PROHIBITED_FRONTEND_IMPORTS = [
    "bootstrap",
    "antd",
    "@mui",
    "material-ui",
    "@chakra-ui",
    "jquery",
    "semantic-ui",
    "bulma",
    "foundation-sites",
]


def get_root_dir() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def init_staging_workspace(name: str) -> None:
    system_name = re.sub(r"[^a-zA-Z0-9_-]", "", name.strip().lower())
    if not system_name:
        print("[ERRO] Nome do sistema inválido. Use caracteres alfanuméricos.")
        sys.exit(1)

    root_dir = get_root_dir()
    staging_dir = root_dir / "staging"
    project_dir = staging_dir / system_name
    source_dir = project_dir / "source"
    template_path = staging_dir / "TEMPLATE_EXTRACTION.md"

    if project_dir.exists():
        print(f"⚠️ A pasta de quarentena '{system_name}' já existe em: {project_dir}")
        return

    os.makedirs(source_dir, exist_ok=True)

    # Criação de .gitignore local de proteção em profundidade
    local_gitignore = project_dir / ".gitignore"
    with open(local_gitignore, "w", encoding="utf-8") as f:
        f.write("# Isolamento estrito de quarentena\n*\n!.gitignore\n!EXTRACTION_SPEC.md\n")

    # Geração de EXTRACTION_SPEC.md a partir do template
    spec_path = project_dir / "EXTRACTION_SPEC.md"
    if template_path.exists():
        with open(template_path, "r", encoding="utf-8") as f:
            template_content = f.read()

        target_slice = system_name.replace("-", "_")
        spec_content = template_content.replace("{SYSTEM_NAME}", system_name).replace(
            "{TARGET_SLICE}", target_slice
        )
        with open(spec_path, "w", encoding="utf-8") as f:
            f.write(spec_content)
    else:
        with open(spec_path, "w", encoding="utf-8") as f:
            f.write(f"# Especificação de Extração: {system_name}\n\nDocumente aqui as regras mapeadas.\n")

    print(f"✨ Área de quarentena criada com sucesso para: '{system_name}'")
    print(f"📁 Caminho da quarentena: {project_dir}")
    print(f"📄 Especificação gerada: {spec_path}")
    print("\n👉 Próximos passos:")
    print(f"   1. Copie o repositório/arquivos legados para: {source_dir}")
    print(f"   2. Preencha o documento de especificação em: {spec_path}")
    print(f"   3. Execute o scaffold da fatia: python tools/scripts/slice_scaffold.py --name {target_slice}")
    print(f"   4. Implemente as regras e audite com: python tools/scripts/reverse_engineering.py audit --slice {target_slice}")


def list_staging_workspaces() -> None:
    root_dir = get_root_dir()
    staging_dir = root_dir / "staging"

    if not staging_dir.exists():
        print("Nenhuma pasta de staging encontrada.")
        return

    print("=" * 60)
    print("SoftForge — Projetos em Quarentena para Engenharia Reversa")
    print("=" * 60)

    count = 0
    for item in staging_dir.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            count += 1
            has_spec = (item / "EXTRACTION_SPEC.md").exists()
            has_source = (item / "source").exists() and any((item / "source").iterdir())
            spec_badge = "[SPEC OK]" if has_spec else "[SEM SPEC]"
            source_badge = "[SOURCE CARREGADO]" if has_source else "[SOURCE VAZIO]"
            print(f"- {item.name:<25} {spec_badge:<12} {source_badge}")

    if count == 0:
        print("Nenhum projeto registrado no momento em staging/.")
    print("=" * 60)


def audit_slice_compliance(slice_name: str) -> bool:
    slice_name = slice_name.strip().lower()
    root_dir = get_root_dir()
    api_slice_dir = root_dir / "apps" / "api" / "src" / "slices" / slice_name
    web_feature_dir = root_dir / "apps" / "web" / "src" / "features" / slice_name

    print("=" * 60)
    print(f"SoftForge — Auditoria de Conformidade Arquitetural: '{slice_name}'")
    print("=" * 60)

    if not api_slice_dir.exists():
        print(f"[ERRO] A fatia de backend '{slice_name}' não existe em: {api_slice_dir}")
        return False

    errors: list[str] = []
    warnings: list[str] = []

    # 1. Checagem de arquivos estruturais obrigatórios no Backend
    required_files = [
        "__init__.py",
        "models.py",
        "schemas.py",
        "service.py",
        "router.py",
        f"tests/test_{slice_name}_slice.py",
    ]
    for rel_path in required_files:
        fpath = api_slice_dir / rel_path
        if not fpath.exists():
            errors.append(f"Arquivo obrigatório não encontrado no backend: {rel_path}")

    # 2. Análise de código em models.py (Base, workspace_id)
    models_file = api_slice_dir / "models.py"
    if models_file.exists():
        content = models_file.read_text(encoding="utf-8")
        if "from src.core.database import Base" not in content and "(Base)" not in content:
            errors.append("models.py não herda de 'src.core.database.Base'.")
        if "workspace_id" not in content:
            errors.append("models.py não possui campo 'workspace_id' para multi-tenancy.")

    # 3. Análise de imports proibidos no Backend
    for py_file in api_slice_dir.rglob("*.py"):
        try:
            content = py_file.read_text(encoding="utf-8")
            for prohibited in PROHIBITED_BACKEND_IMPORTS:
                if re.search(rf"\b(import|from)\s+{prohibited}\b", content):
                    errors.append(
                        f"Import proibido no backend ({prohibited}) detectado em: {py_file.name}"
                    )
        except Exception:
            pass

    # 4. Análise do Frontend (se houver implementação correspondente)
    if web_feature_dir.exists():
        print(f"[*] Verificando conformidade do frontend em: {web_feature_dir}")
        for ext in ["*.css", "*.scss", "*.less"]:
            for css_file in web_feature_dir.rglob(ext):
                warnings.append(
                    f"Folha de estilo legada encontrada em feature: {css_file.name}. Prefira classes Tailwind e componentes nativos."
                )

        for ts_file in web_feature_dir.rglob("*.tsx"):
            try:
                content = ts_file.read_text(encoding="utf-8")
                for prohibited in PROHIBITED_FRONTEND_IMPORTS:
                    if prohibited in content:
                        errors.append(
                            f"Dependência visual proibida ({prohibited}) encontrada em: {ts_file.name}. Use exclusivamente o design system SoftForge."
                        )
            except Exception:
                pass

    # Relatório Final
    if errors:
        print("\n❌ FALHAS DETECTADAS:")
        for err in errors:
            print(f"  - {err}")
    else:
        print("\n✅ ESTRUTURA E ISOLAMENTO 100% EM CONFORMIDADE COM O SOFTFORGE!")

    if warnings:
        print("\n⚠️ AVISOS DE ATENÇÃO:")
        for warn in warnings:
            print(f"  - {warn}")

    print("=" * 60)
    return len(errors) == 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SoftForge — Gerenciamento de Engenharia Reversa e Quarentena"
    )
    subparsers = parser.add_subparsers(dest="command", help="Comando a executar")

    # init
    init_parser = subparsers.add_parser(
        "init", help="Inicializa uma nova área de quarentena em staging/"
    )
    init_parser.add_argument(
        "--name", required=True, help="Nome do sistema externo a analisar (ex: crm-antigo)"
    )

    # list
    subparsers.add_parser("list", help="Lista todos os sistemas em quarentena em staging/")

    # audit
    audit_parser = subparsers.add_parser(
        "audit", help="Audita uma fatia vertical migrada contra regras e contaminação de código"
    )
    audit_parser.add_argument(
        "--slice", required=True, help="Nome da fatia a auditar (ex: projects, billing)"
    )

    args = parser.parse_args()

    if args.command == "init":
        init_staging_workspace(args.name)
    elif args.command == "list":
        list_staging_workspaces()
    elif args.command == "audit":
        success = audit_slice_compliance(args.slice)
        sys.exit(0 if success else 1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
