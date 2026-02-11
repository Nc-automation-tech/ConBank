# ============================================================================
# Dockerfile Multi-Stage - Frontend + Backend Integrado
# ============================================================================
# Stage 1: Build do Frontend
# Stage 2: Backend + Frontend estático
# ============================================================================

# ============================================================================
# STAGE 1: Build do Frontend React/Vite
# ============================================================================
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend

# Copiar package files
COPY frontend/package*.json ./

# Instalar dependências
RUN npm ci --only=production

# Copiar código fonte
COPY frontend/ ./

# Build do frontend (gera pasta /frontend/dist)
RUN npm run build

# ============================================================================
# STAGE 2: Backend Python + Frontend Estático
# ============================================================================
FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements do backend
COPY backend/requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código do backend
COPY backend/ .

# Copiar frontend buildado do stage anterior
COPY --from=frontend-builder /frontend/dist ./static

# Expor porta
EXPOSE 8000

# Variáveis de ambiente (podem ser sobrescritas no docker-compose)
ENV DATABASE_URL=postgresql://postgres:b2ad156f04d4203f02f3@n8n_postgres:5432/ConBank
ENV PYTHONUNBUFFERED=1

# Comando para iniciar o servidor
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]