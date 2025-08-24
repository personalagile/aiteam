FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml README.md /app/
RUN pip install -U pip && pip install -e ".[dev,agents]" && pip install daphne>=4.0

COPY . /app

EXPOSE 8000
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "aiteam.asgi:application"]
