# ---- Etapa 1: compilar la web (Vue + Vite) ----
FROM node:20-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---- Etapa 2: servidor unico (web compilada + API) ----
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_PORT=5173

WORKDIR /app

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ ./backend/
COPY --from=frontend /app/frontend/dist ./frontend/dist

WORKDIR /app/backend

EXPOSE 5173

# Sin scripts de inicio/apagado: el contenedor arranca el servicio y se reinicia solo.
CMD ["sh", "-c", "python -m alembic upgrade head || true; exec python -m uvicorn app.main:app --host 0.0.0.0 --port ${APP_PORT:-5173}"]
