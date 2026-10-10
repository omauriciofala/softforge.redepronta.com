"""Atalho conveniente para executar o CLI e Servidor MCP de DevTasks a partir da raiz."""

import os
from pathlib import Path
import subprocess
import sys

root_dir = Path(__file__).resolve().parent.parent.parent
api_dir = root_dir / "apps" / "api"
venv_py_win = api_dir / ".venv" / "Scripts" / "python.exe"
venv_py_nix = api_dir / ".venv" / "bin" / "python"

venv_py = venv_py_win if venv_py_win.exists() else (venv_py_nix if venv_py_nix.exists() else None)

if venv_py and Path(sys.executable).resolve() != venv_py.resolve():
    env = os.environ.copy()
    res = subprocess.run([str(venv_py), __file__] + sys.argv[1:], env=env)
    sys.exit(res.returncode)

if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

from src.slices.dev_tasks.cli import main

if __name__ == "__main__":
    main()
