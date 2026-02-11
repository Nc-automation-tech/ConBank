# ============================================================================
# Dockerfile Único - Frontend + Backend (COM CORREÇÕES)
# ============================================================================

# ============================================================================
# STAGE 1: Build do Frontend (VERSÃO ROBUSTA)
# ============================================================================
FROM node:18-alpine AS frontend-build

WORKDIR /app

# Aumentar limite de memória do Node (comum em builds grandes)
ENV NODE_OPTIONS="--max-old-space-size=4096"

# Desabilitar telemetria
ENV NEXT_TELEMETRY_DISABLED=1
ENV CI=true

# Copiar package files
COPY frontend/package*.json ./

# Limpar cache do npm e instalar
RUN npm cache clean --force && \
    npm ci --legacy-peer-deps --no-audit --no-fund || \
    npm install --legacy-peer-deps --no-audit --no-fund

# Copiar TUDO do frontend (incluindo arquivos de config)
COPY frontend/ ./

# Verificar se arquivos importantes existem
RUN test -f vite.config.ts || test -f vite.config.js || echo "⚠️ vite.config não encontrado"
RUN test -f tsconfig.json || echo "⚠️ tsconfig.json não encontrado"
RUN test -f index.html || echo "⚠️ index.html não encontrado"

# Build com tratamento de erro
RUN set -e && \
    echo "🔨 Iniciando build..." && \
    npm run build 2>&1 | tee build.log && \
    echo "✅ Build concluído" || \
    (echo "❌ ERRO NO BUILD:" && cat build.log && exit 1)

# Verificar se dist foi criado
RUN if [ ! -d "dist" ]; then \
        echo "❌ ERRO: pasta dist não foi criada!"; \
        echo "Conteúdo atual:"; ls -la; \
        exit 1; \
    fi && \
    echo "✅ dist/ criado com sucesso" && \
    ls -la dist/

# ============================================================================
# STAGE 2: Backend Python + Frontend estático
# ============================================================================
FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema (se necessário)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY backend/requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar código do backend
COPY backend/ .

# Copiar frontend buildado
COPY --from=frontend-build /app/dist ./static

# Verificar se static tem conteúdo
RUN if [ ! -f "static/index.html" ]; then \
        echo "❌ ERRO: static/index.html não encontrado!"; \
        ls -la static/; \
        exit 1; \
    fi && \
    echo "✅ Frontend copiado com sucesso"

# Expor porta
EXPOSE 8000

# Health check (opcional)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000')" || exit 1

# Iniciar servidor
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
