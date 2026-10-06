import os
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def run_step(name: str, cmd: list[str], cwd: Path | None = None) -> bool:
    print(f"\n[*] [{name}] Executando: {' '.join(cmd)}")
    try:
        # No Windows, comandos como 'npm' são scripts .cmd
        exec_cmd = list(cmd)
        if sys.platform == "win32" and exec_cmd[0] in ("npm", "npx", "pnpm"):
            exec_cmd[0] = f"{exec_cmd[0]}.cmd"

        res = subprocess.run(
            exec_cmd,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            check=False,
            encoding="utf-8",
            errors="replace",
        )
        if res.returncode == 0:
            print(f"[OK] [{name}] Sucesso!")
            if res.stdout.strip():
                print(res.stdout.strip())
            return True
        else:
            print(f"[FAIL] [{name}] Falhou com código {res.returncode}:")
            if res.stdout:
                print(res.stdout)
            if res.stderr:
                print(res.stderr)
            return False
    except Exception as e:
        print(f"[FAIL] [{name}] Erro ao disparar processo: {e}")
        return False


def main() -> None:
    root_dir = Path(__file__).resolve().parent.parent.parent
    api_dir = root_dir / "apps" / "api"
    web_dir = root_dir / "apps" / "web"

    # Seleciona o executável Python do ambiente virtual se existir
    venv_py_win = api_dir / ".venv" / "Scripts" / "python.exe"
    venv_py_nix = api_dir / ".venv" / "bin" / "python"
    if venv_py_win.exists():
        py_exec = str(venv_py_win)
    elif venv_py_nix.exists():
        py_exec = str(venv_py_nix)
    else:
        py_exec = sys.executable

    print("=" * 60)
    print("SoftForge - Pipeline Unificado de Guardrails para IA")
    print("=" * 60)

    success = True

    # 1. Exportação e Validação Estática do OpenAPI 3.1
    export_script = root_dir / "tools" / "scripts" / "export_openapi.py"
    if not run_step("OpenAPI Spec Export", [py_exec, str(export_script)]):
        success = False

    # 2. Testes de Integração do Backend (Pytest com SQLite in-memory)
    if not run_step("Backend Integration Tests", [py_exec, "-m", "pytest", "-v"], cwd=api_dir):
        success = False

    # 3. Linter e Verificação de Código com Ruff
    if not run_step("Backend Linter (Ruff)", [py_exec, "-m", "ruff", "check", "src"], cwd=api_dir):
        success = False

    # 4. Validação do Frontend (se dependências estiverem instaladas completamente)
    if (web_dir / "node_modules" / ".bin").exists():
        if not run_step("Frontend Typecheck", ["npm", "run", "typecheck"], cwd=web_dir):
            success = False

    print("\n" + "=" * 60)
    if success:
        print("[SUCESSO] TODOS OS GUARDRAILS FORAM ATENDIDOS COM SUCESSO!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("[ALERTA] Foram detectadas falhas nas verificações de qualidade.")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
