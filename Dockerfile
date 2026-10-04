FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN useradd --create-home --uid 10001 appuser
WORKDIR /app

COPY pyproject.toml constraints.txt README.md LICENSE ./
COPY src ./src
COPY app ./app
RUN python -m pip install --no-cache-dir -c constraints.txt . \
    && python -m pip check

USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"
STOPSIGNAL SIGTERM
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]
