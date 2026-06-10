FROM node:22-alpine AS frontend-build

WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY frontend/ ./
RUN npm run build
RUN test -f /frontend/dist/index.html
RUN test -d /frontend/dist/assets


FROM python:3.12-slim AS application

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FRONTEND_DIST_DIR=/app/backend/static
ENV REQUIRE_FRONTEND=true

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY --from=frontend-build /frontend/dist/ ./backend/static/
RUN test -f /app/backend/static/index.html
RUN test -d /app/backend/static/assets

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "3010", "--proxy-headers"]
