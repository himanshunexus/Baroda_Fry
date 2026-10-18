FROM node:22-bookworm-slim AS frontend-build
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt
COPY backend/ /app/backend/
COPY --from=frontend-build /build/frontend/dist/ /app/frontend/dist/
RUN SECRET_KEY=build-only-static-collection DEBUG=true LOCAL_MODE=true python /app/backend/manage.py collectstatic --noinput && \
    groupadd --system app && useradd --system --gid app --home-dir /app app && \
    chown -R app:app /app
USER app
WORKDIR /app/backend
CMD ["sh", "-c", "exec daphne -b 0.0.0.0 -p ${PORT:-8000} config.asgi:application"]
