import json
import os
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Garante que o diretório apps/api esteja no PYTHONPATH
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
api_dir = project_root / "apps" / "api"
sys.path.insert(0, str(api_dir))

# Evita tentar conectar a bancos reais durante a extração a frio do schema
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from src.main import app  # noqa: E402


def export_openapi() -> None:
    """Extrai estaticamente a especificação OpenAPI 3.1 da aplicação FastAPI."""
    schema = app.openapi()
    output_path = api_dir / "openapi.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)

    print(f"✅ Especificação OpenAPI 3.1 exportada com sucesso em: {output_path}")


if __name__ == "__main__":
    export_openapi()
