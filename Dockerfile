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
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR /app/backend

# Puerto interno real de la aplicacion. En Dokploy configure el dominio con
# "Container Port = 5173" o publique el puerto en Advanced -> Ports.
EXPOSE 5173

# Sin HEALTHCHECK a proposito: el servicio puede arrancar aunque MySQL no este
# disponible y un healthcheck fallido haria que Docker/Swarm lo reinicie en
# bucle. La comprobacion esta en /health (manual) y /health/db.

# El contenedor arranca solo: espera MySQL, crea la BD si falta, migra y sirve
# la web + API. No depende de scripts .bat ni de terminales.
ENTRYPOINT ["/entrypoint.sh"]
CMD []
