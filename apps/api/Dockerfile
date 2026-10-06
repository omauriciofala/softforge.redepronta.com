FROM python:3.12-slim

# Evita criação de arquivos .pyc e bufferiza stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Instala dependências de compilação essenciais e utilitários
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Instala uv para resolução ultrarrápida de pacotes
RUN pip install --no-cache-dir uv

# Copia arquivos de definição do projeto
COPY pyproject.toml ./

# Instala dependências via uv
RUN uv pip install --system -e ".[dev]"

# Copia o código da aplicação
COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
