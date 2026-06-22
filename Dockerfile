# Image de l'application Gefradis (version B, composable) pour Cloud Run.
# Base Python + Playwright/Chromium installé avec ses dépendances système.
FROM python:3.12-slim

WORKDIR /app

# Dépendances Python, puis Chromium + ses libs système (rendu des bannières).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && playwright install --with-deps chromium

# Le code de l'application B (le reste du dépôt n'est pas nécessaire).
COPY composable/ ./composable/

# Cloud Run fournit le port via la variable PORT ; on écoute sur toutes les interfaces.
ENV HOST=0.0.0.0 \
    PYTHONUNBUFFERED=1
EXPOSE 8001

WORKDIR /app/composable
CMD ["python", "backend/api.py"]
