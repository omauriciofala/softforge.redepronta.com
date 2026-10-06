"""SoftForge - Unified Release Automation Script.

Enforces Semantic Versioning (SemVer) across the monorepo, validates all
guardrails via verify.py, updates version manifests (pyproject.toml, package.json),
generates/prepends changelog entries, and optionally creates Git tags.
"""

import argparse
from datetime import datetime, timezone
import json
import re
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def get_current_version(root_dir: Path) -> str:
    pyproject_path = root_dir / "apps" / "api" / "pyproject.toml"
    if pyproject_path.exists():
        content = pyproject_path.read_text(encoding="utf-8")
        match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
        if match:
            return match.group(1)

    pkg_path = root_dir / "apps" / "web" / "package.json"
    if pkg_path.exists():
        data = json.loads(pkg_path.read_text(encoding="utf-8"))
        if "version" in data:
            return data["version"]

    return "0.1.0"


def bump_version(current: str, bump_type: str) -> str:
    parts = current.split(".")
    if len(parts) != 3:
        raise ValueError(f"Versão inválida para SemVer: {current}")

    major, minor, patch = map(int, parts)
    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    elif bump_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError(f"Tipo de bump desconhecido: {bump_type}")


def update_file_version(file_path: Path, current_ver: str, new_ver: str, dry_run: bool = False) -> None:
    if not file_path.exists():
        return

    content = file_path.read_text(encoding="utf-8")
    if file_path.suffix == ".toml":
        updated = re.sub(
            r'^(version\s*=\s*)"' + re.escape(current_ver) + r'"',
            r'\1"' + new_ver + r'"',
            content,
            flags=re.MULTILINE,
        )
    elif file_path.suffix == ".json":
        data = json.loads(content)
        if "version" in data:
            data["version"] = new_ver
            updated = json.dumps(data, indent=2) + "\n"
        else:
            updated = content
    else:
        updated = content.replace(f'version = "{current_ver}"', f'version = "{new_ver}"')

    if not dry_run and updated != content:
        file_path.write_text(updated, encoding="utf-8")
    print(f"  [+] Atualizado {file_path.name}: {current_ver} -> {new_ver} {'(dry-run)' if dry_run else ''}")


def get_git_commits_since_last_tag() -> list[str]:
    try:
        # Pega a última tag se houver
        tag_proc = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True,
            text=True,
            check=False,
        )
        last_tag = tag_proc.stdout.strip()
        git_range = f"{last_tag}..HEAD" if last_tag else "HEAD"

        log_proc = subprocess.run(
            ["git", "log", git_range, "--oneline", "--no-merges"],
            capture_output=True,
            text=True,
            check=False,
            encoding="utf-8",
        )
        if log_proc.returncode == 0:
            lines = [l.strip() for l in log_proc.stdout.splitlines() if l.strip()]
            return lines
    except Exception:
        pass
    return []


def update_changelog(
    root_dir: Path,
    new_version: str,
    commits: list[str],
    custom_notes: str | None = None,
    dry_run: bool = False,
) -> None:
    changelog_path = root_dir / "CHANGELOG.md"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    features = []
    fixes = []
    others = []

    for commit in commits:
        parts = commit.split(" ", 1)
        desc = parts[1] if len(parts) > 1 else commit
        if desc.startswith("feat"):
            features.append(desc)
        elif desc.startswith("fix"):
            fixes.append(desc)
        else:
            others.append(desc)

    new_entry_lines = [
        f"## [v{new_version}] - {today}",
        "",
    ]

    if custom_notes:
        new_entry_lines.extend([custom_notes.strip(), ""])

    if features:
        new_entry_lines.append("### ✨ Novas Funcionalidades")
        for f in features:
            new_entry_lines.append(f"- {f}")
        new_entry_lines.append("")

    if fixes:
        new_entry_lines.append("### 🐛 Correções de Bugs")
        for f in fixes:
            new_entry_lines.append(f"- {f}")
        new_entry_lines.append("")

    if others and not features and not fixes and not custom_notes:
        new_entry_lines.append("### 🔨 Alterações Gerais")
        for o in others[:15]:
            new_entry_lines.append(f"- {o}")
        new_entry_lines.append("")

    new_entry = "\n".join(new_entry_lines).strip() + "\n\n"

    header = "# Changelog — SoftForge\n\nTodas as mudanças notáveis neste projeto são documentadas aqui seguindo o padrão [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/) e [Semantic Versioning](https://semver.org/lang/pt-BR/).\n\n---\n\n"

    if changelog_path.exists():
        existing = changelog_path.read_text(encoding="utf-8")
        if existing.startswith("# Changelog"):
            parts = existing.split("---\n\n", 1)
            if len(parts) > 1:
                final_content = header + new_entry + parts[1]
            else:
                final_content = header + new_entry + existing
        else:
            final_content = header + new_entry + existing
    else:
        final_content = header + new_entry

    if not dry_run:
        changelog_path.write_text(final_content, encoding="utf-8")
    print(f"  [+] CHANGELOG.md atualizado com a versão v{new_version} {'(dry-run)' if dry_run else ''}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Automação unificada de release e versionamento para o SoftForge")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--bump", choices=["major", "minor", "patch"], help="Tipo de incremento SemVer")
    group.add_argument("--version", help="Versão explícita (ex: 1.0.0)")

    parser.add_argument("--skip-verify", action="store_true", help="Ignora a execução prévia do pipeline verify.py")
    parser.add_argument("--dry-run", action="store_true", help="Simula o lançamento sem modificar arquivos ou Git")
    parser.add_argument("--tag", action="store_true", help="Cria a tag Git vX.Y.Z e comita automaticamente")
    parser.add_argument("-m", "--message", help="Mensagem ou descrição destacada da versão para o Changelog")

    args = parser.parse_args()

    root_dir = Path(__file__).resolve().parent.parent.parent
    current_ver = get_current_version(root_dir)

    if args.version:
        new_ver = args.version.lstrip("v")
    else:
        new_ver = bump_version(current_ver, args.bump)

    print("=" * 60)
    print(f"SoftForge — Lançamento de Release: v{current_ver} -> v{new_ver}")
    print("=" * 60)

    # 1. Execução de Guardrails
    if not args.skip_verify:
        print("\n[*] Executando guardrails do framework antes da release...")
        verify_script = root_dir / "tools" / "scripts" / "verify.py"
        py_exec = sys.executable
        res = subprocess.run([py_exec, str(verify_script)], check=False)
        if res.returncode != 0:
            print("\n[ERRO] O pipeline verify.py falhou! Corrija os problemas antes de lançar.")
            sys.exit(1)
        print("[OK] Guardrails aprovados com sucesso!")

    # 2. Atualização dos Manifestos de Versão
    print("\n[*] Sincronizando manifestos de versão:")
    update_file_version(root_dir / "apps" / "api" / "pyproject.toml", current_ver, new_ver, args.dry_run)
    update_file_version(root_dir / "apps" / "web" / "package.json", current_ver, new_ver, args.dry_run)

    docs_pkg = root_dir / "docs" / "package.json"
    if docs_pkg.exists():
        update_file_version(docs_pkg, current_ver, new_ver, args.dry_run)

    # 3. Atualização do CHANGELOG.md
    print("\n[*] Gerando notas de versão no CHANGELOG.md:")
    commits = get_git_commits_since_last_tag()
    update_changelog(root_dir, new_ver, commits, custom_notes=args.message, dry_run=args.dry_run)

    # 4. Git Commit & Tag
    if args.tag and not args.dry_run:
        print(f"\n[*] Criando commit e tag Git v{new_ver}:")
        subprocess.run(["git", "add", "."], cwd=root_dir, check=True)
        commit_msg = f"chore(release): release v{new_ver}"
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=root_dir, check=True)
        tag_msg = f"SoftForge v{new_ver}"
        if args.message:
            tag_msg += f" - {args.message}"
        subprocess.run(["git", "tag", "-a", f"v{new_ver}", "-m", tag_msg], cwd=root_dir, check=True)
        print(f"[OK] Tag v{new_ver} criada com sucesso!")
        print(f"👉 Para publicar no repositório remoto: git push origin main --tags")

    print("\n" + "=" * 60)
    print(f"✨ Release v{new_ver} processada com sucesso!")
    print("=" * 60)


if __name__ == "__main__":
    main()
