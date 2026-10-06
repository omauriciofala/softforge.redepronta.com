"""SoftForge - Initializer of Universal AI Guidelines and Skills.

Equips any new project or workspace created with SoftForge with universal
AI agent guidelines (Karpathy-inspired principles), multi-vendor rules,
and discovery bridges for Antigravity, Claude Code, Cursor, Windsurf, Copilot, and Codex.
"""

import argparse
import os
import shutil
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def sync_ai_guidelines(target_dir: Path) -> None:
    source_root = Path(__file__).resolve().parent.parent.parent
    target_dir = target_dir.resolve()

    print(f"[*] Sincronizando diretrizes de IA do SoftForge em: {target_dir}")

    # Lista de arquivos e pastas para sincronizar
    items_to_sync = [
        (".agents/skills/karpathy-guidelines/SKILL.md", target_dir / ".agents" / "skills" / "karpathy-guidelines" / "SKILL.md"),
        (".agents/rules/karpathy-guidelines.md", target_dir / ".agents" / "rules" / "karpathy-guidelines.md"),
        (".agents/rules/versioning-policy.md", target_dir / ".agents" / "rules" / "versioning-policy.md"),
        (".ai/rules/karpathy-guidelines.md", target_dir / ".ai" / "rules" / "karpathy-guidelines.md"),
        (".ai/rules/versioning-policy.md", target_dir / ".ai" / "rules" / "versioning-policy.md"),
        (".ai/rules/documentation-first.md", target_dir / ".ai" / "rules" / "documentation-first.md"),
        (".ai/rules/openapi-contracts.md", target_dir / ".ai" / "rules" / "openapi-contracts.md"),
        (".ai/rules/vertical-slices.md", target_dir / ".ai" / "rules" / "vertical-slices.md"),
        ("AGENTS.md", target_dir / "AGENTS.md"),
        (".ai/AGENTS.md", target_dir / ".ai" / "AGENTS.md"),
        ("CLAUDE.md", target_dir / "CLAUDE.md"),
        (".github/copilot-instructions.md", target_dir / ".github" / "copilot-instructions.md"),
    ]

    copied_count = 0
    for src_rel, dest_path in items_to_sync:
        src_path = source_root / src_rel
        if src_path.exists():
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            if src_path.resolve() != dest_path.resolve():
                shutil.copy2(src_path, dest_path)
            copied_count += 1
            print(f"  [+] {dest_path.relative_to(target_dir)}")
        else:
            print(f"  [!] Origem não encontrada: {src_path}")

    print(f"\n[OK] {copied_count} recursos de IA configurados com sucesso em {target_dir}!")
    print("🤖 Assistentes suportados:")
    print("   - Google Antigravity (.agents/skills/karpathy-guidelines/SKILL.md)")
    print("   - Claude Code (CLAUDE.md)")
    print("   - Cursor & Windsurf (AGENTS.md & .ai/rules/)")
    print("   - GitHub Copilot (.github/copilot-instructions.md)")
    print("   - Universal Codex & LLMs (AGENTS.md)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Inicializa as diretrizes e skills de IA universais do SoftForge")
    parser.add_argument(
        "--target",
        type=str,
        default=".",
        help="Diretório de destino para instalar/atualizar as regras de IA (padrão: diretório atual)",
    )
    args = parser.parse_args()
    target_path = Path(args.target)
    sync_ai_guidelines(target_path)


if __name__ == "__main__":
    main()
