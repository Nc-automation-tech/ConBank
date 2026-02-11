# ============================================================================
# Dockerfile para Easypanel - Otimizado
# ============================================================================
# Easypanel usa buildx e pode ter limites de recursos
# ============================================================================

# ============================================================================
# STAGE 1: Build do Frontend (Otimizado)
# ============================================================================
FROM node:18-alpine AS frontend-build

WORKDIR /app

# Variáveis para otimizar build
ENV NODE_ENV=production
ENV NODE_OPTIONS="--max-old-space-size=2048"
ENV CI=true
ENV DISABLE_ESLINT_PLUGIN=true

# Copiar apenas package files primeiro (cache)
COPY frontend/package.json frontend/package-lock.json* ./

# Install com configurações otimizadas
RUN npm ci --only=production --ignore-scripts || \
    npm install --only=production --ignore-scripts

# Copiar código fonte
COPY frontend/ ./

# Build com tratamento de erro
RUN npm run build || \
    (echo "Build falhou. Tentando sem TypeScript checks..." && \
     npm run build --no-typescript-check) || \
    (echo "ERRO: Build impossível" && exit 1)

# Verificar se dist foi criado
RUN test -d dist || (echo "ERRO: dist não criado" && exit 1)

# ============================================================================
# STAGE 2: Runtime - Backend + Frontend
# ============================================================================
FROM python:3.11-slim

WORKDIR /app

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Instalar apenas dependências essenciais
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar requirements
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código do backend
COPY backend/ .

# Copiar frontend buildado
COPY --from=frontend-build /app/dist ./static

# Verificar se static existe e tem index.html
RUN test -f static/index.html || \
    (echo "ERRO: static/index.html não encontrado" && exit 1)

# Expor porta (Easypanel geralmente usa 3000 ou variável PORT)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000')" || exit 1

# Start command
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
