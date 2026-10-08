FROM node:24-alpine AS ui
WORKDIR /ui
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock
COPY backend/ backend/
COPY alembic.ini ./
COPY docker-entrypoint.sh ./
COPY --from=ui /ui/dist frontend/dist
RUN useradd --uid 10001 --create-home pack \
    && mkdir -p /app/.local/images \
    && chown -R pack:pack /app \
    && chmod +x /app/docker-entrypoint.sh
USER pack
EXPOSE 8000
ENTRYPOINT ["/app/docker-entrypoint.sh"]
